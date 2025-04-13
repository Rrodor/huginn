from get_data_gouv import get_data_from_gouv
from Candidat import Candidat
from utils import colored_text, hugenote_prompt
from charts import create_single_results_chart, create_group_results_chart, create_turnout_comparison_chart
import pandas as pd
import shutil
import load_csv
import os
import sys

#===========================================================#
#                AESTHETIC DISPLAY                          #
#===========================================================#

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
    print("from the French legislative elections between 1958 and 2012.")
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


def process_election_data(departement_code, district_code, dataframe):
    
    # RESULT STRUCTURE
    result = {
        'found': False,
        'participation': {
            'registered': 0,
            'voters': 0,
            'valid_votes': 0,
            'blank_void': 0,
            'turnout_pct': 0,
            'abstention_pct': 0,
            'blank_void_pct': 0,
            'valid_votes_pct': 0
        },
        'party_results': [],
        'metadata': {
            'is_1981_format': False
        }
    }
    
    try:
        # FILTER
        district_nb = int(district_code)
        departement_nb = int(departement_code)
        filtered_df = None
        
        # CHECK COMPATIBILITY
        filter_attempts = [
            lambda df: df[(df['Code département'] == departement_nb) & (df['circonscription'] == district_nb)],
            lambda df: df[(df['Code département'] == str(departement_nb)) & (df['circonscription'] == str(district_nb))],
            lambda df: df[(df['Code département'] == str(departement_nb)) & (df['circonscription'] == district_nb)],
            lambda df: df[(df['Code département'] == departement_nb) & (df['circonscription'] == str(district_nb))]]
        
        for filter_attempt in filter_attempts:
            try:
                filtered_result = filter_attempt(dataframe)
                if not filtered_result.empty:
                    filtered_df = filtered_result
                    break
            except Exception:
                continue
        
        # STATE
        if filtered_df is None or filtered_df.empty:
            return result
        result['found'] = True
        
        # DISTRICT ROW
        row = filtered_df.iloc[0]
        
        # DETERMINE FORMAT 'BEFORE 1981' OR 'AFTER 1981'
        result['metadata']['is_1981_format'] = any('1 voix' in col for col in filtered_df.columns)
        
        # GET REMAINING STATISTICS
        total_registered = get_value_from_df(row, 'Inscrits')
        total_voters = get_value_from_df(row, 'Votants')
        valid_votes = get_value_from_df(row, 'Exprimés')
        
        # OPTIONNAL : WHITE / CANCELED VOTES
        possible_blank_columns = ['Blancs et nuls', 'Blancs', 'Nuls']
        blank_void = 0
        for col in possible_blank_columns:
            if col in row:
                blank_void = get_value_from_df(row, col)
                break
        
        # GET CUSTOM PERCENTAGES
        turnout_pct = (total_voters / total_registered * 100) if total_registered > 0 else 0
        abstention_pct = 100 - turnout_pct
        blank_void_pct = (blank_void / total_voters * 100) if total_voters > 0 else 0
        valid_votes_pct = (valid_votes / total_voters * 100) if total_voters > 0 else 0
        
        # PARTICIPATION STRUCTURE
        result['participation'] = {
            'registered': int(total_registered),
            'voters': int(total_voters),
            'valid_votes': int(valid_votes),
            'blank_void': int(blank_void),
            'turnout_pct': turnout_pct,
            'abstention_pct': abstention_pct,
            'blank_void_pct': blank_void_pct,
            'valid_votes_pct': valid_votes_pct}
        
        # EXCLUDE TO PROCESS ONLY PARTY RESULT
        always_excluded = [
            'Code département', 'département', 'circonscription',
            'élu premier tour', 'Inscrits', 'Votants', 'Exprimés', 
            'Blancs et nuls', 'Blancs', 'Nuls', '']
        excluded_columns = set()
        for col in always_excluded:
            if col in filtered_df.columns:
                excluded_columns.add(col)
        
        party_results = []
        
        # PROCESS RESULT DEPENDING ON CSV FORMAT (1958 OR 1981)
        if result['metadata']['is_1981_format']:
            # POST 1981
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
                            'party': party,
                            'display_name': f"{party} - {candidate_name}",
                            'candidate_name': candidate_name,
                            'votes': int(votes),
                            'percentage': percentage
                        })
                except (ValueError, TypeError, KeyError):
                    pass

                candidate_num += 1
        else:
            # ANTE 1981
            for column in filtered_df.columns:
                if column not in excluded_columns:
                    try:
                        value = pd.to_numeric(row[column], errors='coerce')
                        if pd.notna(value) and value > 0:
                            score = int(value)
                            percentage = (score / valid_votes * 100) if valid_votes > 0 else 0
                            party_results.append({
                                'party': column,
                                'display_name': column,
                                'candidate_name': "",
                                'votes': score,
                                'percentage': percentage
                            })
                    except (ValueError, TypeError):
                        pass
        
        # SORT VOTES
        party_results.sort(key=lambda x: x['votes'], reverse=True)
        result['party_results'] = party_results
        
        # Get election status if available
        # if 'élu premier tour' in row:
        #     status_value = get_value_from_df(row, 'élu premier tour')
        #     elected_first_round = None
            
        #     if status_value in ['O', 'OUI', 'Y', 'YES', True, 1]:
        #         elected_first_round = True
        #     elif status_value in ['N', 'NON', 'N', 'NO', False, 0]:
        #         elected_first_round = False
                
        #     result['metadata']['elected_first_round'] = elected_first_round
            
    except Exception as e:
        result['metadata']['error'] = str(e)
        
    return result

def display_round_data(departement_code, district_code, current_dataframe):
    
    # FILTER DATA
    result = process_election_data(departement_code, district_code, current_dataframe)
    if not result['found']:
        print(colored_text("[HUGENOTE]:", "red"), 
              f"No results found for: departement({departement_code}), district({district_code}).")
        return result
    
    # DISPLAY STATISTICS
    participation = result['participation']
    print("-" * 50)
    print(colored_text("\nELECTION PARTICIPATION:", "green"))
    print("-" * 50)
    print(f"Registered voters:    {participation['registered']:,}")
    print(f"Turnout:              {participation['voters']:,} ({participation['turnout_pct']:.1f}%)")
    print(f"Abstention:           {participation['registered'] - participation['voters']:,} ({participation['abstention_pct']:.1f}%)")
    print(f"Blank/void ballots:   {participation['blank_void']:,} ({participation['blank_void_pct']:.1f}%)")
    print(f"Valid votes:          {participation['valid_votes']:,} ({participation['valid_votes_pct']:.1f}%)")
    print("-" * 50)
    
    # DISPLAY POLITICAL PARTY RESULTS
    print(colored_text("POLITICAL PARTY RESULTS", "green"))
    print("-" * 50)
    party_results = result['party_results']
    if not party_results:
        print("No party result data available in this dataset.")
    else:
        for i, party in enumerate(party_results):
            if i == 0:
                print(f"{party['display_name']:<25}: {party['votes']:,} votes ({party['percentage']:.1f}%) - LEADING")
            else:
                print(f"{party['display_name']:<25}: {party['votes']:,} votes ({party['percentage']:.1f}%)")
    
    print("-" * 50)
        
    return result

#===========================================================#
#                ELECTION MANAGER                           #
#===========================================================#

def handle_legi_input():
    try:

        # ASK FOR YEAR (TO UPDATE AND IMPROVE)
        # Handle the election between 1958 and 2012.
        # Let the user choose any year, if it's not matching any election date, ask him for the closest next/previous election.
        while True:
            year_input = hugenote_prompt("Which year are you looking for? (For this version, only date between 1958 and 2012 are supported)")
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
                departement_input = hugenote_prompt("Which department? (example: 75, 01, 66)")
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
        print(colored_text(f"\nRESULTS FOR DEPARTEMENT ({departement_input}) | DISTRICT ({district_input}) | YEAR ({year_input}) ", "green"))
        print(colored_text("\nFIRST ROUND DETAILS", "yellow"))
        filtered_data_turn1 = display_round_data(departement_input, district_input, first_round_df)
        print(colored_text("\nSECOND ROUND DETAILS", "yellow"))
        filtered_data_turn2 = display_round_data(departement_input, district_input, second_round_df)
        if not filtered_data_turn1['found'] or not filtered_data_turn2['found']:
            print(colored_text("[HUGENOTE]:", "red"), "Data for one or both rounds not found. Exiting program.")
            sys.exit(1) 

        while True:
            print()
            visual_input = hugenote_prompt("Available views : \n[1] Single turn result chart \n[2] Compare results between rounds \n[3] Compare turnout statistic")
            if not (visual_input.isdigit() and visual_input in ['1', '2', '3']):
                print(colored_text("[HUGENOTE]:", "red"), "You must choose between option 1, 2 and 3.")
                continue
            if visual_input == '1':
                round_choice = hugenote_prompt("Which round? (1, 2, both)")
                if round_choice == '1':
                    create_results_chart(filtered_data_turn1)
                    break
                elif round_choice == '2':
                    create_results_chart(filtered_data_turn2)
                    break
                else:
                    print(colored_text("[HUGENOTE]:", "red"), "Invalid round selection.")
                    continue
            if visual_input == '2':
                create_group_results_chart(filtered_data_turn1, filtered_data_turn2)
                break
            if visual_input == '3':
                create_turnout_comparison_chart(filtered_data_turn1, filtered_data_turn2)
                break
            
    except Exception as e:
        print(colored_text("\n[HUGENOTE]:", "red"), f"Error processing legislative election data: {e}")

#===========================================================#
#                MAIN                                       #
#===========================================================#

def erase_data():
    data_dir = "hugenote_data"
    if os.path.exists(data_dir):
        shutil.rmtree(data_dir)
    os.makedirs(data_dir, exist_ok=True)

def main():
    try:
        # DISPLAY HEADER AN INTRODUCTION
        display_header()
        
        # REMOVE PREVIOUS DATA
        erase_data()

        # ASK FOR ELECTION TYPE
        while True:
            election_type = hugenote_prompt("Which election type do you want to look at? (For this version, only 'parliament' is available)")
            # PARLIAMENT ELECTION PATH
            if election_type.lower() == 'parliament':
                handle_legi_input()
                break
            else:
                print(colored_text("[HUGENOTE]:", "red"), "Sorry, only 'parliament' is currently supported.")
            
    except KeyboardInterrupt:
        print(f"\n{colored_text('[HUGENOTE]:', 'green')} Program terminated by user.")
        erase_data()
        sys.exit(0)
    except Exception as e:
        print(colored_text("[HUGENOTE]:", "red"), f"An unexpected error occurred: {e}")
        erase_data()


if __name__ == "__main__":
    main()