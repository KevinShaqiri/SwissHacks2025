import requests
import os
import json
import base64
import re
import difflib
from src.compare.docx_pdf import compare_profile_account
from src.compare.docx_txt import compare_profile_description
from src.compare.pdf_png import compare_account_passport
from src.compare.pdf_txt import compare_account_description
from src.compare.png_txt import compare_passport_description
from src.utils.docx_json import docx_to_text, extract_json_from_docx_text
from src.utils.passport_json import extract_passport_data
from src.utils.pdf_formatter import extract_pdf_form_data
import time

base_url = 'https://hackathon-api.mlo.sehlat.io'

docx_path = 'data/profile.docx'
png_path = 'data/passport.png'
pdf_path = 'data/account_opening.pdf'
txt_path = 'data/description.txt'

def write_files(res: dict):

    if not os.path.isdir(os.path.join(os.getcwd(), 'data')):
            os.mkdir(os.path.join(os.getcwd(), 'data'))

    for (key, value) in res["client_data"].items():

        if key == "passport":
            with open('./data/passport.png', 'wb') as file:
                file.write(base64.b64decode(value))

        elif key == "profile":
            with open('./data/profile.docx', 'wb') as file:
                file.write(base64.b64decode(value))

        elif key == "description":
            with open('./data/description.txt', 'wb') as file:
                file.write(base64.b64decode(value))

        elif key == "account":
            with open('./data/account_opening.pdf', 'wb') as file:
                file.write(base64.b64decode(value))
        else:
            print(f"Unexpected file format: {key}, saving failed.")

    return


def start_session():
    
    headers = {
        "x-api-key": "B2z7Cx_ui0dGJBVWZRLbzU40G2PB4UjeFqjQZd4-9ew",
        "Content-Type": "application/json",

    }

    data = json.dumps({

        "player_name": "techy"
    })

    response = requests.post(url=base_url+'/game/start', 
                             headers=headers, 
                             data=data)
    
    if response.status_code == 200:
    
        res = response.json()

        session_id = res['session_id']
        client_id = res['client_id']

        write_files(res)

        return session_id, client_id
    
    else:
        print(f"Connection failed. Error Code: {response.status_code}")
        return None, None


def make_prediction(session_id: str, client_id: str, pred: str):

    headers = {
        "x-api-key": "B2z7Cx_ui0dGJBVWZRLbzU40G2PB4UjeFqjQZd4-9ew",
        "Content-Type": "application/json",
    }

    data = json.dumps({
        "decision": pred,
        "session_id": session_id,
        "client_id": client_id
    })

    response = requests.post(url=base_url+'/game/decision', 
                             headers=headers, 
                             data=data)
    
    if response.status_code == 200:
        res = response.json()
        
        status = res["status"]
        client_id = res["client_id"]
        score = res["score"]
        
        if status == "gameover":
            return client_id, score, status
        
        else:
            write_files(res)
            return client_id, score, status

    else:
        print(f"Connection failed. Error Code: {response.status_code}")
        return None, None, None

def extract_jsons():

    docx_text = docx_to_text(docx_path)
    docx_json = extract_json_from_docx_text(docx_text)
    print("Saving JSON to ")
    with open('data/profile_docx.json', "w", encoding="utf-8") as f:
        json.dump(docx_json, f, indent=2, ensure_ascii=False)

    passport_json = extract_passport_data(png_path)
    with open('./data/passport_png.json', "w", encoding="utf-8") as f:
        json.dump(passport_json, f, indent=2, ensure_ascii=False)
    
    pdf_json = extract_pdf_form_data(pdf_path)
    with open("./data/account_opening_pdf.json", 'w') as json_file:
        json.dump(pdf_json, json_file, indent=4)
    print("Finished loading JSONs.")
    return docx_json, passport_json, pdf_json 

def extract_patterns_from_text(text):
    """
    Extract common patterns from text using regex
    """
    patterns = {
        'email': re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text),
        'phone': re.findall(r'(?:\+\d{1,3}[-\.\s]?)?(?:\(?\d{3}\)?[-\.\s]?)?\d{3}[-\.\s]?\d{4,}', text),
        'dates': re.findall(r'\b(?:\d{1,2}[-/\.]\d{1,2}[-/\.]\d{2,4}|\d{2,4}[-/\.]\d{1,2}[-/\.]\d{1,2}|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{4})\b', text, re.IGNORECASE),
        'passport': re.findall(r'\b[A-Z0-9]{6,10}\b', text),
        'names': re.findall(r'\b(?:[A-Z][a-z]+ ){1,2}[A-Z][a-z]+\b', text),
        'addresses': re.findall(r'\b\d+\s+[A-Za-z\s,]+(?:Road|Rd|Street|St|Avenue|Ave|Boulevard|Blvd|Lane|Ln|Drive|Dr|Court|Ct|Plaza|Plz|Terrace|Ter|Place|Pl)\b', text, re.IGNORECASE),
        'postcodes': re.findall(r'\b[A-Z]{1,2}\d[A-Z\d]? \d[A-Z]{2}\b|\b\d{5}(?:-\d{4})?\b', text),
        'money_amounts': re.findall(r'\$\s*\d+(?:,\d{3})*(?:\.\d{2})|\d+(?:,\d{3})*(?:\.\d{2})?\s*(?:dollars|USD|GBP|EUR|pounds|euros)', text, re.IGNORECASE),
        'percentages': re.findall(r'\b\d+(?:\.\d+)?%\b', text),
        'years': re.findall(r'\b(19|20)\d{2}\b', text),
        'age': re.findall(r'\b(?:age(?:d)?\s+|is\s+)(\d{1,3})(?:\s+years\s+old)?\b', text, re.IGNORECASE)
    }
    return patterns

def check_key_field_in_text(field_name, field_value, text):
    """
    Check if a specific key field from a document appears in the text
    Returns: (bool, str) - (is_consistent, explanation)
    """
    if not field_value:  # Skip empty fields
        return True, f"{field_name} is empty in document"
    
    # Clean and prepare the field value for matching
    clean_value = str(field_value).strip().lower()
    clean_text = text.lower()
    
    # Try exact match first
    if clean_value in clean_text:
        return True, f"{field_name} '{field_value}' found in text"
    
    # Try fuzzy matching for longer fields
    if len(clean_value) > 3:
        # Split into words and check if most words appear near each other
        words = clean_value.split()
        word_found_count = sum(1 for word in words if word in clean_text)
        if word_found_count / len(words) >= 0.7:  # 70% of words found
            return True, f"{field_name} '{field_value}' partially matched in text"
    
    # For names, try checking first name and last name separately
    if 'name' in field_name.lower() and ' ' in clean_value:
        name_parts = clean_value.split()
        first_name = name_parts[0]
        last_name = name_parts[-1]
        
        if first_name in clean_text and last_name in clean_text:
            return True, f"{field_name} parts '{first_name}' and '{last_name}' found separately in text"
    
    # For dates, try different formats
    if any(date_word in field_name.lower() for date_word in ['date', 'birth', 'dob']):
        # Try to extract all dates from the field value
        dates_in_field = re.findall(r'\d+', clean_value)
        dates_in_text = re.findall(r'\d+', clean_text)
        
        # Check if the dates are present in the text
        if all(date in dates_in_text for date in dates_in_field):
            return True, f"{field_name} date components found in text"
    
    # For financial amounts, check for numeric part
    if any(money_word in field_name.lower() for money_word in ['amount', 'balance', 'money', 'income']):
        # Extract numeric values
        amounts = re.findall(r'\d+(?:,\d{3})*(?:\.\d+)?', clean_value)
        if amounts:
            for amount in amounts:
                if amount in clean_text:
                    return True, f"{field_name} amount '{amount}' found in text"
    
    return False, f"{field_name} '{field_value}' NOT found in text"

def check_critical_fields(json_data, text):
    """
    Check if critical fields from a JSON document appear in the text
    Returns: (bool, list) - (all_consistent, list of inconsistencies)
    """
    # Define critical fields to check based on common JSON keys
    critical_fields = []
    inconsistencies = []
    
    # Dynamically identify critical fields from the JSON
    for key, value in json_data.items():
        # Classify fields as critical based on key names
        if any(critical_word in key.lower() for critical_word in 
               ['name', 'birth', 'address', 'passport', 'country', 'nationality', 'document', 
                'email', 'phone', 'occupation', 'income', 'education']):
            critical_fields.append((key, value))
    
    # Check each critical field
    all_consistent = True
    for field_name, field_value in critical_fields:
        is_consistent, explanation = check_key_field_in_text(field_name, field_value, text)
        if not is_consistent:
            all_consistent = False
            inconsistencies.append(f"INCONSISTENCY: {explanation}")
    
    return all_consistent, inconsistencies

def check_cross_document_fields(json1, json2, label1="Document 1", label2="Document 2"):
    """
    Compare specific fields across two documents
    Returns: (bool, list) - (all_consistent, list of inconsistencies)
    """
    inconsistencies = []
    
    # Define fields that should be compared across documents, with potential variations in key names
    field_mappings = [
        # Format: [[json1_possible_keys], [json2_possible_keys], field_description]
        [['name', 'full_name', 'client_name'], ['name', 'full_name', 'client_name'], "Name"],
        [['birth_date', 'date_of_birth', 'dob'], ['birth_date', 'date_of_birth', 'dob'], "Date of Birth"],
        [['country', 'nationality'], ['country', 'nationality'], "Country/Nationality"],
        [['passport_number', 'passport', 'document_number'], ['passport_number', 'passport', 'document_number'], "Passport/Document Number"],
        [['address', 'residence'], ['address', 'residence'], "Address"],
        [['email', 'email_address'], ['email', 'email_address'], "Email"],
        [['phone', 'telephone', 'phone_number'], ['phone', 'telephone', 'phone_number'], "Phone"],
        [['occupation', 'profession', 'job'], ['occupation', 'profession', 'job'], "Occupation"]
    ]
    
    all_consistent = True
    
    for json1_keys, json2_keys, field_desc in field_mappings:
        # Get values from both documents if they exist
        json1_value = None
        json2_value = None
        
        for key in json1_keys:
            if key in json1 and json1[key]:
                json1_value = str(json1[key]).strip().lower()
                break
                
        for key in json2_keys:
            if key in json2 and json2[key]:
                json2_value = str(json2[key]).strip().lower()
                break
        
        # If both documents have this field, compare them
        if json1_value and json2_value:
            # Exact match
            if json1_value == json2_value:
                continue
                
            # Fuzzy match for longer strings
            if len(json1_value) > 3 and len(json2_value) > 3:
                similarity = difflib.SequenceMatcher(None, json1_value, json2_value).ratio()
                if similarity >= 0.8:  # 80% similar
                    continue
            
            # Name specific comparison
            if field_desc == "Name" and ' ' in json1_value and ' ' in json2_value:
                # Compare first and last names separately
                json1_parts = json1_value.split()
                json2_parts = json2_value.split()
                
                # Check if first names match
                if json1_parts[0] == json2_parts[0]:
                    continue
                    
                # Check if last names match
                if json1_parts[-1] == json2_parts[-1]:
                    continue
            
            # Date specific comparison - compare numeric parts
            if field_desc == "Date of Birth":
                date1_nums = re.findall(r'\d+', json1_value)
                date2_nums = re.findall(r'\d+', json2_value)
                
                if date1_nums == date2_nums:
                    continue
            
            # If we get here, the fields are inconsistent
            all_consistent = False
            inconsistencies.append(f"INCONSISTENCY: {field_desc} doesn't match between {label1} and {label2}: '{json1_value}' vs '{json2_value}'")
    
    return all_consistent, inconsistencies

def enhance_docx_txt_comparison(profile_docx, description_text):
    """
    Enhanced version of docx-txt comparison with much more thorough text analysis
    """
    # First, check critical fields from profile_docx against the text
    critical_fields_match, inconsistencies = check_critical_fields(profile_docx, description_text)
    if not critical_fields_match:
        print("Critical field inconsistencies found:")
        for inconsistency in inconsistencies:
            print(f"  - {inconsistency}")
        return False
    
    # Extract patterns from text for additional verification
    text_patterns = extract_patterns_from_text(description_text)
    
    # Check for specific information in the text
    if 'names' in text_patterns and text_patterns['names']:
        print(f"Names found in text: {text_patterns['names']}")
        
        # Check if any name in the document matches names in text
        name_match = False
        document_name = None
        
        for key in profile_docx:
            if 'name' in key.lower() and profile_docx[key]:
                document_name = profile_docx[key]
                break
                
        if document_name:
            for text_name in text_patterns['names']:
                similarity = difflib.SequenceMatcher(None, document_name.lower(), text_name.lower()).ratio()
                if similarity >= 0.7:  # 70% similar
                    name_match = True
                    break
                    
            if not name_match:
                print(f"  - INCONSISTENCY: Document name '{document_name}' doesn't match any name in text")
                return False
    
    # Then, use the standard comparison as a backup
    basic_match = compare_profile_description(profile_docx, description_text)
    if not basic_match:
        print("  - Standard profile-description comparison failed")
        return False
    
    # Finally, perform a much stricter secondary check to confirm consistency
    system_prompt = """
You are an EXTREMELY METICULOUS document validation expert. Your task is to CAREFULLY analyze a text description 
and determine if it's 100% consistent with structured profile data.

CRITICAL INSTRUCTIONS:
1. READ THE TEXT DESCRIPTION WITH EXTREME THOROUGHNESS. Every single word matters.
2. Extract ALL factual details from the description (names, dates, locations, etc.).
3. Compare each extracted fact against the corresponding profile data field.
4. The text is PRIMARY - if any profile data contradicts the text, this is a SERIOUS inconsistency.
5. Be EXTREMELY CAREFUL with names, dates, locations, relationships, and financial information.
6. Pay careful attention to subtle contradictions that might indicate fraud.
7. Do not assume information not explicitly stated in the text.

YOUR DETERMINATION MUST BE STRICT:
- If there is ANY inconsistency between the text and profile, respond "False"
- Only if ALL information aligns perfectly, respond "True"

Your final output must be EXACTLY "True" or "False".
"""
    
    user_message = f"""
PROFILE DATA (structured):
{json.dumps(profile_docx, indent=2)}

TEXT DESCRIPTION:
{description_text}

Please determine if the text description is 100% consistent with the profile data.
Every factual detail in the profile must match what's stated in the text.
Search for ANY contradictions or inconsistencies, no matter how subtle.
"""
    
    from openai import OpenAI
    from dotenv import load_dotenv
    load_dotenv()
    
    client = OpenAI(api_key=os.getenv("SWISSHACKS_API"))
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt.strip()},
            {"role": "user", "content": user_message.strip()}
        ],
        temperature=0.0  # Zero temperature for most deterministic output
    )
    
    content = response.choices[0].message.content.strip().lower()
    
    # Return True only if the response explicitly contains "true"
    return "true" in content

def predict(txt, png_json, profile_docx, account_opening_pdf):
    """
    Predict whether to accept or reject a client based on checking:
    1. If first_name from the profile exists in the description text
    2. If passport full name exists in the description text
    Explains exactly where inconsistencies are found.
    """
    inconsistencies = []
    
    # --- FIRST NAME CHECK ---
    print("Checking if first_name exists in description text...")
    
    # Look for first_name field in profile_docx
    first_name = None
    first_name_source = None
    
    for key in profile_docx:
        if key.lower() == 'first_name' and profile_docx[key]:
            first_name = profile_docx[key]
            first_name_source = f"profile_docx['{key}']"
            break
    
    # If first_name field not found, try to find it in other fields
    if not first_name:
        for key in profile_docx:
            if 'name' in key.lower() and profile_docx[key]:
                # Try to extract first name from a full name
                name_parts = profile_docx[key].split()
                if name_parts:
                    first_name = name_parts[0]  # Take first part as first name
                    first_name_source = f"profile_docx['{key}'] (first part)"
                    break
    
    # If still no first_name found, check in other documents
    if not first_name:
        for key in account_opening_pdf:
            if key.lower() == 'first_name' and account_opening_pdf[key]:
                first_name = account_opening_pdf[key]
                first_name_source = f"account_opening_pdf['{key}']"
                break
            elif 'name' in key.lower() and account_opening_pdf[key]:
                # Try to extract first name from a full name
                name_parts = account_opening_pdf[key].split()
                if name_parts:
                    first_name = name_parts[0]  # Take first part as first name
                    first_name_source = f"account_opening_pdf['{key}'] (first part)"
                    break
    
    # If no first_name found anywhere, record inconsistency
    if not first_name:
        inconsistency_explanation = {
            "error_type": "MISSING_FIELD",
            "field": "first_name",
            "explanation": "Could not find first_name field in any document",
            "documents_checked": ["profile_docx", "account_opening_pdf"],
            "available_fields": {
                "profile_docx": list(profile_docx.keys()),
                "account_opening_pdf": list(account_opening_pdf.keys())
            }
        }
        inconsistencies.append(inconsistency_explanation)
    else:
        print(f"Looking for first_name: '{first_name}' (from {first_name_source}) in text")
        
        # Create a list of variations to look for
        first_name_variations = [
            first_name.lower(),
            first_name.upper(),
            first_name.capitalize()
        ]
        
        # For short names, be more careful about matching whole words
        if len(first_name) <= 3:
            # Use word boundary regex to find whole word matches
            found = False
            import re
            for variation in first_name_variations:
                pattern = r'\b' + re.escape(variation) + r'\b'
                if re.search(pattern, txt, re.IGNORECASE):
                    found = True
                    break
        else:
            # For longer names, simpler contains check is sufficient
            found = any(variation in txt.lower() for variation in first_name_variations)
        
        if not found:
            # Create detailed explanation of the inconsistency
            # Extract a short context from the text (first 100 chars) for reference
            text_sample = txt[:100] + "..." if len(txt) > 100 else txt
            
            inconsistency_explanation = {
                "error_type": "NAME_NOT_FOUND",
                "expected_field": "first_name",
                "expected_value": first_name,
                "source": first_name_source,
                "text_sample": text_sample,
                "text_length": len(txt),
                "explanation": f"The first name '{first_name}' from {first_name_source} was not found in the description text",
                "possible_names_in_text": extract_patterns_from_text(txt).get('names', [])
            }
            inconsistencies.append(inconsistency_explanation)
    
    # --- PASSPORT FULL NAME CHECK ---
    print("Checking if passport full name exists in description text...")
    
    # Look for full name in passport data
    passport_full_name = None
    passport_name_source = None
    
    # Check common name fields in passport
    for key in png_json:
        if 'name' in key.lower() and png_json[key]:
            passport_full_name = png_json[key]
            passport_name_source = f"passport_png['{key}']"
            break
    
    # If no full name found in passport, record inconsistency
    if not passport_full_name:
        inconsistency_explanation = {
            "error_type": "MISSING_FIELD",
            "field": "passport_full_name",
            "explanation": "Could not find full name field in passport document",
            "available_fields": list(png_json.keys())
        }
        inconsistencies.append(inconsistency_explanation)
    else:
        print(f"Looking for passport full name: '{passport_full_name}' (from {passport_name_source}) in text")
        
        # Check if the passport full name appears in the text (case insensitive)
        passport_name_found = False
        
        # Try exact match
        if passport_full_name.lower() in txt.lower():
            passport_name_found = True
        else:
            # Try more flexible matching by checking each part of the name
            name_parts = passport_full_name.split()
            parts_found = 0
            for part in name_parts:
                if len(part) > 2 and part.lower() in txt.lower():  # Only count parts with >2 chars
                    parts_found += 1
            
            # If most of the name parts are found, consider it a match
            if parts_found >= len(name_parts) * 0.7:  # 70% of parts found
                passport_name_found = True
        
        if not passport_name_found:
            # Create detailed explanation of the inconsistency
            text_sample = txt[:100] + "..." if len(txt) > 100 else txt
            
            inconsistency_explanation = {
                "error_type": "PASSPORT_NAME_NOT_FOUND",
                "expected_field": "passport_full_name",
                "expected_value": passport_full_name,
                "source": passport_name_source,
                "text_sample": text_sample,
                "explanation": f"The passport full name '{passport_full_name}' was not found in the description text",
                "possible_names_in_text": extract_patterns_from_text(txt).get('names', [])
            }
            inconsistencies.append(inconsistency_explanation)
    
    # --- DECISION LOGIC ---
    # If any inconsistencies were found, reject
    if inconsistencies:
        print("\n=== INCONSISTENCY DETAILS ===")
        for i, inconsistency in enumerate(inconsistencies, 1):
            print(f"Inconsistency #{i}:")
            print(json.dumps(inconsistency, indent=2))
            print("-----------------------------")
        print("=============================\n")
        
        print(f"DECISION: Reject - {len(inconsistencies)} inconsistencies found")
        return "Reject"
    
    # All checks passed
    print("DECISION: Accept - All name checks passed")
    return "Accept"

def main():
    session_id, client_id = start_session()
    print(f"Session started.\nSession ID: {session_id}\nClient ID: {client_id}\n")
    status = "success"
    score = 0
    
    while (status != "gameover") and (status != None):
        with open("./data/description.txt", "r", encoding="utf-8") as f:
            txt = f.read()
        profile_docx, png_json, account_opening_pdf = extract_jsons()
        pred = predict(txt, png_json, profile_docx, account_opening_pdf)
        print(f"Prediction made: {pred}")
        client_id, score, status = make_prediction(session_id, client_id, pred)
        print(f"Current score: {score}")
    
    print(f"The score reached is {score}")

if __name__ == '__main__':
    main()  
