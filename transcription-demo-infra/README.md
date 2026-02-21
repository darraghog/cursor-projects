# Transcription Demo – DevOps / IaC

Manages the **full DevOps lifecycle** for the [transcription-demo](../transcription-demo) app: S3 bucket, Lambda (Nova summarization), IAM, and S3→Lambda trigger. **Infrastructure** and **Lambda code** can be deployed **independently**.

> **Note:** CDK deployment is not fully working and requires further testing (e.g. bootstrap with AdministratorAccess, credential/profile handling, cleanup of failed CDKToolkit stacks). Use the instructions below as a starting point and validate in your environment.

## Multiple instances (same region)

You can deploy several independent instances in one region (e.g. `dev`, `prod`, `customer-a`) by passing an **instance** name. Each instance gets its own stack pair and S3 bucket.

```bash
# Deploy instance "dev" (bucket name will be transcription-demo-dev-ACCOUNT_ID)
cdk deploy --all -c instance=dev --require-approval never

# Deploy instance "prod" with an explicit bucket name
cdk deploy --all -c instance=prod -c bucket_name=my-transcription-prod --require-approval never
```

Stack names become `TranscriptionDemoInfra-dev`, `TranscriptionDemoLambda-dev`, etc. The **BucketName** output is on the Lambda stack; use it with the demo scripts: `--bucket <value>`.

## What’s in this repo

| Stack | Contents | Deploy when |
|-------|----------|-------------|
| **TranscriptionDemoInfra** | IAM role (S3 + Bedrock); no dependency on Lambda stack | Permissions change |
| **TranscriptionDemoLambda** | S3 bucket, Lambda function (code + deps), S3 event notification | Bucket, Lambda code, or trigger change |

## Prerequisites

- **Python 3.9+** and **uv** (or pip)
- **AWS CDK CLI** (e.g. `npm install -g aws-cdk` or use `npx aws-cdk`)
- **AWS CLI** configured (e.g. `aws sso login --profile PowerUser`)
- **Enable** Amazon Nova (e.g. `amazon.nova-lite-v1:0`) in Bedrock → Model access in your account/region

## One-time setup

**CDK bootstrap** (once per account/region): run before the first deploy so CDK can stage assets (e.g. Lambda code). **Requires IAM permissions** (create/delete roles); the PowerUser permission set does *not* allow this—use a profile with AdministratorAccess (e.g. `administrator`) for bootstrap:

```bash
aws sso login --profile administrator
cdk bootstrap aws://YOUR_ACCOUNT_ID/us-east-1 --profile administrator
```
After bootstrap, you can deploy app stacks with PowerUser if your stacks don't need to create IAM roles; otherwise use the same admin profile for deploy.

Then install deps and bundle the Lambda:

```bash
cd transcription-demo-infra
uv sync
# Bundle Lambda (code + jinja2) for CDK asset
chmod +x scripts/bundle_lambda.sh && ./scripts/bundle_lambda.sh
```

## Deploy infrastructure only (IAM role)

Use when you change **IAM permissions** only. The bucket lives in the Lambda stack. For a non-default instance, add `-c instance=NAME`:

```bash
cdk deploy TranscriptionDemoInfra --require-approval never
# Or for instance "dev":
cdk deploy TranscriptionDemoInfra-dev --require-approval never
```

Optional: use an explicit bucket name when deploying the Lambda stack (e.g. to match transcription-demo scripts):

```bash
cdk deploy TranscriptionDemoLambda -c bucket_name=genai-training-bucket --require-approval never
```

## Deploy Lambda only (bucket, code, trigger)

Use when you change **bucket**, **Lambda code**, or **S3 trigger**:

```bash
./scripts/bundle_lambda.sh   # required after any lambda/ or lambda/requirements.txt change
cdk deploy TranscriptionDemoLambda --require-approval never
```

CDK will only update the Lambda asset and related resources; the infra stack is unchanged.

## Deploy everything

First time or after changing both infra and Lambda:

```bash
./scripts/bundle_lambda.sh
cdk deploy --all --require-approval never
```

**If CDK reports "Unable to resolve AWS account" or "no credentials have been configured":** Use the deploy wrapper so only your profile is used (it unsets credential env vars and sets `AWS_PROFILE`):

```bash
# Deploy with administrator profile (no account/region needed if profile works)
AWS_PROFILE=administrator ./scripts/cdk-deploy.sh --all --require-approval never

# If that still fails, pass account so CDK doesn't need to resolve it
CDK_ACCOUNT=YOUR_ACCOUNT_ID AWS_PROFILE=administrator ./scripts/cdk-deploy.sh --all --require-approval never
```
Replace `YOUR_ACCOUNT_ID` with your 12-digit account ID (e.g. from `aws sts get-caller-identity --profile administrator --query Account --output text`).

## Syncing with the transcription-demo app

After deploy, **TranscriptionDemoLambda** outputs **BucketName**. Use it when running the [transcription-demo](../transcription-demo) scripts:

```bash
# Option 1: pass bucket explicitly
uv run python scripts/run_transcript_only.py --bucket <BucketName>

# Option 2: set default via env (e.g. for one instance)
export TRANSCRIPTION_DEMO_BUCKET=<BucketName>
uv run python scripts/run_transcript_only.py
```

For multiple instances, pass `--bucket` per run or set `TRANSCRIPTION_DEMO_BUCKET` to the instance’s bucket.

## Verify deployment

1. **Unit tests** (no AWS, from `transcription-demo`):
   ```bash
   cd ../transcription-demo && uv run pytest tests/ -v
   ```

2. **Live verification** (after deploy; uses stack output and runs transcript-only demo):
   ```bash
   chmod +x scripts/verify_deployment.sh
   AWS_PROFILE=administrator ./scripts/verify_deployment.sh
   ```
   For a non-default instance: `INSTANCE=dev AWS_PROFILE=administrator ./scripts/verify_deployment.sh`

## Project layout

```
transcription-demo-infra/
├── app.py                          # CDK app entry
├── cdk.json
├── pyproject.toml / requirements.txt
├── lambda/                         # Lambda source (keep in sync with transcription-demo/lambda-src if desired)
│   ├── lambda_function.py
│   ├── prompt_template.txt
│   └── requirements.txt
├── scripts/
│   └── bundle_lambda.sh            # Builds .lambda_bundle for CDK asset
├── transcription_demo_infra/
│   ├── infra_stack.py              # S3 + IAM
│   └── lambda_stack.py             # Lambda + S3 trigger
└── README.md
```

## Summary

- **Infra changes** → `cdk deploy TranscriptionDemoInfra`
- **Lambda/code changes** → `./scripts/bundle_lambda.sh` then `cdk deploy TranscriptionDemoLambda`
- **Both** → `./scripts/bundle_lambda.sh` then `cdk deploy --all`
