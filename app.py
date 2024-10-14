#!/usr/bin/env python3
import os

import aws_cdk as cdk

from github_oidc.github_oidc_stack import GithubOidcStack

# https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.App.html
app = cdk.App()


GithubOidcStack(
    app,
    "GithubOidcStack",
    env=cdk.Environment(
        account=os.getenv('CDK_DEFAULT_ACCOUNT'),
        region=os.getenv('CDK_DEFAULT_REGION'),
    ),
)

app.synth()
