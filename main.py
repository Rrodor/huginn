from get_data_gouv import get_data_from_gouv
import load_csv
import os
import pandas as pd
from Candidat import Candidat
import sys

#===========================================================#
#                DISPLAY                                    #
#===========================================================#

def colored_text(text, color):
    colors = {
        'yellow': '\033[93m',
        'green': '\033[92m',
        'red': '\033[91m',
        'blue': '\033[94m',
        'reset': '\033[0m'
    }
    return f"{colors.get(color, '')}{text}{colors['reset']}"

def hugenote_prompt(message):
    prefix = colored_text("[HUGENOTE]:", "yellow")
    return input(f"{prefix} {message}\nPlease, type your answer... ").strip()

def display_header():
    header = """
    ╔══════════════════════════════════════════════════════════════════════════╗
    ║                                                                          ║
    ║  ██╗  ██╗██╗   ██╗ ██████╗ ███████╗███╗   ██╗ ██████╗ ████████ ███████╗  ║
    ║  ██║  ██║██║   ██║██╔════╝ ██╔════╝████╗  ██║██╔═══██╗╚══██╔══ ██╔════╝  ║
    ║  ███████║██║   ██║██║  ███╗█████╗  ██╔██╗ ██║██║   ██║   ██║   █████╗    ║
    ║  ██╔══██║██║   ██║██║   ██║██╔══╝  ██║╚██╗██║██║   ██║   ██║   ██╔══╝    ║
    ║  ██║  ██║╚██████╔╝╚██████╔╝███████╗██║ ╚████║╚██████╔╝   ██║   ███████╗  ║
    ║  ╚═╝  ╚═╝ ╚═════╝  ╚═════╝ ╚══════╝╚═╝  ╚═══╝ ╚═════╝    ╚═╝   ╚══════╝  ║
    ║                                                                          ║
    ║                     French Elections Data Explorer                       ║
    ║                                  v0.1                                    ║
    ╚══════════════════════════════════════════════════════════════════════════╝
    """
    print(header)
    print(colored_text("Welcome to Project HUGENOTE!", "green"))
    print("This tool presents the ordered results of any circonscription")
    print("from the French legislative elections of the last 5 years.")
    print()

#===========================================================#
#                DATA                                       #
#===========================================================#

def get_legi_data():
    try:
        df = load_csv.load("test.csv")
    except FileNotFoundError:
        print(colored_text("[HUGENOTE]:", "yellow"), "Error: Data file not found. Please try again.")
        return
    except Exception as e:
        print(colored_text("[HUGENOTE]:", "yellow"), f"Error loading data: {e}")
        return

    while True:
        try:
            departement_number = hugenote_prompt("Quel departement ? (ex: 75, 01, 971)")
            if not departement_number:
                print(colored_text("[HUGENOTE]:", "yellow"), "Department number cannot be empty.")
                continue
                
            circonscription_number = hugenote_prompt("Quelle circonscription ?")
            if not circonscription_number:
                print(colored_text("[HUGENOTE]:", "yellow"), "Circonscription number cannot be empty.")
                continue
                
            if not (departement_number.isdigit() or (departement_number.startswith('0') and departement_number[1:].isdigit())):
                print(colored_text("[HUGENOTE]:", "yellow"), "Le numéro de département doit être un nombre.")
                continue
                
            if not circonscription_number.isdigit():
                print(colored_text("[HUGENOTE]:", "yellow"), "Le numéro de circonscription doit être un nombre.")
                continue
                
            code_circo = departement_number + circonscription_number
            break
        except Exception as e:
            print(colored_text("[HUGENOTE]:", "yellow"), f"Input error: {e}. Please try again.")

    try:
        filtered_df = df[df['Code circonscription législative'] == code_circo]
        if not len(filtered_df):
            print(colored_text("[HUGENOTE]:", "yellow"), f"Error: No data found for department {departement_number}, circonscription {circonscription_number}.")
            return

        candidats = list()
        for i in range(19, 200, 9):
            try:
                if i < len(filtered_df.iloc[0]) and filtered_df.iloc[0].iloc[i] and pd.notna(filtered_df.iloc[0].iloc[i]):
                    voix_value = filtered_df.iloc[0].iloc[i+5]
                    voix_inscrits_value = filtered_df.iloc[0].iloc[i+6]
                    voix_exprimes_value = filtered_df.iloc[0].iloc[i+7]
                    
                    # HANDLE DATA FORMAT ISSUE (TO UPDATE)
                    if isinstance(voix_value, str) and voix_value.strip():
                        voix = int(voix_value)
                    else:
                        voix = int(voix_value)
                        
                    if isinstance(voix_inscrits_value, str) and voix_inscrits_value.strip():
                        voix_inscrits = float(voix_inscrits_value.replace(',','.').replace('%',''))
                    else:
                        voix_inscrits = float(voix_inscrits_value)
                        
                    if isinstance(voix_exprimes_value, str) and voix_exprimes_value.strip():
                        voix_exprimes = float(voix_exprimes_value.replace(',','.').replace('%',''))
                    else:
                        voix_exprimes = float(voix_exprimes_value)
                    
                    new_candidat = Candidat(
                        nuance=filtered_df.iloc[0].iloc[i+1],
                        family_name=filtered_df.iloc[0].iloc[i+2],
                        surname=filtered_df.iloc[0].iloc[i+3],
                        sexe=filtered_df.iloc[0].iloc[i+4],
                        voix=voix,
                        voix_inscrits=voix_inscrits,
                        voix_exprimes=voix_exprimes
                    )
                    candidats.append(new_candidat)
                else:
                    break
            except (ValueError, IndexError) as e:
                print(colored_text("[HUGENOTE]:", "red"), f"Warning: Could not process candidate data at index {i}: {e}")
                continue

        if not candidats:
            print(colored_text("[HUGENOTE]:", "blue"), "No candidate data found for this circonscription.")
            return

        candidats.sort(key=lambda x: x.voix, reverse=True)

        print(f"\n{colored_text('[HUGENOTE]:', 'green')} Results for Department {departement_number}, Circonscription {circonscription_number}:")
        print("-" * 60)
        for i, candidat in enumerate(candidats):
            elected_status = " (ÉLU)" if candidat.elu else ""
            print(f"{i+1}:  {candidat.surname} {candidat.family_name} pour {candidat.nuance} avec {candidat.voix} voix ({candidat.voix_exprimes:.2f}%){elected_status}")
        print("-" * 60)

    except Exception as e:
        print(colored_text("[HUGENOTE]:", "red"), f"Error processing data: {e}")

#===========================================================#
#                ELECTION MANAGER                           #
#===========================================================#

def handle_legi_output():
    try:
        # ASK FOR YEAR (TO UPDATE AND IMPROVE)
        # Handle the election between 1958 and 2012.
        # Let the user choose any year, if it's not matching any election date, ask him for the closest next/previous election.
        while True:
            year_input = hugenote_prompt("Which year are you looking for?")
            if year_input in ['2024']:
                break
            else:
                print(colored_text("[HUGENOTE]:", "blue"), "Invalid year. Currently only 2017 and 2022 are supported.")

        while True:
            turn_input = hugenote_prompt("Which turn are you looking for? (1 or 2)")
            if turn_input in ['1', '2']:
                break
            else:
                print(colored_text("[HUGENOTE]:", "blue"), "Invalid round number. Please enter 1 or 2.")

        print(colored_text("[HUGENOTE]:", "green"), "Fetching data from data.gouv.fr...")
        get_data_from_gouv("test", turn_input)
        get_legi_data()
    except Exception as e:
        print(colored_text("[HUGENOTE]:", "red"), f"Error processing legislative election data: {e}")

#===========================================================#
#                MAIN                                       #
#===========================================================#

def main():
    try:
        # DISPLAY HEADER AN INTRODUCTION
        display_header()
        
        # REMOVE THE PREVIOUS DATASET
        if os.path.exists("test.csv"):
            try:
                os.remove("test.csv")
            except PermissionError:
                print(colored_text("[HUGENOTE]:", "red"), "Error: Could not delete existing data file (permission denied).")
                return
            except Exception as e:
                print(colored_text("[HUGENOTE]:", "red"), f"Error deleting existing data file: {e}")
                return

        # ASK FOR ELECTION TYPE
        while True:
            election_type = hugenote_prompt("Which election type do you want to look at? (type 'legi' for legislative elections)")
            # PARLIAMENT ELECTION PATH
            if election_type.lower() == 'legi':
                handle_legi_output()
                break
            else:
                print(colored_text("[HUGENOTE]:", "blue"), "Sorry, only 'legi' (legislative elections) is currently supported.")
            
    except KeyboardInterrupt:
        print(f"\n{colored_text('[HUGENOTE]:', 'green')} Program terminated by user.")
        sys.exit(0)
    except Exception as e:
        print(colored_text("[HUGENOTE]:", "red"), f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    main()