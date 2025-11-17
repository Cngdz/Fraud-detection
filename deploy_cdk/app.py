#!/usr/bin/env python3
import aws_cdk as cdk
from stacks.vpc_stack import VpcStack
from stacks.hot_path_stack import HotStack
from stacks.cold_path_stack import FraudDetectionStack

app = cdk.App()

# 1️⃣ Deploy VPC trước
vpc_stack = VpcStack(app, "FraudVpcStack")

# 2️⃣ Deploy Hot Path (phụ thuộc vào VPC)
hot_path = HotStack(
    app,
    "FraudHotPathStack",
    vpc=vpc_stack.vpc,
    sg_lambda=vpc_stack.sg_lambda,
    sg_bastion=vpc_stack.sg_bastion
)

# 3️⃣ Deploy Cold Path (phụ thuộc vào VPC)
cold_path = FraudDetectionStack(
    app,
    "FraudColdPathStack",
    vpc=vpc_stack.vpc,
    sg_lambda=vpc_stack.sg_lambda  # ✅ Thêm sg_lambda parameter
)

app.synth()
