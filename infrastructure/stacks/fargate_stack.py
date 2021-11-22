import os
from aws_cdk import (
    aws_elasticloadbalancingv2 as elbv2,
    aws_ec2 as ec2,
    aws_ecr_assets as ecr_assets,
    aws_ecs as ecs,
    aws_efs as efs,
    aws_iam as iam,
    aws_s3 as s3,
    core,
)

from infrastructure.stacks.database_stack import DatabaseStack
from infrastructure.stacks.vpc_stack import VpcStack


class FargateStack(core.NestedStack):

    def __init__(self, scope: core.Construct, id: str, params, vpc_stack: VpcStack, database_stack: DatabaseStack,
                 **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        ecs_efs = efs.FileSystem(
            self, "Wordpress-EFS-FS",
            vpc=vpc_stack.vpc,
            performance_mode=efs.PerformanceMode.GENERAL_PURPOSE,
            throughput_mode=efs.ThroughputMode.BURSTING,
        )

        wordpress_volume = ecs.Volume(
            name="Wordpress-EFS-Volume",
            efs_volume_configuration=ecs.EfsVolumeConfiguration(
                file_system_id=ecs_efs.file_system_id
            )
        )

        self.ecs_wordpress_task = ecs.FargateTaskDefinition(self, "Wordpress-ECS-Task", volumes=[wordpress_volume],
                                                            cpu=params.fargate.cpu,
                                                            memory_limit_mib=params.fargate.memory_limit)

        ecs_cluster = ecs.Cluster(
            self, 'Wordpress-ECS-Cluster',
            vpc=vpc_stack.vpc,
            enable_fargate_capacity_providers=True
        )

        ecs_service = ecs.FargateService(
            self, "Wordpress-ECS-Service",
            task_definition=self.ecs_wordpress_task,
            platform_version=ecs.FargatePlatformVersion.VERSION1_4,
            cluster=ecs_cluster,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE),
        )

        media_bucket = s3.Bucket(
            self, 'Wordpress-S3-Bucket',
            versioned=False,
            bucket_name='cc.wp-media.bucket',
            encryption=s3.BucketEncryption.S3_MANAGED,
            removal_policy=core.RemovalPolicy.RETAIN if params.name == "prod" else core.RemovalPolicy.DESTROY
        )

        ecs_wordpress_logging = ecs.AwsLogDriver(
            stream_prefix="ccwp-"
        )

        docker_image = ecr_assets.DockerImageAsset(
            self, "Wordpress-ECR-Image",
            directory=f"{os.path.dirname(__file__)}/../../images/wordpress",
            file="Dockerfile",
            repository_name=params.fargate.container_image_name
        )

        ecs_wordpress_container = self.ecs_wordpress_task.add_container(
            "Wordpress-ECS-Task",
            environment={
                'PRIMARY_DB_URI': f"{database_stack.db_record.domain_name}:{database_stack.database.cluster_endpoint.port}",
                'SECONDARY_DB_URI': f"{database_stack.db_replica_record.domain_name}:{database_stack.database.cluster_endpoint.port}" if params.aurora.get(
                    "has_replica", None) else "",
                'MEDIA_S3_BUCKET': media_bucket.bucket_name,
                'WORDPRESS_TABLE_PREFIX': 'wp_',
                'WORDPRESS_DB_HOST': database_stack.db_record.domain_name
            },
            secrets={
                'WORDPRESS_DB_USER':
                    ecs.Secret.from_secrets_manager(database_stack.database.secret, field="username"),
                'WORDPRESS_DB_PASSWORD':
                    ecs.Secret.from_secrets_manager(database_stack.database.secret, field="password"),
                'WORDPRESS_DB_NAME':
                    ecs.Secret.from_secrets_manager(database_stack.database.secret, field="dbname"),
            },
            image=ecs.ContainerImage.from_docker_image_asset(docker_image),
            logging=ecs_wordpress_logging
        )

        ecs_wordpress_container.add_port_mappings(
            ecs.PortMapping(container_port=80)
        )

        media_bucket.grant_read_write(self.ecs_wordpress_task.task_role)
        media_bucket.grant_delete(self.ecs_wordpress_task.task_role)

        ecs_wordpress_volume_mount_point = ecs.MountPoint(
            read_only=False,
            container_path="/var/www/html",
            source_volume=wordpress_volume.name
        )

        ecs_wordpress_container.add_mount_points(ecs_wordpress_volume_mount_point)

        ecs_service.connections.allow_from(
            other=database_stack.database,
            port_range=database_stack.database.connections.default_port
        )
        ecs_efs.connections.allow_default_port_from(ecs_service)

        scaling = ecs_service.auto_scale_task_count(
            min_capacity=params.fargate.min_capacity,
            max_capacity=params.fargate.max_capacity
        )
        scaling.scale_on_cpu_utilization(
            "Wordpress-ECS-Task",
            target_utilization_percent=75,
            scale_in_cooldown=core.Duration.seconds(30),
            scale_out_cooldown=core.Duration.seconds(30),
        )

        if params.fargate.get("spots", {}).get("enabled", False):
            fargate_ecs_service = ecs_service.node.try_find_child("Service")
            fargate_ecs_service.launch_type = None
            fargate_ecs_service.capacity_provider_strategy = [
                {
                    "capacityProvider": "FARGATE_SPOT",
                    "weight": params.fargate.spots.spot_weight,
                },
                {
                    "capacityProvider": "FARGATE",
                    "weight": params.fargate.spots.normal_weight,
                    "base": 1
                },
            ]

        app_load_balancer = elbv2.ApplicationLoadBalancer(
            self, "Wordpress-ALB",
            vpc=vpc_stack.vpc,
            internet_facing=True,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC),
        )

        ecs_service.connections.allow_from(
            other=app_load_balancer,
            port_range=ec2.Port.tcp(80)
        )

        http_listener = app_load_balancer.add_listener(
            "Wordpress-ALB-HTTP-Listener",
            port=80,
        )

        http_listener.add_targets(
            "Wordpress-ALB-Target",
            protocol=elbv2.ApplicationProtocol.HTTP,
            targets=[ecs_service],
            health_check=elbv2.HealthCheck(healthy_http_codes="200,301,302")
        )

        self.ecs_wordpress_task.task_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "secretsmanager:GetResourcePolicy",
                    "secretsmanager:GetSecretValue",
                    "secretsmanager:DescribeSecret",
                    "secretsmanager:ListSecretVersionIds"
                ],
                resources=[
                    database_stack.database.secret.secret_arn
                ],
                effect=iam.Effect.ALLOW
            )
        )

        self.ecs_wordpress_task.task_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "ecs:StartTelemetrySession"
                ],
                resources=[
                    "*"
                ],
                effect=iam.Effect.ALLOW
            )
        )

        self.ecs_wordpress_task.task_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "s3:ListBucket"
                ],
                resources=[
                    media_bucket.bucket_arn
                ],
                effect=iam.Effect.ALLOW
            )
        )

        self.ecs_wordpress_task.task_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "s3:*Object"
                ],
                resources=[
                    f"{media_bucket.bucket_arn}/*"
                ],
                effect=iam.Effect.ALLOW
            )
        )

        database_stack.database.secret.grant_read(self.ecs_wordpress_task.task_role)
        database_stack.database.connections.allow_from(ecs_cluster,
                                                       ec2.Port(from_port=database_stack.database.cluster_endpoint.port,
                                                                to_port=database_stack.database.cluster_endpoint.port,
                                                                protocol=ec2.Protocol(ec2.Protocol.TCP),
                                                                string_representation="fromECSCluster"))
        core.CfnOutput(
            self,
            'wp_alb_endpoint',
            value=app_load_balancer.load_balancer_dns_name,
            description="The application load balancer url"
        )
