import json
import os

def compare_account_passport():
    """
    Compare values between account_opening_pdf.json and passport_png.json files.
    Performs case-insensitive comparison of relevant fields.
    
    Returns:
        str: True if all comparisons match, False otherwise
    """
    
    current_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    data_dir = os.path.join(current_dir, 'data')
    
    
    try:
        with open(os.path.join(data_dir, 'account_opening_pdf.json'), 'r') as account_file:
            account_data = json.load(account_file)
        
        with open(os.path.join(data_dir, 'passport_png.json'), 'r') as passport_file:
            passport_data = json.load(passport_file)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return 'Reject'
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
        return 'Reject'
    
    
    comparisons = [
        # Compare full name (first_name + surname from passport equals name in account)
        {
            'passport_field': lambda data: (data.get('First_name', '') + ' ' + data.get('Surname', '')).lower(),
            'account_field': lambda data: data.get('name', '').lower(),
            'description': 'Full name'
        },
        # Compare passport number
        {
            'passport_field': lambda data: data.get('Passport_number', '').lower(),
            'account_field': lambda data: data.get('passport_number', '').lower(),
            'description': 'Passport number'
        },
        # Compare first name
        {
            'passport_field': lambda data: data.get('First_name', '').lower(),
            'account_field': lambda data: data.get('Account Holder\'s name', '').lower(),
            'description': 'First name'
        },
        # Compare surname
        {
            'passport_field': lambda data: data.get('Surname', '').lower(),
            'account_field': lambda data: data.get('Account Holder\'s surname', '').lower(),
            'description': 'Surname'
        }
    ]
    
    
    all_match = True
    mismatches = []
    
    for comparison in comparisons:
        passport_value = comparison['passport_field'](passport_data)
        account_value = comparison['account_field'](account_data)
        
        if passport_value != account_value:
            all_match = False
            mismatches.append({
                'field': comparison['description'],
                'passport_value': passport_value,
                'account_value': account_value
            })
    
    # Print results for debugging
    if not all_match:
        print("Mismatches found:")
        for mismatch in mismatches:
            print(f"  {mismatch['field']}: '{mismatch['passport_value']}' vs '{mismatch['account_value']}'")
    else:
        print("All fields match successfully.")
    
    return True if all_match else False

# if __name__ == "__main__":
    
#     result = compare_account_passport()
#     print(f"Comparison result: {result}")
