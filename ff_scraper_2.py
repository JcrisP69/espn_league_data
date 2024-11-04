import requests
import pandas as pd
from ff_data import cookies
import ff_data
import os


def scraper(id, kind = "Draft", year = 2024, week = 0):
        """
        This function determines which api calls to make and exports the results in one csv named accordingly

        id (int): id of the league for requests specific to a league
        kind (str): What type of data is to be retreived
        year (int): year of interest for the request
        week (int): week of interest for the request (0 if the request is yearly)

        Prints:
        str: confirming the output name and location
        """
        

        # Get the directory of the current script
        output_file_name = "ff_output"
        current_directory = os.path.dirname(os.path.abspath(__file__))

        # Define the name of the subfolder where you want to save the file
        output_folder = os.path.join(current_directory, output_file_name)

        # Create the output folder if it doesn't exist
        os.makedirs(output_folder, exist_ok=True)

        match kind:
                case "Draft":
                        draft_df = getdraft(id, year)
                        player_df = getplayers(year)
                        team_df = getteams(year)

                        draft_df = pd.merge(draft_df, player_df, how = "inner", on = "player_id")
                        draft_df = pd.merge(draft_df, team_df, how = "inner", on = "team_id")
                        final_df = draft_df[['bidAmount', 'team_id', 'defaultPositionId', 'fullName', 'team name', 'player_id']]
                        final_df = final_df.replace({"defaultPositionId": ff_data.position_mapping})
                        final_df = final_df.replace({"team_id": ff_data.team_mapping})

                        file_name = f"draft_{year}"
                        final_df.to_csv(os.path.join(output_folder, f'{file_name}.csv'), index=False)


                case "Weekly Matchup":
                        getplmatchup_df = getplmatchup(id, year, week)
                        getplmatchup_df = getplmatchup_df.replace({"slot": ff_data.lineup_slot_mapping}, {"team_id": ff_data.team_mapping})

                        if week == 0:
                                file_name = f"matchup_{year}"
                                getplmatchup_df.to_csv(os.path.join(output_folder, f'{file_name}.csv'), index=False)
                        else:
                                file_name = f"matchup_{year}_{week}"
                                getplmatchup_df.to_csv(os.path.join(output_folder, f'{file_name}.csv'), index=False)


        print(f"Data has been written to {file_name} in {output_file_name}")
                


def getdraft(id, year):
        # Draft info url
        url = f"https://lm-api-reads.fantasy.espn.com/apis/v3/games/ffl/seasons/{year}/segments/0/leagues/{id}?view=mDraftDetail&view=mSettings&view=mTeam&view=modular&view=mNav"
        headers = {"Connection": "keep-alive", "Accept": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:130.0) Gecko/20100101 Firefox/130.0",}

        # Calling the espn api and reading the JSON
        jframe = requests.get(url, headers = headers, cookies = cookies)
        jframe = jframe.json()

        jframe = jframe['draftDetail']['picks']

        # Only keeping the data that is relevant and creating a pandas dataframe that will later be
        # joined by other data
        pframe = pd.DataFrame(jframe)

        pframe.rename(columns = {"playerId": "player_id", "teamId": "league_id"}, inplace = True)
        pframe = pframe[['bidAmount', 'player_id', 'league_id']]

        return pframe

def getplayers(year):
        # Draft info url
        url = f"https://lm-api-reads.fantasy.espn.com/apis/v3/games/ffl/seasons/{year}/players?scoringPeriodId=0&view=players_wl"
        headers = {"Connection": "keep-alive", "Accept": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:130.0) Gecko/20100101 Firefox/130.0",
        "X-Fantasy-Filter":"{\"filterActive\":null}", "X-Fantasy-Platform": "kona-PROD-652b677c73811482e562046ffeb891262541819e",
        "X-Fantasy-Source": "kona",
        }

        # Calling the espn api and reading the JSON
        jframe = requests.get(url, headers = headers, cookies = cookies)
        jframe = jframe.json()

        pframe = pd.DataFrame(jframe)

        pframe.rename(columns = {"id": "player_id", "proTeamId": "team_id"}, inplace = True)
        pframe = pframe[['defaultPositionId', 'fullName', 'player_id', 'team_id']]
        

        return pframe

def getteams(year):
        url = f"https://lm-api-reads.fantasy.espn.com/apis/v3/games/ffl/seasons/{year}?view=proTeamSchedules_wl"
        headers = {"Connection": "keep-alive", "Accept": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:130.0) Gecko/20100101 Firefox/130.0",
        }

        # Calling the espn api and reading the JSON
        jframe = requests.get(url, headers = headers, cookies = cookies)
        jframe = jframe.json()
        jframe = jframe['settings']['proTeams']

        pframe = pd.DataFrame(jframe)

        pframe = pframe[["id", "location", "name"]]
        pframe["team name"] = pframe["location"].astype(str) +" "+ pframe["name"]
        # rename in column
        pframe.rename(columns = {"id":"team_id"}, inplace = True)

        return pframe

def getplmatchup_week(id, year, week):
        url = f"https://lm-api-reads.fantasy.espn.com/apis/v3/games/ffl/seasons/{year}/segments/0/leagues/{id}?scoringPeriodId={week}&view=mBoxscore&view=mMatchupScore&view=mRoster&view=mSettings&view=mStatus&view=mTeam&view=modular&view=mNav"
        headers = {"Connection": "keep-alive", "Accept": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:130.0) Gecko/20100101 Firefox/130.0",
        }

        # Calling the ESPN API and reading the JSON
        jframe = requests.get(url, headers=headers, cookies=cookies)
        jframe = jframe.json()

        pdflist = []
        matchups = ff_data.matchup_key[week]
        team = ["home", "away"]

        for x in team:
                for n in matchups:

                        teamref = jframe['schedule'][n][x]

                        teamref = pd.json_normalize(teamref)

                        teamref = teamref[["teamId"]]

                        ljframe = jframe['schedule'][n][x]['rosterForCurrentScoringPeriod']['entries']

                        lpframe = pd.json_normalize(ljframe)

                        lpframe = lpframe.assign(source = n)

                        lpframe = lpframe.assign(team = x)

                        lpframe = lpframe.assign(league_id = teamref)

                        pdflist.append(lpframe)


        result = pd.concat(pdflist, axis=0, ignore_index=True)

        result.rename(columns = {"lineupSlotId":"slot", 
                                 'playerPoolEntry.appliedStatTotal':'fpts', 
                                 'playerPoolEntry.player.eligibleSlots': 'potslot',
                                 'playerPoolEntry.player.proTeamId':'team_id'}, inplace = True)

        result = result[['slot', 'playerId', 'fpts', 'potslot', 'team_id', 'source', 'team', 'league_id']]

        return result

def getplmatchup(id, year, week = 0):
        if week != 0:
                return getplmatchup_week(id, year, week)
        
        else:
                match year: 
                        case 2022:
                                spread = list(range(1, 16))
                        case 2023:
                                spread = list(range(1, 15))
                        case 2024:
                                spread = list(range(1, 6))
        
                result = []

                for n in spread:
                        result.append(getplmatchup_week(id, year, n))
                results = pd.concat(result, axis=0, ignore_index=True)
                return results

# Example calls :
# scraper("Draft", 26554663, 2024)
# scraper("Weekly Matchup", 2164657, 2024)