from aws_cdk import (
    Stack,
    aws_kinesis as kinesis,
    aws_dynamodb as dynamodb,
    aws_sns as sns,
    aws_sns_subscriptions as subscriptions,
    aws_sagemaker as sagemaker,
    aws_lambda as _lambda,
    aws_ec2 as ec2,
    aws_iam as iam,
)
from constructs import Construct
import aws_cdk as cdk

class FraudDetectionStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, vpc, sg_lambda, **kwargs):
        super().__init__(scope, construct_id, **kwargs)

        # ======================
        # 1. TẠO KINESIS DATA STREAM
        # ======================
        stream = kinesis.Stream(
            self,
            "TransactionsStream",
            stream_name="transactions-stream",
            shard_count=1,  # 1 shard cho demo
        )

        # ======================
        # 2. TẠO DYNAMODB TABLE
        # ======================
        table = dynamodb.Table(
            self,
            "FraudResultsTable",
            table_name="fraud-results",
            partition_key=dynamodb.Attribute(
                name="transactionId",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,  # Pay per request
            removal_policy=cdk.RemovalPolicy.DESTROY  # Xóa khi stack bị xóa (chỉ cho môi trường dev)
        )

        # ======================
        # 3. TẠO SNS TOPIC VÀ SUBSCRIPTIONS
        # ======================
        topic = sns.Topic(
            self,
            "FraudAlertTopic",
            topic_name="fraud-alert",
            display_name="Fraud Detection Alert Topic"
        )

        # Email Subscription
        topic.add_subscription(
            subscriptions.EmailSubscription("hd.vucuong@gmail.com")  # type: ignore
        )

        # SMS Subscription (tạm comment nếu chưa cần)
        # topic.add_subscription(
        #     subscriptions.SmsSubscription("+84123456789")  # type: ignore
        # )

        # ======================
        # 4. TẠO SAGEMAKER NOTEBOOK INSTANCE
        # ======================
        notebook_role = iam.Role.from_role_name(
            self,
            "SageMakerRole",
            role_name="role-sagemaker-fraud"
        )

        notebook = sagemaker.CfnNotebookInstance(
            self,
            "FraudDetectionNotebook",
            notebook_instance_name="fraud-detection-endpoint-1",
            instance_type="ml.t3.medium",  # Instance type phù hợp cho demo
            role_arn=notebook_role.role_arn,
            # Gắn vào private subnet đầu tiên của VPC
            subnet_id=vpc.select_subnets(
                subnet_type=ec2.SubnetType.PRIVATE_ISOLATED
            ).subnets[0].subnet_id,
            security_group_ids=[sg_lambda.security_group_id],
            volume_size_in_gb=5  # Kích thước volume
        )

        # ======================
        # 5. TẠO LAMBDA FRAUD SCORING
        # ======================
        lambda_role = iam.Role.from_role_name(
            self,
            "LambdaRoleProcessing",
            role_name="role-lambda-processing"
        )

        lambda_fraud_scoring = _lambda.Function(
            self,
            "LambdaFraudScoring",
            function_name="Lambda_FraudScoring",
            runtime=_lambda.Runtime.PYTHON_3_13,
            handler="lambda_function.lambda_handler",
            code=_lambda.Code.from_asset("../src/lambda_fraud_scoring"),
            role=lambda_role,
            vpc=vpc,
            security_groups=[sg_lambda],
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_ISOLATED
            ),
            timeout=cdk.Duration.seconds(30),
            memory_size=128,
            environment={
                "STREAM_NAME": stream.stream_name,
                "DYNAMODB_TABLE": table.table_name,
                "SNS_TOPIC_ARN": topic.topic_arn,
                "SAGEMAKER_ENDPOINT": "fraud-detection-endpoint-1",
                "ALERT_LAMBDA_NAME": "Lambda_Alert",
                "REGION": self.region
            }
        )

        # Cấp quyền cho Lambda Fraud Scoring
        stream.grant_read(lambda_fraud_scoring)
        table.grant_read_write_data(lambda_fraud_scoring)
        topic.grant_publish(lambda_fraud_scoring)

        # ======================
        # 6. TẠO LAMBDA ALERT
        # ======================
        lambda_alert = _lambda.Function(
            self,
            "LambdaAlert",
            function_name="Lambda_Alert",
            runtime=_lambda.Runtime.PYTHON_3_13,
            handler="lambda_function.lambda_handler",
            code=_lambda.Code.from_asset("../src/lambda_alert"),
            role=lambda_role,
            vpc=vpc,
            security_groups=[sg_lambda],
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_ISOLATED
            ),
            timeout=cdk.Duration.seconds(30),
            memory_size=128,
            environment={
                "SNS_TOPIC_ARN": topic.topic_arn,
                "DYNAMODB_TABLE": table.table_name,
                "REGION": self.region
            }
        )

        # Cấp quyền cho Lambda Alert
        topic.grant_publish(lambda_alert)
        table.grant_read_data(lambda_alert)

        # ======================
        # OUTPUTS
        # ======================
        cdk.CfnOutput(self, "KinesisStreamName", value=stream.stream_name)
        cdk.CfnOutput(self, "DynamoDBTableName", value=table.table_name)
        cdk.CfnOutput(self, "SNSTopicArn", value=topic.topic_arn)
        cdk.CfnOutput(self, "NotebookInstanceName", value=notebook.notebook_instance_name)  # type: ignore
        cdk.CfnOutput(self, "FraudScoringLambda", value=lambda_fraud_scoring.function_name)
        cdk.CfnOutput(self, "AlertLambda", value=lambda_alert.function_name)