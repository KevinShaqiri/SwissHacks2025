import requests
import os
import json
import base64
# from src.parse_docx import 
# from src.docx_txt

base_url = 'https://hackathon-api.mlo.sehlat.io'

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
        

def main():
    session_id, client_id = start_session()
    status = "success"
    score = 0
    # while (status != "gameover") and (status != None):
    client_id, score, status = make_prediction(session_id, client_id, "Accept")
    
    print(f"The score reached is {score}")


if __name__ == '__main__':

    main()  
