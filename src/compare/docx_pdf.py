import json
import os
from dotenv import load_dotenv
from openai import OpenAI
from datetime import datetime
import re
# Load environment variables
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def compare_profile_account(profile_docx: dict, account_opening_pdf: dict) -> bool:

    """
    Compare factual details between two structured JSON objects.
    The function instructs a consistency checker via OpenAI to compare the two JSONs.
    
    Args:
        json1 (dict): The first JSON object containing structured factual data.
        json2 (dict): The second JSON object containing structured factual data.
    
    Returns:
        bool: True if all corresponding factual fields align, False if any inconsistency is found.
        
    Raises:
        ValueError: If the response from OpenAI is not exactly "True" or "False".
    """
    system_prompt = f"""
You are a highly skilled consistency checker focused on semantic data analysis. Today is: {datetime.today()}.
The API will provide you with two JSON objects. Please note:
- The JSON objects may vary in length and structure and may not share identical keys.
- Keys representing similar information might have different names (e.g., "surname" vs. "lastName", "DOB" vs. "dateOfBirth").
- Some fields may include Unicode escape sequences (e.g., "\u2019", "\u00e9") instead of properly parsed special characters. Prior to comparison, normalize these values to their standard representations
- Your task is to:
  1. Parse and normalize each JSON object (including converting any Unicode codes to their corresponding characters).
  2. Identify keys that are semantically equivalent, even if named differently.
  3. Compare the values of these semantically matched keys.
  4. Determine if the overall factual data between the two JSON objects is consistent.

Rules:
- If all matching fields are consistent or logically aligned, consider the JSONs consistent.
- If any direct factual contradiction is detected, consider them inconsistent.
- Reason about why you made such decision, clearly outlying whether there is a contradiction or not.
- Your final output (response content) must be EXACTLY one of the following:
    - "True" if the data is consistent.
    - "False" if any inconsistency is found.

"""

    user_message = f"""Here are the two JSON objects:
First JSON:
{json.dumps(profile_docx, indent=2)}

Second JSON:
{json.dumps(account_opening_pdf, indent=2)}
"""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt.strip()},
            {"role": "user", "content": user_message.strip()}
        ], temperature=0.5
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
        else:
            return False

if __name__ == "__main__":
    # Example usage: Adjust the file names and paths to match your environment.
    with open("./data/profile_docx.json", "r", encoding="utf-8") as f:
        profile_docx = json.load(f)

    with open("./data/account_opening_pdf.json", "r", encoding="utf-8") as f:
        account_opening_pdf = json.load(f)

    result = compare_profile_account(profile_docx, account_opening_pdf)
    print("Consistent:", result)
