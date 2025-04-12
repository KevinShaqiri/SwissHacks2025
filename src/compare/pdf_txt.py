from dotenv import load_dotenv
import os
from openai import OpenAI
import json
from datetime import datetime

# Load env variables
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def compare_account_description(docx_json: dict, text_content: str) -> bool:
    system_prompt = f"""
You are a consistency checker. Today is: {datetime.today()}.

The user provides:

1. A structured JSON object containing verified factual data (e.g. passport data etc.).
2. A text document (.txt) that contains narrative or descriptive content which may reference this data.

Your task is to say whether the data in the files are consistent among one other. 
If yes, return True, if no return False. Don't explain.

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

    with open("./data/account_opening_pdf.json", "r", encoding="utf-8") as f:
        png_json = json.load(f)

    result = compare_account_description(png_json, txt)
    print("Answer:", result)
