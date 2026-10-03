from app.services.bedrock_service import classify_complaint


complaint = """
I cancelled my subscription last week but you've taken money
from my account again today. I want the charge reversed and
I don't want to be billed again.
"""


result = classify_complaint(complaint)

print(result)
print()
print(result.model_dump_json(indent=2))