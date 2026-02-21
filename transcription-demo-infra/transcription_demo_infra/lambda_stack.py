"""Lambda stack: S3 bucket, summarization function, and S3 trigger. Deploy this for code or trigger changes."""
from pathlib import Path

from aws_cdk import CfnOutput, Duration, RemovalPolicy, Stack, Token
from aws_cdk import aws_iam as iam
from aws_cdk import aws_lambda as _lambda
from aws_cdk import aws_s3 as s3
from aws_cdk import aws_s3_notifications as s3n
from constructs import Construct

from .infra_stack import InfraStack


class LambdaStack(Stack):
    """Bucket, Lambda function (Nova summarization), and S3 event. Depends only on InfraStack for IAM role."""

    def __init__(self, scope: Construct, construct_id: str, infra: InfraStack, instance: str = "default", **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        self.instance = instance

        # Bucket lives here so S3 event notification does not create Infra -> Lambda dependency
        bucket_name = self.node.try_get_context("bucket_name")
        if not bucket_name:
            account = self.node.try_get_context("account") or self.account
            if account and not Token.is_unresolved(account):
                bucket_name = f"transcription-demo-{instance}-{account}".lower()
            else:
                bucket_name = None
        self.bucket = s3.Bucket(
            self,
            "TranscriptBucket",
            bucket_name=bucket_name,
            removal_policy=RemovalPolicy.RETAIN,
            auto_delete_objects=False,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            encryption=s3.BucketEncryption.S3_MANAGED,
        )
        # Bucket policy in this stack (not role policy in Infra) so Infra never references this bucket
        self.bucket.add_to_resource_policy(
            iam.PolicyStatement(
                principals=[infra.lambda_role],
                actions=["s3:GetObject*", "s3:PutObject*", "s3:DeleteObject*", "s3:GetBucket*", "s3:List*"],
                resources=[self.bucket.bucket_arn, self.bucket.arn_for_objects("*")],
            )
        )

        repo_root = Path(__file__).resolve().parent.parent
        bundle_dir = repo_root / ".lambda_bundle"
        if not (bundle_dir / "lambda_function.py").exists():
            raise FileNotFoundError("Lambda bundle not found. Run: scripts/bundle_lambda.sh")
        code_path = str(bundle_dir)

        self.fn = _lambda.Function(
            self,
            "Summarize",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="lambda_function.lambda_handler",
            code=_lambda.Code.from_asset(code_path),
            role=infra.lambda_role,
            timeout=Duration.seconds(120),
            memory_size=128,
            environment={"BEDROCK_REGION": self.region},
        )

        self.bucket.add_event_notification(
            s3.EventType.OBJECT_CREATED,
            s3n.LambdaDestination(self.fn),
            s3.NotificationKeyFilter(suffix=".json"),
        )

        CfnOutput(
            self,
            "BucketName",
            value=self.bucket.bucket_name,
            description="S3 bucket for transcripts and results",
            export_name=f"TranscriptionDemo-BucketName-{instance}" if instance != "default" else None,
        )
