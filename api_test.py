import requests
import re
import os
import pdfplumber
import json

base_url = 'https://hackathon-api.mlo.sehlat.io/game/start'

def get_data_from_api():
    
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }

    data = {

        "player_name": "Techy"
    }

    response = requests.post(url=base_url, 
                             headers=headers, 
                             data=data)
    
    if response.status_code == 200:
        data = response.json()
        return data
    else:
        print(f"API Error: {response.status_code}")


data = get_data_from_api()
print(data)
