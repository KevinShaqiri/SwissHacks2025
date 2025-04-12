from dotenv import load_dotenv
import os
from openai import OpenAI
import json

# Load env variables
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def compare_docx_txt(docx_json: dict, text_content: str) -> bool:
    system_prompt = """
You are a consistency checker. The user provides:

A structured JSON object that was parsed from a .docx form. It contains factual fields like name, gender, job history, income, wealth origin, etc.

A .txt file with 5 narrative sections: Summary Note, Family Background, Occupation History, Wealth Summary, and Client Summary.

Your task is to check whether the logic in each section of the .txt is consistent with the facts in the JSON. You do not need to match every sentence word-for-word. Instead, verify:

Does the .txt describe information that logically aligns with what’s in the JSON?

Does the .txt contradict or go against any factual field in the JSON?

Consider a section inconsistent if:

It describes facts (e.g. employment history, income source, family status) that directly contradict what's in the JSON

It makes assumptions or statements that are clearly not supported by the JSON data

If all 5 sections are logically consistent, return "True".

If any one section is logically inconsistent, return "False".

Only return "True" or "False". Do not explain.
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

    with open("./data/profile_docx.json", "r", encoding="utf-8") as f:
        docx_json = json.load(f)

    result = compare_docx_txt(docx_json, txt)
    print("Consistent:", result)
