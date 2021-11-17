from aws_cdk import (
    aws_ec2 as ec2,
    core
)


class VpcStack(core.NestedStack):
    def __init__(self, scope: core.Construct, id: str, params,
                 **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        self.vpc = ec2.Vpc(
            self,
            "Wordpress-VPC",
            nat_gateways=params.vpc.get("nats_number", 1),
            max_azs=params.vpc.az_number,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    cidr_mask=24,
                    name='Wordpress-VPC-Public-Subnet',
                    subnet_type=ec2.SubnetType.PUBLIC,
                ),
                ec2.SubnetConfiguration(
                    cidr_mask=28,
                    name='Wordpress-VPC-Private-Subnet',
                    subnet_type=ec2.SubnetType.ISOLATED,
                ),
                ec2.SubnetConfiguration(
                    cidr_mask=24,
                    name='Wordpress-VPC-Natted-Subnet',
                    subnet_type=ec2.SubnetType.PRIVATE,
                )
            ]
        )
