import requests
import pandas as pd
import zipfile
import os
import re
import shutil
from loguru import logger
from utils import colored_text, hugenote_prompt
from load_csv import load
from io import BytesIO

def get_RID(dataset_name: str, election_type: str, year: str) -> str:

    if (election_type == 'district'):
        if (1958 <= int(year) <= 2012):
            return "82734ca4-9362-42b8-8646-395a1bd8ec1c"
        else:
            print(colored_text("[HUGENOTE]:", "red"), "Only year between 1958 and 2012 are available in this version")
            return None
    # LEGISLATIVE ELECTION 2024
    # if round_number == '2':
    #     return "41ed46cd-77c2-4ecc-b8eb-374aa953ca39"
    # if round_number == '1':
    #     return "5163f2e3-1362-4c35-89a0-1934bb74f2d9"

def get_data_from_gouv(dataset_name: str, election_type: str, year: str) -> pd.DataFrame:
    
    try:
        rid = get_RID(dataset_name, election_type, year)
        if not rid:
            print(colored_text("[HUGENOTE]:", "red"), "Error while fetching data from data.gouv.fr")
            return False
        
        # REMOVE PREVIOUS DATA
        data_dir = "hugenote_data"
        if os.path.exists(data_dir):
            shutil.rmtree(data_dir)
        os.makedirs(data_dir, exist_ok=True)

        # FETCH DATA.GOUV
        url = f"https://www.data.gouv.fr/fr/datasets/r/{rid}"
        response = requests.get(url)
        if response.status_code != 200:
            print(colored_text("[HUGENOTE]:", "red"), f"Failed to download archive: HTTP {response.status_code}")
            return False

        # EXTRACT
        print(colored_text("[HUGENOTE]:", "green"), "Fetch has been a success!")
        print(colored_text("[HUGENOTE]:", "blue"), "Extracting archive...")
        with zipfile.ZipFile(BytesIO(response.content)) as zip_ref:
            zip_ref.extractall(data_dir)
        print(colored_text("[HUGENOTE]:", "green"), "Archive extraction has been a success!")

        # GET CSV NAME
        csv_files = []
        for root, _, files in os.walk(data_dir):
            for file in files:
                if file.endswith('.csv'):
                    csv_files.append(os.path.join(root, file))
        if not csv_files:
            print("No CSV files found in the archive")
            return False
        
        # PREPARE TARGET
        first_round_filename = "cdsp_legi" + year + "t1_circ"
        second_round_filename = "cdsp_legi" + year + "t2_circ"
        
        for file_path in csv_files:
            file_name = os.path.basename(file_path)
            if first_round_filename.lower() in file_name.lower():
                first_round_file = file_path
            elif second_round_filename.lower() in file_name.lower():
                second_round_file = file_path

        if not first_round_file:
            print(colored_text("[HUGENOTE]:", "red"), f"First round data not found for year {year}")
            return None, None
        
        if not second_round_file:
            print(colored_text("[HUGENOTE]:", "red"), f"Second round data not found for year {year}")
            return None, None

        print(colored_text("[HUGENOTE]:", "blue"), f"Loading first round data: {os.path.basename(first_round_file)}")
        first_round_df = load(first_round_file)
        
        print(colored_text("[HUGENOTE]:", "blue"), f"Loading second round data: {os.path.basename(second_round_file)}")
        second_round_df = load(second_round_file)
        
        print(colored_text("[HUGENOTE]:", "green"), "Successfully loaded both election rounds!")
        
        return first_round_df, second_round_df

    except Exception as e:
        logger.error(f"error: {e}")