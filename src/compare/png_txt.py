from dotenv import load_dotenv
import os
from openai import OpenAI
import json
from datetime import datetime

# Load env variables
load_dotenv()
client = OpenAI(api_key=os.getenv("SWISSHACKS_API"))

def compare_passport_description(docx_json: dict, text_content: str) -> bool:
    system_prompt = f"""
You are a highly skilled consistency checker focused on semantic data analysis. Today is: {datetime.today()}.
The API will provide you with two JSON objects. Please note:
- The JSON objects may vary in length and structure and may not share identical keys.
- Keys representing similar information might have different names (e.g., "surname" vs. "lastName", "DOB" vs. "dateOfBirth").
- Some fields may include Unicode escape sequences (e.g., "\u2019", "\u00e9") instead of properly parsed special characters. Prior to comparison, normalize these values to their standard representations.
- Your task is to:
  1. Parse and normalize each JSON object (including converting any Unicode codes to their corresponding characters).
  2. Identify keys that are semantically equivalent, even if named differently.
  3. Compare the values of these semantically matched keys.
  4. Determine if the overall factual data between the two JSON objects is consistent.

Rules:
- If all matching fields are consistent or logically aligned, consider the JSONs consistent.
- If any direct factual contradiction is detected, consider them inconsistent.
- Your final output must be exactly one of the following (without any explanations):
    - "True" if the data is consistent.
    - "False" if any inconsistency is found.

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
        ]
    )

    content = response.choices[0].message.content.strip()
    
    if content.lower() == "true":
        return True
    elif content.lower() == "false":
        return False
    else:
        raise ValueError(f"Unexpected answer from OpenAI: {content}")

if __name__ == "__main__":
    with open("./data/description.txt", "r", encoding="utf-8") as f:
        txt = f.read()

    with open("./data/passport_png.json", "r", encoding="utf-8") as f:
        png_json = json.load(f)

    result = compare_passport_description(png_json, txt)
    print("Answer:", result)
