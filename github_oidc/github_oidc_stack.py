
import yaml

from aws_cdk import (
    Stack,
    Duration,
    CfnOutput,
    aws_iam as iam,
)
from constructs import Construct

GITHUB_THUMBPRINT = "6938fd4d98bab03faadb97b34396831e3780aea1"
OIDC_CONFIG_PATH = "./AccessConfigOIDC.yaml"
MAX_SESSION_DURATION_HOURS = 1 # Must be between 1 and 12
GITHUB_ACTIONS_ROLE_NAME = "github_actions_role"

class GithubOidcStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        ### GitHub OIDC Provider
        # https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_iam.OpenIdConnectProvider.html
        github_provider = iam.OpenIdConnectProvider(self, "GitHubOIDC",
            ## This URL is one per ACCOUNT, hence why OIDC is it's own repo:
            url="https://token.actions.githubusercontent.com",
            client_ids=["sts.amazonaws.com"],
            ## Thumbprint from the GitHub runner cert:
            # https://github.blog/changelog/2022-01-13-github-actions-update-on-oidc-based-deployments-to-aws/
            thumbprints=[GITHUB_THUMBPRINT],
        )

        ### The Role for the Actions Runner to Assume
        # https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_iam.Role.html
        github_actions_role = iam.Role(
            self,
            "GitHubActionsRole",
            # This stack can only be deployed one per account anyways,
            # so just make the role easy to use with actions:
            role_name=GITHUB_ACTIONS_ROLE_NAME,
            max_session_duration=Duration.hours(MAX_SESSION_DURATION_HOURS),
            # https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_iam.FederatedPrincipal.html
            assumed_by=iam.FederatedPrincipal(
                federated=github_provider.open_id_connect_provider_arn,
                assume_role_action="sts:AssumeRoleWithWebIdentity",
                conditions={
                    "ForAnyValue:StringLike": {
                        # Controls who can be a subscriber (sub) to the role:
                        "token.actions.githubusercontent.com:sub": self._load_whitelist_config(OIDC_CONFIG_PATH),
                    },
                    "StringEquals": {
                        "token.actions.githubusercontent.com:aud": "sts.amazonaws.com",
                    },
                },
            ),
        )

        ### Permissions for the Actions Runner
        ## Just use the provided cdk v2 roles, as they are already set up for this:
        # Use the CDK Deployment roles:
        # Bootstrap info: https://docs.aws.amazon.com/cdk/latest/guide/bootstrapping.html
        # Guide on this:  https://medium.com/@mylesloffler/using-github-actions-to-deploy-a-cdk-application-f28b7f792f12
        # Another Guide:  https://stackoverflow.com/a/61102280/11650472
        # docs on object: https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_iam.PolicyStatement.html
        assume_cdk_roles_policy = iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=["sts:AssumeRole"],
            resources=[f"arn:aws:iam::{self.account}:role/cdk-*"],
            conditions={
                "StringEquals": {
                    "aws:ResourceTag/aws-cdk:bootstrap-role": [
                        # https://docs.aws.amazon.com/cdk/v2/guide/bootstrapping-env.html#bootstrapping-env-roles
                        "file-publishing",
                        "lookup",
                        "deploy",
                    ],
                },
            },
        )
        ### Attach the policy to the role:
        # https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_iam.Role.html#addwbrtowbrpolicystatement
        github_actions_role.add_to_policy(assume_cdk_roles_policy)

        ### OUTPUTS:
        # https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.CfnOutput.html
        CfnOutput(
            self,
            "GithubActionsRoleName",
            value=github_actions_role.role_name,
            description="The role name for GH Actions to assume",
        )


    def _load_whitelist_config(self, path: str) -> list:
        with open(path, mode="r", encoding="utf-8") as yaml_file:
            whitelist_info = yaml.safe_load(yaml_file)

        whitelisted_repos = []
        ## Loop through the config file, and snag all the repos that can use OIDC:
        # (See the config itself for info structure, and on adding more)
        # TLDR: {OrgName: {RepoName: [Branches]}}
        for org_name, repo_info in whitelist_info.items():
            for repo_name, branches_list in repo_info.items():
                for branch in branches_list:
                    # If I need to expand this one day, there's more than just `:ref:` to use.
                    # There's also at least`:pull_request:` and `:Environment:`. Merging on ONLY
                    # push makes sure only reviewed code runs on my account though.
                    whitelisted_repos.append(f"repo:{org_name}/{repo_name}:ref:{branch}")
        return whitelisted_repos
