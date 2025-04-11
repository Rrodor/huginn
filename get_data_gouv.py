import requests
import pandas as pd


def get_RID(dataset_name: str, round_number) -> str:
    if round_number == '2':
        return "41ed46cd-77c2-4ecc-b8eb-374aa953ca39"
    if round_number == '1':
        return "5163f2e3-1362-4c35-89a0-1934bb74f2d9"

def get_data_from_gouv(dataset_name: str, round_number) -> pd.DataFrame:
    try:
        rid = get_RID(dataset_name, round_number)
    except:
        return
    url = f"https://tabular-api.data.gouv.fr/api/resources/{rid}/data/csv/"
    print(f"url= {url}")
    response = requests.get(url)
    binary_content = response.content

    doc_name = dataset_name + ".csv"

    with open('test.csv', 'wb') as f:
        f.write(binary_content)

    print("data downloaded")
