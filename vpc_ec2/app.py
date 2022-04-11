#!/usr/bin/env python3
import os

import aws_cdk as cdk

from majdvpc_cdk.majdvpc_cdk_stack import MajdvpcCdkStack


app = cdk.App()
MajdvpcCdkStack(app, "majdvpc-cdk", env=cdk.Environment(
    account="415102591172",
#   region="us-west-2")
    region="us-east-1")
    )

app.synth()
