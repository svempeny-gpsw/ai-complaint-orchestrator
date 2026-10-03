import boto3

session = boto3.Session(
    profile_name="complaint-demo",
    region_name="us-east-1",
)

bedrock = session.client("bedrock-runtime")

response = bedrock.converse(
    modelId="us.anthropic.claude-sonnet-4-6",
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "text": (
                        "A customer says: "
                        "'I cancelled last week but you charged me again today.' "
                        "Classify this complaint in one short sentence."
                    )
                }
            ],
        }
    ],
    inferenceConfig={
        "maxTokens": 100,
        "temperature": 0,
    },
)

print(response["output"]["message"]["content"][0]["text"])