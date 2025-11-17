from aws_cdk import (
    Stack,
    aws_ec2 as ec2,
    aws_lambda as _lambda,
    aws_apigateway as apigateway,
    aws_elasticache as elasticache,
    aws_iam as iam,
    aws_s3 as s3,
)
from constructs import Construct


class HotStack(Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        vpc,
        sg_lambda,
        sg_bastion,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # ===============================
        # 1️⃣  TẠO ELASTICACHE SERVERLESS
        # ===============================

        # Gắn role hệ thống bắt buộc cho ElastiCache
        elasticache_role = iam.CfnServiceLinkedRole(
            self,
            "ElastiCacheServiceLinkedRole",
            aws_service_name="elasticache.amazonaws.com",
        )

        # ElastiCache Redis Serverless hiện CDK chưa hỗ trợ chính thức,
        # nên dùng CfnServerlessCache.
        redis_serverless = elasticache.CfnServerlessCache(
            self,
            "FraudRedis",
            engine="redis",
            serverless_cache_name="fraud-redis",
            description="Serverless Redis for Fraud System",
            major_engine_version="7",  # Redis version 7.x
            security_group_ids=[sg_lambda.security_group_id],
            subnet_ids=[
                subnet.subnet_id
                for subnet in vpc.select_subnets(
                    subnet_type=ec2.SubnetType.PRIVATE_ISOLATED
                ).subnets
            ],
        )
        redis_serverless.node.add_dependency(elasticache_role)

        # ===============================
        # 2️⃣  TẠO LAMBDA FUNCTION
        # ===============================

        lambda_fn = _lambda.Function(
            self,
            "LambdaProcessTransaction",
            function_name="Lambda_ProcessTransaction",
            runtime=_lambda.Runtime.PYTHON_3_13,
            handler="lambda_handler.main",  # file lambda_handler.py, function main()
            code=_lambda.Code.from_asset("../src/lambda_process_transaction"),  # thư mục chứa code lambda
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_ISOLATED
            ),
            security_groups=[sg_lambda],
            environment={
                "REDIS_ENDPOINT": redis_serverless.attr_endpoint_address,
                "REDIS_PORT": redis_serverless.attr_endpoint_port,
                "APP_ENV": "prod",
            },
            role=iam.Role.from_role_arn(
                self,
                "LambdaRole",
                "arn:aws:iam::365187552932:role/role-lambda-processing",
            ),
        )

        # ===============================
        # 3️⃣  TẠO API GATEWAY
        # ===============================

        # Gắn Service Role cho API Gateway
        api_role = iam.CfnServiceLinkedRole(
            self,
            "ApiGatewayServiceLinkedRole",
            aws_service_name="apigateway.amazonaws.com",
        )

        fraud_api = apigateway.RestApi(
            self,
            "FraudApi",
            rest_api_name="fraud-api",
            description="Fraud detection API Gateway",
            endpoint_types=[apigateway.EndpointType.REGIONAL],
            deploy_options=apigateway.StageOptions(stage_name="prod"),
        )
        fraud_api.node.add_dependency(api_role)

        # Tạo resource /transaction + method POST
        transaction_resource = fraud_api.root.add_resource("transaction")
        transaction_resource.add_method(
            "POST", apigateway.LambdaIntegration(lambda_fn)  # type: ignore
        )

        # ===============================
        # 4️⃣  TẠO S3 BUCKET (DATALAKE)
        # ===============================

        fraud_raw_logs = s3.Bucket(
            self,
            "FraudRawLogs",
            bucket_name="fraud-raw-logs",
            versioned=True,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=None,  # không tự xóa
            enforce_ssl=True,
        )

        # ===============================
        # 5️⃣  TẠO BASTION HOST
        # ===============================

        # public subnet phải có trong VPCStack
        public_subnets = vpc.select_subnets(
            subnet_group_name="public-subnet-2a"
        ).subnets

        bastion_host = ec2.Instance(
            self,
            "BastionHost",
            instance_type=ec2.InstanceType("t2.micro"),
            machine_image=ec2.MachineImage.latest_amazon_linux(),
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(subnets=public_subnets),
            security_group=sg_bastion,
            key_name="edit-redis",  # keypair có sẵn
        )
