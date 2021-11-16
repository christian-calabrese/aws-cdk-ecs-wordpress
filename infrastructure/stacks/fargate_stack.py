import os
from aws_cdk import (
    aws_elasticloadbalancingv2 as elbv2,
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_efs as efs,
    aws_ecr_assets as ecr_assets,
    aws_s3 as s3,
    core,
)


class FargateStack(core.NestedStack):

    def __init__(self, scope: core.Construct, id: str, params, vpc_stack: core.Stack, database_stack: core.Stack,
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

        ecs_wordpress_task = ecs.FargateTaskDefinition(self, "Wordpress-ECS-Task", volumes=[wordpress_volume])

        ecs_cluster = ecs.Cluster(
            self, 'Wordpress-ECS-Cluster',
            vpc=vpc_stack.vpc
        )

        ecs_service = ecs.FargateService(
            self, "Wordpress-ECS-Service",
            task_definition=ecs_wordpress_task,
            platform_version=ecs.FargatePlatformVersion.VERSION1_4,
            cluster=ecs_cluster,
        )

        wordpress_image = ecr_assets.DockerImageAsset(
            self, "Wordpress-ECR-Image",
            directory=f"{os.path.dirname(__file__)}/../../images/wordpress",
            file="Dockerfile",
        )

        media_bucket = s3.Bucket(
            self, 'Wordpress-S3-Bucket',
            versioned=False,
            bucket_name='flowing.wp-media.bucket',
            encryption=s3.BucketEncryption.S3_MANAGED,
            removal_policy=core.RemovalPolicy.RETAIN
        )

        ecs_wordpress_container = ecs_wordpress_task.add_container(
            "Wordpress-ECS-Task",
            environment={
                'PRIMARY_DB_URI': database_stack.database.cluster_endpoint.hostname,
                'SECONDARY_DB_URI': database_stack.replica_database.cluster_endpoint.hostname if params.aurora.get(
                    "has_replica", None) else "",
                'MEDIA_S3_BUCKET': media_bucket.bucket_name,
                'WORDPRESS_TABLE_PREFIX': 'wp_'
            },
            secrets={
                'DB_USER':
                    ecs.Secret.from_secrets_manager(database_stack.database.secret, field="database_username"),
                'DB_PWD':
                    ecs.Secret.from_secrets_manager(database_stack.database.secret, field="database_password"),
                'DB_NAME':
                    ecs.Secret.from_secrets_manager(database_stack.database.secret, field="database_name"),
            },
            image=ecs.ContainerImage.from_docker_image_asset(wordpress_image)
        )

        ecs_wordpress_container.add_port_mappings(
            ecs.PortMapping(container_port=80)
        )

        media_bucket.grant_read_write(ecs_wordpress_task.task_role)
        media_bucket.grant_delete(ecs_wordpress_task.task_role)

        ecs_wordpress_volume_mount_point = ecs.MountPoint(
            read_only=True,
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
            min_capacity=2,
            max_capacity=10
        )
        scaling.scale_on_cpu_utilization(
            "Wordpress-ECS-Task",
            target_utilization_percent=75,
            scale_in_cooldown=core.Duration.seconds(120),
            scale_out_cooldown=core.Duration.seconds(30),
        )

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