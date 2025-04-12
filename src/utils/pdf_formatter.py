import fitz
import os
import json

def extract_pdf_form_data(pdf_path):
    form_data = {}
    other_currency_value = None
    has_standard_currency = False
    
    try:
        doc = fitz.open(pdf_path)
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            
            widgets = page.widgets()
            
            for widget in widgets:
                try:
                    field_name = widget.field_name if hasattr(widget, 'field_name') else None
                    
                    field_value = widget.get_text() if hasattr(widget, 'get_text') else None
                    
                    if not field_value and hasattr(widget, 'field_value'):
                        field_value = widget.field_value
                    
                    if field_name and field_value:
                        if field_name == 'other_ccy' or 'other_ccy' in field_name.lower():
                            other_currency_value = field_value
                        elif 'other' in field_name.lower() and 'currency' in field_name.lower():
                            other_currency_value = field_value
                        
                        if any(curr in field_name.lower() for curr in ['chf', 'eur', 'usd']):
                            is_checked = (
                                field_value == "Yes" or 
                                field_value == "On" or 
                                field_value == "True" or 
                                field_value == "Checked" or
                                field_value == "Selected" or
                                field_value == "1" or
                                field_value is True
                            )
                            
                            if is_checked:
                                has_standard_currency = True
                                if 'chf' in field_name.lower():
                                    form_data['Currency'] = 'CHF'
                                elif 'eur' in field_name.lower():
                                    form_data['Currency'] = 'EUR'
                                elif 'usd' in field_name.lower():
                                    form_data['Currency'] = 'USD'
                        
                        elif 'name of the account' in field_name.lower() or field_name == 'account_name':
                            form_data['Name of the account'] = field_value
                        elif "account holder's name" in field_name.lower() or field_name == 'account_holder_name':
                            form_data["Account Holder's name"] = field_value
                        elif "account holder's surname" in field_name.lower() or field_name == 'account_holder_surname':
                            form_data["Account Holder's surname"] = field_value
                        else:
                            form_data[field_name] = field_value
                
                except Exception as widget_error:
                    print(f"Warning: Could not process widget: {widget_error}")
        
        if not has_standard_currency and other_currency_value and other_currency_value.strip():
            if other_currency_value.lower() != 'off':
                form_data['Currency'] = other_currency_value
                if 'other_ccy' in form_data:
                    del form_data['other_ccy']
        
        doc.close()
        
    except Exception as e:
        print("An error occurred:", e)
        import traceback
        traceback.print_exc()
    
    return form_data

def flatten_pdf_with_fitx(input_pdf_path, output_pdf_path):
    try:
        orig_doc = fitz.open(input_pdf_path)
        
        new_doc = fitz.open()
        
        for page_num in range(len(orig_doc)):
            page = orig_doc[page_num]
            
            new_page = new_doc.new_page(width=page.rect.width, height=page.rect.height)
            
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
            new_page.insert_image(new_page.rect, pixmap=pix)
            
            widgets = page.widgets()
            form_data = []
            
            for widget in widgets:
                try:
                    field_value = widget.get_text() if hasattr(widget, 'get_text') else None
                    
                    if not field_value and hasattr(widget, 'field_value'):
                        field_value = widget.field_value
                        
                    if not field_value:
                        continue
                        
                    form_data.append({
                        'rect': widget.rect,
                        'value': field_value
                    })
                except Exception as widget_error:
                    print(f"Warning: Could not process widget: {widget_error}")
            
            for field in form_data:
                rect = field['rect']
                value = field['value']
                
                text_point = fitz.Point(rect.x0 + 2, rect.y0 + (rect.height * 0.7))
                
                new_page.insert_text(
                    text_point,
                    str(value),
                    fontsize=11,
                    color=(0, 0, 0)
                )
        
        new_doc.save(output_pdf_path)
        
        new_doc.close()
        orig_doc.close()
        
    except Exception as e:
        print("An error occurred:", e)
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    input_pdf = os.path.join("data", "account_opening.pdf")
    output_pdf = os.path.join("data", "account_opening_flat.pdf")
    output_json = os.path.join("data", "account_opening_pdf.json")
    
    form_data_dict = extract_pdf_form_data(input_pdf)
    
    # Save the dictionary to a JSON file
    with open(output_json, 'w') as json_file:
        json.dump(form_data_dict, json_file, indent=4)
    
    flatten_pdf_with_fitx(input_pdf, output_pdf)
    exit(0)
