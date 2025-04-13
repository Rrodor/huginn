from get_data_gouv import get_data_from_gouv
import load_csv
import os
import pandas as pd
from Candidat import Candidat
import sys

#===========================================================#
#                AESTHETIC DISPLAY                          #
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
    return input(f"{prefix} {message}\n>>> ").strip()

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

def get_value_from_df(row, column_name, default=0):
    try:
        if column_name in row:
            value = row[column_name]
            return 0 if pd.isna(value) else value
        return default
    except Exception:
        return default


def display_round_data(departement_code, district_code, current_dataframe):

    try:
        # FILTER COLUMNS
        district_nb = int(district_code)
        departement_nb = int(departement_code)
        filtered_df = None
        
        # COMPATIBILTY CHECK
        filter_attempts = [
            # NUMERIC FILTERING
            lambda df: df[(df['Code département'] == departement_nb) & (df['circonscription'] == district_nb)],
            # STRING FILTERING
            lambda df: df[(df['Code département'] == str(departement_nb)) & (df['circonscription'] == str(district_nb))],
            # STRING AND NUMERIC
            lambda df: df[(df['Code département'] == str(departement_nb)) & (df['circonscription'] == district_nb)],
            # NUMERIC AND STRING
            lambda df: df[(df['Code département'] == departement_nb) & (df['circonscription'] == str(district_nb))]]
        
        for filter_attempt in filter_attempts:
            try:
                result = filter_attempt(current_dataframe)
                if not result.empty:
                    filtered_df = result
                    break
            except Exception:
                continue
        
        if filtered_df is None or filtered_df.empty:
            print(colored_text("[HUGENOTE]:", "red"), 
                  f"No results found for: departement({departement_nb}), district({district_nb}).")
            return
        
        # GET DISTRICT LINE
        row = filtered_df.iloc[0]

        # HANDLE CANDIDATE NAME
        is_2002_format = any('1 voix' in col for col in filtered_df.columns)
        
        # GET STATISTICS with fallbacks for missing columns
        total_registered = get_value_from_df(row, 'Inscrits')
        total_voters = get_value_from_df(row, 'Votants')
        valid_votes = get_value_from_df(row, 'Exprimés')
        
        # GET BLANK VOTE IF THEY EXIST
        possible_blank_columns = ['Blancs et nuls', 'Blancs', 'Nuls']
        blank_void = 0
        for col in possible_blank_columns:
            if col in row:
                blank_void = get_value_from_df(row, col)
                break
        
        # MAKE PERCENTAGES 
        turnout_pct = (total_voters / total_registered * 100) if total_registered > 0 else 0
        abstention_pct = 100 - turnout_pct
        blank_void_pct = (blank_void / total_voters * 100) if total_voters > 0 else 0
        valid_votes_pct = (valid_votes / total_voters * 100) if total_voters > 0 else 0
        
        # PARTICIPATION STATISTICS
        print("-" * 50)
        print(colored_text("\nELECTION PARTICIPATION:", "green"))
        print("-" * 50)
        print(f"Registered voters:    {int(total_registered):,}")
        print(f"Turnout:              {int(total_voters):,} ({turnout_pct:.1f}%)")
        print(f"Abstention:           {int(total_registered - total_voters):,} ({abstention_pct:.1f}%)")
        print(f"Blank/void ballots:   {int(blank_void):,} ({blank_void_pct:.1f}%)")
        print(f"Valid votes:          {int(valid_votes):,} ({valid_votes_pct:.1f}%)")
        print("-" * 50)
        
        # PARTY RESULTS
        print(colored_text("POLITICAL PARTY RESULTS", "green"))
        print("-" * 50)
        
        # EXCLUDE NON RESULT COLUMNS
        always_excluded = [
            'Code département', 'département', 'circonscription',
            'élu premier tour', 'Inscrits', 'Votants', 'Exprimés', 
            'Blancs et nuls', 'Blancs', 'Nuls', ''
        ]
        
        # GET POLITICAL PARTY RESULT DYNAMICLY
        excluded_columns = set()
        for col in always_excluded:
            if col in filtered_df.columns:
                excluded_columns.add(col)
        
        party_results = []
        
        # HANDLE NAME AND PARTY FORMAT
        if is_2002_format:
            candidate_num = 1
            while True:
                voix_col = f"{candidate_num} voix"
                party_col = f"{candidate_num} nuance"
                name_col = f"{candidate_num} Nom candidat"
                firstname_col = f"{candidate_num} Prénom candidat"
                if voix_col not in row or pd.isna(row[voix_col]):
                    break
                try:
                    votes = pd.to_numeric(row[voix_col], errors='coerce')
                    party = row[party_col] if pd.notna(row[party_col]) else "Unknown"
                    candidate_name = f"{row[firstname_col]} {row[name_col]}" if pd.notna(row[name_col]) else ""

                    if pd.notna(votes) and votes > 0:
                        percentage = (votes / valid_votes * 100) if valid_votes > 0 else 0
                        party_results.append({
                            'party': f"{party} - {candidate_name}",
                            'votes': int(votes),
                            'percentage': percentage
                        })
                except (ValueError, TypeError, KeyError):
                    pass

                candidate_num += 1
        else:
            # HANDLE POLITICAL PARTY NAME ONLY
            for column in filtered_df.columns:
                if column not in excluded_columns:
                    try:
                        value = pd.to_numeric(row[column], errors='coerce')
                        if pd.notna(value) and value > 0:
                            score = int(value)
                            percentage = (score / valid_votes * 100) if valid_votes > 0 else 0
                            party_results.append({
                                'party': column,
                                'votes': score,
                                'percentage': percentage
                            })
                    except (ValueError, TypeError):
                        pass
        
        # SORT BY DESCENDING VOTE
        party_results.sort(key=lambda x: x['votes'], reverse=True)
        
        # DISPLAY PARTY RESULT
        if not party_results:
            print("No party result data available in this dataset.")
        else:
            for i, result in enumerate(party_results):
                if i == 0:
                    print(f"{result['party']:<25}: {result['votes']:,} votes ({result['percentage']:.1f}%) - LEADING")
                else:
                    print(f"{result['party']:<25}: {result['votes']:,} votes ({result['percentage']:.1f}%)")
        
        print("-" * 50)
        
        # CHECK ELECTION STATUS
        # elected_status = None
        # if 'élu premier tour' in row:
        #     status_value = get_value_from_df('élu premier tour')
        #     if status_value in ['O', 'OUI', 'Y', 'YES', True, 1]:
        #         elected_status = True
        #     elif status_value in ['N', 'NON', 'N', 'NO', False, 0]:
        #         elected_status = False
            
        #     if elected_status is not None:
        #         elected_text = "Yes" if elected_status else "No"
        #         print(f"Candidate elected in first round: {elected_text}")
        
    except Exception as e:
        print(colored_text("[HUGENOTE]:", "red"), f"Error displaying results: {e}")
        import traceback
        traceback.print_exc()

#===========================================================#
#                ELECTION MANAGER                           #
#===========================================================#

def handle_legi_input():
    try:

        # ASK FOR YEAR (TO UPDATE AND IMPROVE)
        # Handle the election between 1958 and 2012.
        # Let the user choose any year, if it's not matching any election date, ask him for the closest next/previous election.
        while True:
            year_input = hugenote_prompt("Which year are you looking for?")
            if year_input.isdigit() and year_input in ['1958', '1962', '1967', '1968', '1973', '1978', '1981', '1986', '1988', '1993', '1997', '2002', '2007', '2012']:
                break
            else:
                print(colored_text("[HUGENOTE]:", "red"), "Invalid year. Try '1958', '1962', '1967', '1968', '1973', '1978', '1981', '1986', '1988', '1993', '1997', '2002', '2007', '2012'")

        # ASK FOR TYPE OF DATA NEEDED
        # Add 'nation' to type input when the database is setup.
        while True:
            type_input = hugenote_prompt("Which data are you looking for? (for this version, only 'district' is supported)")
            if type_input in ['district']:
                break
            else:
                print(colored_text("[HUGENOTE]:", "red"), "Invalid input, please enter 'district' the vizualize the outcome of an election round.")

        # FETCH LEGI DATA
        print(colored_text("[HUGENOTE]:", "blue"), "Fetching legislative election data from data.gouv.fr...")
        first_round_df, second_round_df = get_data_from_gouv("test", type_input, year_input)

        # ASK FOR ROUND
        # while True:
        #     turn_input = hugenote_prompt("Which turn are you looking for? (1 or 2)")
        #     if turn_input in ['1', '2']:
        #         break
        #     else:
        #         print(colored_text("[HUGENOTE]:", "red"), "Invalid round number. Please enter 1 or 2.")

        # ASK FOR DEPARTEMENT AND DISTRICT
        while True:
            try:
                departement_input = hugenote_prompt("Which department? (example: 75, 01, 971)")
                if not departement_input:
                    print(colored_text("[HUGENOTE]:", "red"), "Department number cannot be empty.")
                    continue
                
                if not (departement_input.isdigit() or (departement_input.startswith('0') and departement_input[1:].isdigit())):
                    print(colored_text("[HUGENOTE]:", "red"), "Department must be a number.")
                    continue
                    
                district_input = hugenote_prompt("Which district? (example: 1, 3, 11)")
                if not district_input:
                    print(colored_text("[HUGENOTE]:", "red"), "District number cannot be empty.")
                    continue
                    
                if not district_input.isdigit():
                    print(colored_text("[HUGENOTE]:", "red"), "District must be a number.")
                    continue
                
                break
            except Exception as e:
                print(colored_text("[HUGENOTE]:", "red"), f"Input error: {e}. Please try again.")

        print(colored_text("[HUGENOTE]:", "blue"), "Processing results...")
        print(colored_text(f"\nRESULTS FOR {departement_input}, DISTRICT {district_input}, YEAR {year_input} ", "green"))
        print(colored_text("\nFIRST ROUND DETAILS", "yellow"))
        display_round_data(departement_input, district_input, first_round_df)
        print(colored_text("\nSECOND ROUND DETAILS", "yellow"))
        display_round_data(departement_input, district_input, second_round_df)

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
                handle_legi_input()
                break
            else:
                print(colored_text("[HUGENOTE]:", "red"), "Sorry, only 'legi' (legislative elections) is currently supported.")
            
    except KeyboardInterrupt:
        print(f"\n{colored_text('[HUGENOTE]:', 'green')} Program terminated by user.")
        sys.exit(0)
    except Exception as e:
        print(colored_text("[HUGENOTE]:", "red"), f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    main()