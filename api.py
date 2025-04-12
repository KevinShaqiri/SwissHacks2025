import requests
import os
import json
import base64
from src.compare.docx_pdf import compare_profile_account
from src.compare.docx_txt import compare_profile_description
from src.compare.pdf_png import compare_account_passport
from src.compare.pdf_txt import compare_account_description
from src.compare.png_txt import compare_passport_description
from src.utils.docx_json import docx_to_text, extract_json_from_docx_text
from src.utils.passport_json import extract_passport_data
from src.utils.pdf_formatter import extract_pdf_form_data
import time
# from src.parse_docx import 
# from src.docx_txt

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
    
def predict(txt, png_json, profile_docx, account_opening_pdf):

    accept_acc_desc = compare_account_description(account_opening_pdf, txt)
    accept_prof_acc = compare_profile_account(profile_docx, account_opening_pdf)
    accept_acc_pass = compare_account_passport()
    accept_prof_desc = compare_profile_description(profile_docx, txt)
    # accept_png_desc = compare_passport_description(png_json, txt)
    
    matchings = {

        "PDF vs Text": accept_acc_desc,
        "DOCX vs PDF": accept_prof_acc, 
        "PDF vs PNG": accept_acc_pass,  
        "DOCX vs Text": accept_prof_desc,  
        # "Passport vs Text": accept_png_desc 
    }

    for key, value in matchings.items():
        print(f'{key}: {value}')

    if False not in matchings.values(): 
        return "Accept"
    else: 
        return "Reject" 

def main():
    session_id, client_id = start_session()
    print(f"Session started.\nSession ID: {session_id}\nClient ID: {client_id}\n")
    status = "success"
    score = 0
    
    while (status != "gameover") and (status != None):
        with open("./data/description.txt", "r", encoding="utf-8") as f:
            txt = f.read()
        profile_docx, png_json, account_opening_pdf = extract_jsons()
        time.sleep(2)
        pred = predict(txt, png_json, profile_docx, account_opening_pdf)
        print(f"Prediction made: {pred}")
        client_id, score, status = make_prediction(session_id, client_id, pred)
        print(f"Current score: {score}")
    
    print(f"The score reached is {score}")

if __name__ == '__main__':
    main()  
