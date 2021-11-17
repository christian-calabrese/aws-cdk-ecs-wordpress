from aws_cdk import (
    aws_ec2 as ec2,
    core
)


class VpcStack(core.NestedStack):
    def __init__(self, scope: core.Construct, id: str, params,
                 **kwargs) -> None:
        super().__init__(scope, id, **kwargs)
        self.nats_number = params.vpc.get("nats_number", 1)

        self.subnets_configuration = [
            ec2.SubnetConfiguration(
                cidr_mask=24,
                name='Wordpress-VPC-Public-Subnet',
                subnet_type=ec2.SubnetType.PUBLIC,
            ),
            ec2.SubnetConfiguration(
                cidr_mask=24,
                name='Wordpress-VPC-Private-Subnet',
                subnet_type=ec2.SubnetType.ISOLATED,
            )
        ]

        if self.nats_number > 0:
            self.subnets_configuration.append(
                ec2.SubnetConfiguration(
                    cidr_mask=24,
                    name='Wordpress-VPC-Natted-Subnet',
                    subnet_type=ec2.SubnetType.PRIVATE,
                ))

        self.vpc = ec2.Vpc(
            self,
            "Wordpress-VPC",
            nat_gateways=self.nats_number,
            max_azs=params.vpc.az_number,
            subnet_configuration=self.subnets_configuration,
            enable_dns_support=True,
            enable_dns_hostnames=True
        )
