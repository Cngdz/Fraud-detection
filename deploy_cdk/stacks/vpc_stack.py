# Tên file: stacks/vpc_stack.py

from aws_cdk import (
    Stack,
    aws_ec2 as ec2,  # Dịch vụ VPC, Subnet, Security Group
)
from constructs import Construct

class VpcStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # === 1. TẠO VPC ===
        
        self.vpc = ec2.Vpc(
            self, "fraud-vpc",
            cidr="10.0.0.0/16",
            max_azs=2,  
            nat_gateways=0, 
            enable_dns_hostnames=True,
            enable_dns_support=True,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="private-subnet-2a",
                    subnet_type=ec2.SubnetType.PRIVATE_ISOLATED,
                    cidr_mask=24
                ),
                ec2.SubnetConfiguration(
                    name="private-subnet-2b",
                    subnet_type=ec2.SubnetType.PRIVATE_ISOLATED,
                    cidr_mask=24
                ),
                ec2.SubnetConfiguration(
                    name="public-subnet-2a",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=24
                ),
                ec2.SubnetConfiguration(
                    name="public-subnet-2b",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=24
                )
            ]
        )

        
        # === 2. TẠO SECURITY GROUP ===
        # SG cho Lambda
        self.sg_lambda = ec2.SecurityGroup(
            self, "lambda-sg",
            vpc=self.vpc,
            security_group_name="lambda-sg",
            description="Allow Lambda outbound all traffic",
            allow_all_outbound=True
        )

        # SG cho ElastiCache
        self.sg_redis = ec2.SecurityGroup(
            self, "redis-sg",
            vpc=self.vpc,
            security_group_name="redis-sg",
            description="Allow Redis inbound from Lambda only",
            allow_all_outbound=True
        )
        # Chỉ cho phép Lambda kết nối Redis qua cổng 6379
        self.sg_redis.add_ingress_rule(
            peer=self.sg_lambda,
            connection=ec2.Port.tcp(6379),
            description="Allow Redis access from Lambda"
        )

        # SG cho Interface Endpoints
        self.sg_endpoints = ec2.SecurityGroup(
            self, "endpoints-sg",
            vpc=self.vpc,
            security_group_name="endpoints-sg",
            description="Allow HTTPS access to VPC Endpoints",
            allow_all_outbound=True
        )
        self.sg_endpoints.add_ingress_rule(
            ec2.Peer.any_ipv4(),
            ec2.Port.tcp(80),
            "Allow HTTP inbound"
        )
        self.sg_endpoints.add_ingress_rule(
            ec2.Peer.any_ipv4(),
            ec2.Port.tcp(443),
            "Allow HTTPS inbound"
        )

        # SG cho Bastion host / endpoint
        self.sg_bastion = ec2.SecurityGroup(
            self, "bastion-sg",
            vpc=self.vpc,
            security_group_name="bastion-sg",
            description="Allow SSH and TCP:5000 inbound from anywhere",
            allow_all_outbound=True
        )
        self.sg_bastion.add_ingress_rule(
            ec2.Peer.any_ipv4(),
            ec2.Port.tcp(22),
            "Allow SSH inbound"
        )
        self.sg_bastion.add_ingress_rule(
            ec2.Peer.any_ipv4(),
            ec2.Port.tcp(5000),
            "Allow TCP 5000 inbound"
        )

        # 🧩 3. VPC ENDPOINTS ---------------------------------

        # Gateway Endpoint cho S3, dynamodb
        self.s3_endpoint = self.vpc.add_gateway_endpoint(
            "vpce-s3",
            service=ec2.GatewayVpcEndpointAwsService.S3,
            subnets=[ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_ISOLATED)]
        )
        self.dynamodb_endpoint = self.vpc.add_gateway_endpoint(
            "vpce-dynamodb",
            service=ec2.GatewayVpcEndpointAwsService.DYNAMODB,
            subnets=[ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_ISOLATED)]
        )

        # Interface Endpoints (paid)
        self.kinesis_endpoint = ec2.InterfaceVpcEndpoint(
            self, "vpce-kinesis",
            vpc=self.vpc,
            service=ec2.InterfaceVpcEndpointAwsService.KINESIS_STREAMS,
            private_dns_enabled=True,
            subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_ISOLATED),
            security_groups=[self.sg_endpoints]
        )

        self.sagemaker_endpoint = ec2.InterfaceVpcEndpoint(
            self, "vpce-sagemaker",
            vpc=self.vpc,
            service=ec2.InterfaceVpcEndpointAwsService.SAGEMAKER_RUNTIME,
            private_dns_enabled=True,
            subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_ISOLATED),
            security_groups=[self.sg_endpoints]
        )

        self.lambda_endpoint = ec2.InterfaceVpcEndpoint(
            self, "vpce-lambda",
            vpc=self.vpc,
            service=ec2.InterfaceVpcEndpointAwsService.LAMBDA_,
            private_dns_enabled=True,
            subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_ISOLATED),
            security_groups=[self.sg_endpoints]
        )

        self.sns_endpoint = ec2.InterfaceVpcEndpoint(
            self, "vpce-sns",
            vpc=self.vpc,
            service=ec2.InterfaceVpcEndpointAwsService.SNS,
            private_dns_enabled=True,
            subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_ISOLATED),
            security_groups=[self.sg_endpoints]
        )