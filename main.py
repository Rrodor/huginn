from get_data_gouv import get_data_from_gouv
import load_csv
import os
import pandas as pd
from Candidat import Candidat

def test_func():
    df = load_csv.load("test.csv")

    departement_number = input("quel departement ?\n->")
    circonscription_number = input("quel circonscription ?\n->")
    #error check

    code_circo = departement_number + circonscription_number

    filtered_df = df[df['Code circonscription législative'] == code_circo]
    if not len(filtered_df):
        print("error")
        return

    candidats = list()
    for i in range (19, 200, 9):
        if filtered_df.iloc[0].iloc[i] and pd.notna(filtered_df.iloc[0].iloc[i]):
            new_candidat = Candidat(nuance = filtered_df.iloc[0].iloc[i+1],
                                    family_name = filtered_df.iloc[0].iloc[i+2],
                                    surname = filtered_df.iloc[0].iloc[i+3],
                                    sexe = filtered_df.iloc[0].iloc[i+4],
                                    voix=int(filtered_df.iloc[0].iloc[i+5]),
                                    voix_inscrits=float(filtered_df.iloc[0].iloc[i+6].replace(',','.').replace('%','')),
                                    voix_exprimes=float(filtered_df.iloc[0].iloc[i+7].replace(',','.').replace('%','')))
            candidats.append(new_candidat)
        else:
            break

    candidats.sort(key=lambda x: x.voix, reverse=True)

    for i, candidat in enumerate(candidats):
        print (f"{i+1}:  {candidat.surname} {candidat.family_name} pour {candidat.nuance} avec {candidat.voix} voix")


def main():
    if os.path.exists("test.csv"):
        os.remove("test.csv")

    print("Welcome to the V0 of project Huggin.\n This V0 aim will present the ordered result of any circonscription of the french legislative election of the last 5 years.")
    year_input = input("which year are your looking for? (need implementation)\n->")
    round_input = input("which round are you looking for?\n->")

    if not round_input == '1' and not round_input == '2':
        print("invalid round number")
        return

    # if not os.path.exists("test.csv"):
        # print("unable to find data, start fetching")

    get_data_from_gouv("test", round_input)
    test_func()



if __name__ == "__main__":
    main()
