import os
import base64
from openai import OpenAI
import json
from pathlib import Path
import re
from datetime import datetime

def encode_image(image_path):
    """Encode image to base64 string"""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def convert_date_format(date_str):
    """Convert date from formats like '03-Jun-2021' to ISO format '2021-06-03'"""
    if not date_str or date_str == "null":
        return date_str
    
    # Try different date formats
    date_formats = [
        # 03-Jun-2021, 3-Jun-2021, 03 Jun 2021, 3 Jun 2021
        r'(\d{1,2})[-\s]([A-Za-z]{3})[-\s](\d{4})',
        # Jun-03-2021, Jun 03 2021
        r'([A-Za-z]{3})[-\s](\d{1,2})[-\s](\d{4})',
        # 03.06.2021, 3.6.2021
        r'(\d{1,2})\.(\d{1,2})\.(\d{4})',
        # 03/06/2021, 3/6/2021
        r'(\d{1,2})/(\d{1,2})/(\d{4})',
        # 2021-06-03, 2021.06.03, 2021/06/03
        r'(\d{4})[-\./](\d{1,2})[-\./](\d{1,2})'
    ]
    
    # Month name to number mapping
    month_map = {
        'jan': '01', 'feb': '02', 'mar': '03', 'apr': '04', 'may': '05', 'jun': '06',
        'jul': '07', 'aug': '08', 'sep': '09', 'oct': '10', 'nov': '11', 'dec': '12'
    }
    
    for pattern in date_formats:
        match = re.search(pattern, date_str, re.IGNORECASE)
        if match:
            groups = match.groups()
            
            # Format: DD-MMM-YYYY or DD MMM YYYY
            if len(groups) == 3 and len(groups[1]) == 3 and groups[1].lower() in month_map:
                day = groups[0].zfill(2)
                month = month_map[groups[1].lower()]
                year = groups[2]
                return f"{year}-{month}-{day}"
            
            # Format: MMM-DD-YYYY or MMM DD YYYY
            elif len(groups) == 3 and len(groups[0]) == 3 and groups[0].lower() in month_map:
                day = groups[1].zfill(2)
                month = month_map[groups[0].lower()]
                year = groups[2]
                return f"{year}-{month}-{day}"
            
            # Format: DD.MM.YYYY or DD/MM/YYYY
            elif len(groups) == 3 and len(groups[0]) <= 2 and len(groups[1]) <= 2:
                day = groups[0].zfill(2)
                month = groups[1].zfill(2)
                year = groups[2]
                return f"{year}-{month}-{day}"
            
            # Format: YYYY-MM-DD, YYYY.MM.DD, YYYY/MM/DD
            elif len(groups) == 3 and len(groups[0]) == 4:
                year = groups[0]
                month = groups[1].zfill(2)
                day = groups[2].zfill(2)
                return f"{year}-{month}-{day}"
    
    # If no pattern matched, try parsing with datetime
    try:
        # Try various formats
        for fmt in ["%d-%b-%Y", "%d %b %Y", "%b-%d-%Y", "%b %d %Y", 
                    "%d.%m.%Y", "%d/%m/%Y", "%Y-%m-%d", "%Y.%m.%d", "%Y/%m/%d"]:
            try:
                date_obj = datetime.strptime(date_str, fmt)
                return date_obj.strftime("%Y-%m-%d")
            except ValueError:
                continue
    except Exception:
        # If all parsing attempts fail, return the original string
        pass
    
    return date_str

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
            
            # Convert date formats for Issue_date and Expiry_date
            if 'Issue_date' in parsed_data and parsed_data['Issue_date']:
                parsed_data['Issue_date'] = convert_date_format(parsed_data['Issue_date'])
            
            if 'Expiry_date' in parsed_data and parsed_data['Expiry_date']:
                parsed_data['Expiry_date'] = convert_date_format(parsed_data['Expiry_date'])
                
            if 'Birth_date' in parsed_data and parsed_data['Birth_date']:
                parsed_data['Birth_date'] = convert_date_format(parsed_data['Birth_date'])
            
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
