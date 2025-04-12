from dotenv import load_dotenv
import os
from openai import OpenAI
import json
from datetime import datetime
import re

# Load env variables
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def compare_profile_description(docx_json: dict, text_content: str) -> bool:
    system_prompt = f"""
You are a highly skilled consistency checker specializing in matching structured factual data. Today is: {datetime.today()}.
The API will provide you with two items:
1. A structured JSON object (extracted from an official form) containing factual fields such as name, gender, employment details, income, wealth origin, etc.
2. A plain text document with five narrative sections in the following order:
   - Summary Note
   - Family Background
   - Occupation History
   - Wealth Summary
   - Client Summary

Additional Consideration:
- Some fields in the JSON may include Unicode escape sequences (e.g., "\u2019", "\u00e9") instead of the expected special characters. Normalize these escape sequences to their standard character representations before performing any comparisons.

Your task is to:
  1. Parse and normalize the JSON object to ensure any Unicode codes are converted to the correct characters.
  2. Extract and analyze factual details from the JSON.
  3. Read through the text document, recognizing and extracting the factual statements within each of its five sections.
  4. Compare the facts in the JSON with the corresponding details in the text, ensuring there are no contradictions.
  5. Understand that while the text may include extra narrative details, only factual discrepancies count as inconsistencies.

Rules:
- If every factual field in the JSON aligns with the narrative and no contradictions are found, output "True".
- If any part of the text contradicts a field in the JSON, output "False".
- Reason about why you made such decision, clearly outlying whether there is a contradiction or not. 
- Your final output (content) must be EXACTLY one of the following:
    - "True" if the data is consistent.
    - "False" if any inconsistency is found. Give explanaitions why

"""

    user_message = f"""Here is the text file content:
{text_content}

And here is the parsed JSON:
{json.dumps(docx_json, indent=2)}
"""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt.strip()},
            {"role": "user", "content": user_message.strip()}
        ], temperature=0
    )

    content = response.choices[0].message.content.strip()
    
    if content.lower() == "true":
        return True
    elif content.lower() == "false":
        return False
    else:
        decision = re.sub(r'[^A-Za-z]', '', content.split()[-1])
        if decision == "True":
            return True
        elif decision == "False":
            return False 
        else:
            raise ValueError(f"Unexpected output: {content}") 

if __name__ == "__main__":
    with open("./data/description.txt", "r", encoding="utf-8") as f:
        txt = f.read()

    with open("./data/profile_docx.json", "r", encoding="utf-8") as f:
        docx_json = json.load(f)

    result = compare_profile_description(docx_json, txt)
    print("Consistent:", result)
