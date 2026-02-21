# Transcription summarization Lambda — see transcription-demo/lambda-src for source of truth.
# This copy is used by CDK deployment; keep in sync or symlink.

import json
import os
from pathlib import Path

import boto3
from jinja2 import Template

BEDROCK_REGION = os.environ.get("BEDROCK_REGION", "us-east-1")
s3_client = boto3.client("s3")
bedrock_runtime = boto3.client("bedrock-runtime", BEDROCK_REGION)


def lambda_handler(event, context):
    bucket = event["Records"][0]["s3"]["bucket"]["name"]
    key = event["Records"][0]["s3"]["object"]["key"]

    if "-transcript.json" not in key:
        print("This demo only works with *-transcript.json.")
        return

    try:
        response = s3_client.get_object(Bucket=bucket, Key=key)
        file_content = response["Body"].read().decode("utf-8")
        transcript = extract_transcript_from_textract(file_content)

        print(f"Successfully read file {key} from bucket {bucket}.")
        summary = bedrock_summarisation(transcript)

        s3_client.put_object(
            Bucket=bucket,
            Key="results.txt",
            Body=summary,
            ContentType="text/plain",
        )
    except Exception as e:
        print(f"Error occurred: {e}")
        return {"statusCode": 500, "body": json.dumps(f"Error occurred: {e}")}

    return {
        "statusCode": 200,
        "body": json.dumps(f"Successfully summarized {key} from bucket {bucket}. Summary: {summary}"),
    }


def extract_transcript_from_textract(file_content):
    transcript_json = json.loads(file_content)
    output_text = ""
    current_speaker = None
    items = transcript_json["results"]["items"]

    for item in items:
        speaker_label = item.get("speaker_label")
        content = item["alternatives"][0]["content"]
        if speaker_label is not None and speaker_label != current_speaker:
            current_speaker = speaker_label
            output_text += f"\n{current_speaker}: "
        if item.get("type") == "punctuation":
            output_text = output_text.rstrip()
        output_text += f"{content} "

    return output_text


def bedrock_summarisation(transcript):
    template_path = Path(__file__).resolve().parent / "prompt_template.txt"
    template_string = template_path.read_text()
    data = {
        "transcript": transcript,
        "topics": ["charges", "location", "availability"],
    }
    prompt = Template(template_string).render(data)
    print(prompt)

    response = bedrock_runtime.converse(
        modelId="amazon.nova-lite-v1:0",
        messages=[{"role": "user", "content": [{"text": prompt}]}],
        inferenceConfig={"maxTokens": 2048, "temperature": 0, "topP": 0.9},
    )
    return response["output"]["message"]["content"][0]["text"]
