"""Infrastructure stack: IAM role for the summarization Lambda. No bucket (bucket lives in Lambda stack to avoid cyclic dependency)."""
from aws_cdk import CfnOutput, Stack
from aws_cdk import aws_iam as iam
from constructs import Construct


class InfraStack(Stack):
    """IAM role for the Lambda. Deploy this when Lambda permissions change. Bucket is in LambdaStack."""

    def __init__(self, scope: Construct, construct_id: str, instance: str = "default", **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        self.instance = instance

        self.lambda_role = iam.Role(
            self,
            "SummarizeLambdaRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole"),
            ],
        )
        self.lambda_role.add_to_principal_policy(
            iam.PolicyStatement(
                actions=["bedrock:InvokeModel", "bedrock:InvokeModelWithResponseStream"],
                resources=["*"],
            )
        )

        CfnOutput(
            self,
            "Instance",
            value=instance,
            description="Instance name (use with scripts --bucket or -c instance)",
        )
