import matplotlib.pyplot as plt
import numpy as np
from utils import colored_text

# def create_single_results_chart(election_data):

#     # EXTRACT DATA FROM FILTERED DATAFRAME
#     party_results = election_data['party_results']
#     # List of political party name
#     parties = [r['display_name'] for r in party_results]
#     # List of votes by political party
#     votes = [r['votes'] for r in party_results]

#     # LIMIT POLITICAL PARTY DISPLAY
#     if len(parties) > 10:
#         parties = parties[:10]
#         votes = votes[:10]

#     # CREATE CHART
#     # Create canva
#     fig, ax = plt.subplots(figsize=(10, 6))
#     # Create x_axis(label, length, color)
#     bars = ax.bar(parties, votes, color='orange')
#     # Create y_axis
#     # ax.invert_yaxis()
#     ax.set_ylabel("Votes")
#     ax.set_title("Election Results by Party")
#     ax.set_xticklabels(parties, rotation=45, ha="right")

#     # CREATE LABEL
#     for bar in bars:
#         # Number of vote length
#         width = bar.get_width()
#         ax.text(width + 100, bar.get_y() + bar.get_height()/2,
#                 f"{width:,}", va='center')

#     # No overlapping
#     plt.tight_layout()

#     plt.show()


#change the function to be more readable by lifting a bit the graph
def create_single_results_chart(election_data):

    # EXTRACT DATA FROM FILTERED DATAFRAME
    party_results = election_data['party_results']
    # List of political party name
    parties = [r['display_name'] for r in party_results]
    # List of votes by political party
    votes = [r['votes'] for r in party_results]

    # LIMIT POLITICAL PARTY DISPLAY
    if len(parties) > 10:
        parties = parties[:10]
        votes = votes[:10]

    # CREATE CHART
    # Create canvas
    fig, ax = plt.subplots(figsize=(10, 6))
    # Create x_axis(label, length, color)
    bars = ax.bar(parties, votes, color='orange')
    # Create y_axis
    ax.set_ylabel("Votes")
    ax.set_title("Election Results by Party")
    ax.set_xticklabels(parties, rotation=45, ha="right")

    # CREATE LABEL - Fixed positioning
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2, height + (max(votes) * 0.01),
                f"{int(height):,}", ha='center', va='bottom')

    # Ensure enough vertical space for labels
    y_max = max(votes) * 1.1  # Add 10% padding at the top
    ax.set_ylim(0, y_max)

    # No overlapping
    plt.tight_layout()

    plt.show()



def add_labels(ax, bars):
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 100,
                f'{height:,}', ha='center', va='bottom')


#change the function so it only take the candidat who reached 2nd round and ajust color to green for the best results
def create_group_results_chart_V2(round1_data, round2_data):
    #PROCESS SECOND ROUND TO LOCATE SECOND ROUND CANDIDAT
    round2_candidats = round2_data.get("party_results")
    if not round2_candidats:
        raise Exception("unable to find 2nd round candidats")

    round1_candidats = round1_data.get("party_results")
    if not round1_candidats:
        raise Exception("unable to find 1nd round candidats")

    for round2_candidat in round2_candidats:
        for round1_candidat in round1_candidats:
            if round1_candidat.get("display_name") and round1_candidat.get("display_name") == round2_candidat.get("display_name"):
                round2_candidat["round1_votes"] = round1_candidat.get("votes")
                break

    labels = [p['display_name'] for p in round2_candidats]
    round1_votes = [p['round1_votes'] for p in round2_candidats]
    round2_votes = [p['votes'] for p in round2_candidats]
    colors_r1 = list()
    colors_r2 = list()
    for i in range(len(round2_votes)):
        if int(round1_votes[i]) < (round2_votes[i]):
            colors_r1.append('red')
            colors_r2.append('green')
        else:
            colors_r2.append('red')
            colors_r1.append('green')

    # print(colors_r1)
    # print(colors_r2)
    # CREATE CHART
    # Bar volume
    x = np.arange(len(labels))
    # Bar lentgh
    width = 0.35
    # Create canva
    fig, ax = plt.subplots(figsize=(12, 8))
    # Get bar color
    # if (round1_votes > round2_votes):
    #     r1_color = 'green'
    #     r2_color = 'red'
    # else:
    #     r1_color = 'red'
    #     r2_color = 'green'
    rects1 = ax.bar(x - width/2, round1_votes, width, label='First Round', color=colors_r1[:len(round1_votes)])
    rects2 = ax.bar(x + width/2, round2_votes, width, label='Second Round', color=colors_r2[:len(round2_votes)])

    # Add labels
    ax.set_ylabel('Votes')
    ax.set_title('Comparison of Election Results: First vs Second Round')
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=45, ha='right')
    ax.legend()
    add_labels(ax, rects1)
    add_labels(ax, rects2)

    fig.tight_layout()

    plt.show()


def create_group_results_chart(round1_data, round2_data):

    # UNIFIED LIST OF POLITICAL PARTY
    all_parties = {}

    # PROCESS FIRST ROUND
    for party in round1_data['party_results']:
        # Where party is an identifying key
        party_key = party['party']
        all_parties[party_key] = {
            'display_name': party['display_name'],
            'round1_votes': party['votes'],
            'round2_votes': 0
        }

    # PROCESS SECOND ROUND
    for party in round2_data['party_results']:
        party_key = party['party']
        if party_key in all_parties:
            all_parties[party_key]['round2_votes'] = party['votes']
        else:
            # In case of list fusion (update for 2017 and 2024 election)
            all_parties[party_key] = {
                'display_name': party['display_name'],
                'round1_votes': 0,
                'round2_votes': party['votes']
            }

    # CONVERT THEN SORT
    parties_list = list(all_parties.values())
    parties_list.sort(key=lambda x: x['round1_votes'] + x['round2_votes'], reverse=True)

    # LIMIT DISPLAY
    if len(parties_list) > 6:
        parties_list = parties_list[:6]

    # EXTRACT DATA
    labels = [p['display_name'] for p in parties_list]
    round1_votes = [p['round1_votes'] for p in parties_list]
    round2_votes = [p['round2_votes'] for p in parties_list]

    # CREATE CHART
    # Bar volume
    x = np.arange(len(labels))
    # Bar lentgh
    width = 0.35
    # Create canva
    fig, ax = plt.subplots(figsize=(12, 8))
    # Get bar color
    if (round1_votes > round2_votes):
        r1_color = 'green'
        r2_color = 'red'
    else:
        r1_color = 'red'
        r2_color = 'green'
    rects1 = ax.bar(x - width/2, round1_votes, width, label='First Round', color=r1_color)
    rects2 = ax.bar(x + width/2, round2_votes, width, label='Second Round', color=r2_color)

    # Add labels
    ax.set_ylabel('Votes')
    ax.set_title('Comparison of Election Results: First vs Second Round')
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=45, ha='right')
    ax.legend()
    add_labels(ax, rects1)
    add_labels(ax, rects2)

    # PROGRESSION
    # for i, party in enumerate(parties_list):
    #     if party['round1_votes'] > 0 and party['round2_votes'] > 0:
    #         pct_change = ((party['round2_votes'] - party['round1_votes']) / party['round1_votes']) * 100
    #         if abs(pct_change) > 5:
    #             color = 'black'
    #             ax.text(x[i],
    #                    max(party['round1_votes'], party['round2_votes']),
    #                    f"{pct_change:+.1f}%",
    #                    color=color,
    #                    fontweight='bold',
    #                    ha='center')

    # Tight layout to prevent label cutoff
    fig.tight_layout()

    plt.show()

def create_turnout_comparison_chart(round1_data, round2_data):

    # EXTRACT PARTICIPATION DATA
    r1_participation = round1_data['participation']
    r2_participation = round2_data['participation']

    # PREPARE DATA CATEGORIES (removed "Registered" as it's always 100%)
    categories = ['Voters', 'Abstention', 'Blank/Void', 'Valid Votes']

    # CALCULATE PERCENTAGES
    r1_pct = [
        r1_participation['turnout_pct'],
        r1_participation['abstention_pct'],
        r1_participation['blank_void_pct'],
        r1_participation['valid_votes_pct']
    ]

    r2_pct = [
        r2_participation['turnout_pct'],
        r2_participation['abstention_pct'],
        r2_participation['blank_void_pct'],
        r2_participation['valid_votes_pct']
    ]

    # DETERMINE COLORS BASED ON WHICH VALUE IS BETTER FOR EACH CATEGORY
    # For Voters and Valid Votes: higher is better (green)
    # For Abstention and Blank/Void: lower is better (green)
    better_if_higher = [True, False, False, True]  # Corresponds to categories order

    r1_colors = []
    r2_colors = []

    for i, (val1, val2, higher_is_better) in enumerate(zip(r1_pct, r2_pct, better_if_higher)):
        if higher_is_better:
            # For metrics where higher is better
            r1_colors.append('green' if val1 > val2 else 'red')
            r2_colors.append('green' if val2 > val1 else 'red')
        else:
            # For metrics where lower is better
            r1_colors.append('green' if val1 < val2 else 'red')
            r2_colors.append('green' if val2 < val1 else 'red')

        # If they're equal, both will be green
        if abs(val1 - val2) < 0.1:  # Small threshold for equality
            r1_colors[i] = 'green'
            r2_colors[i] = 'green'

    # CREATE FIGURE (SINGLE PANEL FOR PERCENTAGES ONLY)
    fig, ax = plt.subplots(figsize=(12, 7))

    # SETUP BAR POSITIONS
    x = np.arange(len(categories))
    width = 0.35

    # CREATE CHART WITH DYNAMIC COLORS
    bars1 = []
    bars2 = []

    # Create bars with individual colors
    for i in range(len(categories)):
        bars1.append(ax.bar(x[i] - width/2, r1_pct[i], width, color=r1_colors[i]))
        bars2.append(ax.bar(x[i] + width/2, r2_pct[i], width, color=r2_colors[i]))

    # CHART
    ax.set_ylabel('Percentage of Registered Voters')
    ax.set_title('Voter Participation Comparison Between Election Rounds')
    ax.set_xticks(x)
    ax.set_xticklabels(categories)
    ax.set_ylim(0, 105)

    # LABELS
    for i in range(len(categories)):
        # First round
        height = r1_pct[i]
        ax.text(x[i] - width/2, height + 2,
               f'{height:.1f}%',
               ha='center', va='bottom',
               fontsize=9)

        # Second round
        height = r2_pct[i]
        ax.text(x[i] + width/2, height + 2,
               f'{height:.1f}%',
               ha='center', va='bottom',
               fontsize=9)

    # INDICATORS
    for i in range(len(categories)):
        pct_change = r2_pct[i] - r1_pct[i]
        if abs(pct_change) > 1.0:
            direction = '▲' if pct_change > 0 else '▼'
            is_improvement = (pct_change > 0 and better_if_higher[i]) or (pct_change < 0 and not better_if_higher[i])
            color = 'green' if is_improvement else 'red'

            ax.text(x[i],
                   max(r1_pct[i], r2_pct[i]) + 5,
                   f"{direction} {abs(pct_change):.1f}%",
                   color=color,
                   fontweight='bold',
                   ha='center')

    # GRIDTY
    ax.grid(axis='y', linestyle='--', alpha=0.3)

    # LAYOUT
    plt.tight_layout()

    # TITLE
    fig.suptitle(f'Participation Comparison: {round1_data["participation"]["registered"]:,} Registered Voters', fontsize=16)
    plt.subplots_adjust(top=0.9)

    plt.show()
