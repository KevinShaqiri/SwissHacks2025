import os
import base64
from openai import OpenAI
import json
from pathlib import Path

def encode_image(image_path):
    """Encode image to base64 string"""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def extract_passport_data(image_path):
    """Extract key-value pairs from passport image using OpenAI's vision model"""
    # Check if image exists
    if not Path(image_path).exists():
        raise FileNotFoundError(f"Image file not found: {image_path}")
    
    # Encode image to base64
    base64_image = encode_image(image_path)
    
    # Initialize OpenAI client (requires API key in environment variable OPENAI_API_KEY)
    client = OpenAI(api_key=os.getenv("SWISSHACKS_API"))
    
    # Create the prompt for analyzing passport data
    prompt = """
    Analyze this passport image in detail. Extract all visible data fields and their values.
    Return ONLY a JSON object with the following structure:
    {
        "Republic_english": "value",
        "Republic_native": "value",
        "Passport_english": "value",
        "Passport_native": "value",
        "Code":"value",
        "Passport_number":"value",
        "Surname":"value",
        "First_name":"value",
        "Birth_date":"value",
        "Citizenship_english":"value",
        "Citizenship_native":"value",
        "Sex":"value",,
        "Issue_date":"value",
        "Expiry_date":"value",
        "Machine_readable_zone":"value"
    }
    
    If a field is not visible or cannot be determined, use null as the value.
    In the fields where we have both english and native, return both values EXACTLY as they are in the image.
    EXTREMELY EXTREMELY IMPORTANT: Even if you think there is a typo:return the values EXACTLY as they are in the image.
    """
    
    # Call the OpenAI API with the vision model
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        max_tokens=2000
    )
    
    # Extract and parse the response text to JSON
    try:
        result_text = response.choices[0].message.content
        # Find JSON content (in case there's extra text)
        json_start = result_text.find('{')
        json_end = result_text.rfind('}') + 1
        if json_start >= 0 and json_end > json_start:
            json_str = result_text[json_start:json_end]
            parsed_data = json.loads(json_str)
            return parsed_data
        else:
            return {"error": "Failed to extract JSON from response", "raw_response": result_text}
    except Exception as e:
        return {"error": f"Error parsing response: {str(e)}", "raw_response": response.choices[0].message.content}

if __name__ == "__main__":
    # Path to the passport image
    image_path = "data/passport.png"
    
    # Extract passport data
    passport_data = extract_passport_data(image_path)
    
    with open('./data/passport_png.json', "w", encoding="utf-8") as f:
        json.dump(passport_data, f, indent=2, ensure_ascii=False)
    # print(json.dumps(passport_data))
    exit(0)
