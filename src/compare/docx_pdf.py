import json
import os

def compare_profile_account(profile_docx: dict, account_opening_pdf: dict) -> bool:
    """
    Compare common/derived fields from two JSONs.
    Returns True if all common fields are consistent, else False.
    """
    consistent = True
    
    # Mapping for directly comparable fields: key in profile_docx -> equivalent key in account_opening_pdf.
    mapping = {
        "last_name": "Account Holder's surname",
        "first_middle_name": "Account Holder's name",
        "passport_no_or_unique_id": "passport_number",
        "country_of_domicile": "country",
        "communication_medium_telephone": "phone_number",
        "communication_medium_email": "email",
    }
    
    for key1, key2 in mapping.items():
        val1 = profile_docx.get(key1, "").strip()
        val2 = account_opening_pdf.get(key2, "").strip()
        if val1 != val2:
            print(f"Inconsistency in field mapping: profile_docx[{key1}]='{val1}' vs account_opening_pdf[{key2}]='{val2}'")
            consistent = False

    # Compare full name derived from profile_docx (first_middle_name + " " + last_name) to account_opening_pdf's "Name of the account"
    full_name_1 = (profile_docx.get("first_middle_name", "").strip() + " " + profile_docx.get("last_name", "").strip()).strip()
    full_name_2 = account_opening_pdf.get("Name of the account", "").strip()
    if full_name_1 != full_name_2:
        print(f"Inconsistency in full name: '{full_name_1}' vs '{full_name_2}'")
        consistent = False

    # Compare address: use profile_docx address and account_opening_pdf components to construct address.
    address1 = profile_docx.get("address", "").strip()
    address2 = f"{account_opening_pdf.get('street_name', '').strip()} {account_opening_pdf.get('building_number', '').strip()}, {account_opening_pdf.get('postal_code', '').strip()} {account_opening_pdf.get('city', '').strip()}"
    if address1 != address2:
        print(f"Inconsistency in address: '{address1}' vs '{address2}'")
        consistent = False
    
    return consistent

# Example usage:
if __name__ == "__main__":

    with open("./data/profile_docx.json", "r", encoding="utf-8") as f:
        profile_docx = json.load(f) 

    with open("./data/account_opening_pdf.json", "r", encoding="utf-8") as f:
        account_opening_pdf = json.load(f) 

    result = compare_profile_account(profile_docx, account_opening_pdf)
    print("Consistency:", True)
