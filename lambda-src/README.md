# Lambda source (for fixing Bedrock model)

This folder contains a copy of **LambdaFunctionSummarize** with the Bedrock model ID updated from the deprecated `amazon.titan-text-express-v1` to **`amazon.titan-text-premier-v1:0`** (Titan Text Premier) so `results.txt` is written again. If Premier is not available in your account, change the `modelId` in `lambda_function.py` to **`amazon.titan-text-lite-v1`** (Titan Text Lite).

## Deploy

```bash
cd transcription-demo/lambda-src
zip -r ../deploy.zip lambda_function.py prompt_template.txt
cd ..
aws lambda update-function-code \
  --function-name LambdaFunctionSummarize \
  --zip-file fileb://deploy.zip \
  --profile administrator
```

Then re-run the transcript demo; `results.txt` in S3 should update.
