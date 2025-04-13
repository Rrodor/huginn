import pandas as pd


def load(path: str) -> pd.DataFrame:

    try:
        data = pd.read_csv(path)
    except FileNotFoundError:
        print("File not found")
        exit(1)
    print("Loading dataset of dimensions {}".format(data.shape))
    return data
