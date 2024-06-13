#database import all player match level stats per league per season
import soccerdata as sd
from soccerdata import FBref 
from datetime import datetime
import pandas as pd
import psycopg2
import sys
import traceback
import requests
import os 
import io
from io import StringIO
import csv #temp csv step in memory step
import time
import random
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

##poetry run python ARGteamMatchstatstest.py

#2122 not found/broken
start_time = time.time()
# Define the proxy list
PROXIES = [
'67.43.236.20:1451',
    '72.10.160.92:16631',
    '72.10.160.172:32387',
    '67.43.236.20:21547',
    '67.43.236.20:27595',
    '67.43.236.20:9929',
    '171.6.160.105:8080',
    '72.10.160.91:2411',
    '72.10.160.94:11617',
    '114.231.46.103:8888',

]

# Define the user-agent list
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:54.0) Gecko/20100101 Firefox/54.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/12.1.2 Safari/605.1.15",
    # Add more user agents as needed
]

url = 'https://fbref.com/en/comps/'


# Function to create a session with retry strategy
def create_session():
    session = requests.Session()
    retries = Retry(total=5, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
    session.mount('http://', HTTPAdapter(max_retries=retries))
    session.mount('https://', HTTPAdapter(max_retries=retries))
    return session

# Function to make a request using rotating proxies and user agents
def fetch_url(url, retries=5):
    session = create_session()
    for _ in range(retries):
        proxy = random.choice(PROXIES)
        user_agent = random.choice(USER_AGENTS)
        headers = {"User-Agent": user_agent}
        try:
            response = session.get(url, headers=headers, proxies={"http": proxy, "https": proxy}, timeout=10)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            print(f"Request failed with proxy {proxy}: {e}")
            time.sleep(random.uniform(1, 5))  # Add random delay to mimic human behavior
    return None

response = fetch_url(url)
if response:
    print("Successfully fetched data")
    print(response.text)  # Process the response as needed
else:
    print("Failed to fetch data")

#pick sample league and season to create tables to base chart off of
ARGstats = sd.FBref(leagues="ARG-ArgentinePrimeraDivisión", seasons='2324')

#player misc stats
ARGteamMatchMisc = ARGstats.read_team_match_stats(stat_type="misc")

# Reset the index to turn multi-index into columns
ARGteamMatchMisc.reset_index(inplace=True)

# Check if the columns are a MultiIndex
if isinstance(ARGteamMatchMisc.columns, pd.MultiIndex):
    # Flatten the multi-level column headers
    ARGteamMatchMisc.columns = [''.join(map(str, col)).strip() for col in ARGteamMatchMisc.columns]

prefix_tm = 'tm'
conditions = ['Performance', 'G', 'Poss', 'Attendance', 'Captain', 'Formation', 'Referee', 'Touches', 
                 'Take', 'Carries', 'Receiving', 'Tackles', 'Challenges', 'Blocks', 'Int', 'Tkl', 'Clr', 'Err', 'Total',
                 'Short', 'Medium', 'Long', 'Ast', 'xA', 'KP', '1/3', 'PPA', 'CrsPA', 'Prg', 'Pass',
                 'Corner', 'Outcomes', 'SCA', 'Standard', 'Expected']

prefix_tkm = 'tkm'
conditions_tkm = ['PerformanceSoTA', 'PerformanceGA', 'PerformanceSaves', 'PerformanceCS', 'PerformancePSxG', 'Penalty Kicks',
                  'LaunchedCmppc', 'PassesAtt', 'PassesThr', 'PassesLaunch', 'Goal', 'Crosses', 'Sweeper']

def add_prefix_to_columns(columns, prefix, conditions):
    new_columns = []
    for col in columns:
        if any(col.startswith(word) for word in conditions):
            new_columns.append(prefix + col)
        else:
            new_columns.append(col)
    return new_columns

def add_tkmprefix_to_columns(columns, prefix_tkm, conditions):
    new_columns = []
    for col in columns:
        if any(col.startswith(word) for word in conditions):
            new_columns.append(prefix_tm + col)
        else:
            new_columns.append(col)
    return new_columns

ARGteamMatchMisc.columns = add_prefix_to_columns(ARGteamMatchMisc.columns, prefix_tm, conditions)

ARGteamMatchMisc = ARGteamMatchMisc.rename(columns={'matchPerformanceAerial DuelsWon%': 'matchPerformanceAerial DuelsWonpc'})

# Identify numeric columns
numeric_columns = ARGteamMatchMisc.select_dtypes(include=['number']).columns

# Identify string columns
string_columns = ARGteamMatchMisc.select_dtypes(include=['object', 'string']).columns

# Replace NaN with 0 in numeric columns
ARGteamMatchMisc[numeric_columns] = ARGteamMatchMisc[numeric_columns].fillna(0)

# Replace NaN with UNK in string columns
ARGteamMatchMisc[string_columns] = ARGteamMatchMisc[string_columns].fillna('UNK')

# Ensure the data types are correct for numeric columns
ARGteamMatchMisc[numeric_columns] = ARGteamMatchMisc[numeric_columns].astype(float)

print("Actual columns in ARGteamMatchMisc:")
print(ARGteamMatchMisc.columns.tolist())

#possession match stats
ARGteamMatchPossesion = ARGstats.read_team_match_stats(stat_type="possession")

# Reset the index to turn multi-index into columns
ARGteamMatchPossesion.reset_index(inplace=True)


# Check if the columns are a MultiIndex
if isinstance(ARGteamMatchPossesion.columns, pd.MultiIndex):
    # Flatten the multi-level column headers
    ARGteamMatchPossesion.columns = [''.join(map(str, col)).strip() for col in ARGteamMatchPossesion.columns]

ARGteamMatchPossesion.columns = add_prefix_to_columns(ARGteamMatchPossesion.columns, prefix_tm, conditions)
ARGteamMatchPossesion = ARGteamMatchPossesion.rename(columns={'matchTakeOnsSucc%': 'matchTakeOnsSuccpc'})
ARGteamMatchPossesion = ARGteamMatchPossesion.rename(columns={'matchTakeOnsTkld%': 'matchTake-OnsTkldpc'})

# Identify numeric columns
numeric_columns = ARGteamMatchPossesion.select_dtypes(include=['number']).columns

# Identify string columns
string_columns = ARGteamMatchPossesion.select_dtypes(include=['object', 'string']).columns

# Replace NaN with 0 in numeric columns
ARGteamMatchPossesion[numeric_columns] = ARGteamMatchPossesion[numeric_columns].fillna(0)

# Replace NaN with UNK in string columns
ARGteamMatchPossesion[string_columns] = ARGteamMatchPossesion[string_columns].fillna('UNK')

# Ensure the data types are correct for numeric columns
ARGteamMatchPossesion[numeric_columns] = ARGteamMatchPossesion[numeric_columns].astype(float)

print("Actual columns in ARGteamMatchPossesion:")
print(ARGteamMatchPossesion.columns.tolist())

#schedule team match stats
ARGteamSchedule = ARGstats.read_team_match_stats(stat_type="schedule")

# Reset the index to turn multi-index into columns
ARGteamSchedule.reset_index(inplace=True)

# Check if the columns are a MultiIndex
if isinstance(ARGteamSchedule.columns, pd.MultiIndex):
    # Flatten the multi-level column headers
    ARGteamSchedule.columns = [''.join(map(str, col)).strip() for col in ARGteamSchedule.columns]
ARGteamSchedule.columns = add_prefix_to_columns(ARGteamSchedule.columns, prefix_tm, conditions)

# Identify numeric columns
numeric_columns = ARGteamSchedule.select_dtypes(include=['number']).columns

# Identify string columns
string_columns = ARGteamSchedule.select_dtypes(include=['object', 'string']).columns

# Replace NaN with 0 in numeric columns
ARGteamSchedule[numeric_columns] = ARGteamSchedule[numeric_columns].fillna(0)

# Replace NaN with UNK in string columns
ARGteamSchedule[string_columns] = ARGteamSchedule[string_columns].fillna('UNK')

print("Actual columns in ARGteamSchedule:")
print(ARGteamSchedule.columns.tolist())

#passing match stats
ARGteamMatchDefense = ARGstats.read_team_match_stats(stat_type="passing")

# Reset the index to turn multi-index into columns
ARGteamMatchDefense.reset_index(inplace=True)

# Check if the columns are a MultiIndex
if isinstance(ARGteamMatchDefense.columns, pd.MultiIndex):
    # Flatten the multi-level column headers
    ARGteamMatchDefense.columns = [''.join(map(str, col)).strip() for col in ARGteamMatchDefense.columns]
ARGteamMatchDefense.columns = add_prefix_to_columns(ARGteamMatchDefense.columns, prefix_tm, conditions)

ARGteamMatchDefense = ARGteamMatchDefense.rename(columns={'ChallengesTkl%': 'ChallengesTklpc'})

# Identify numeric columns
numeric_columns = ARGteamMatchDefense.select_dtypes(include=['number']).columns

# Identify string columns
string_columns = ARGteamMatchDefense.select_dtypes(include=['object', 'string']).columns

# Replace NaN with 0 in numeric columns
ARGteamMatchDefense[numeric_columns] = ARGteamMatchDefense[numeric_columns].fillna(0)

# Replace NaN with UNK in string columns
ARGteamMatchDefense[string_columns] = ARGteamMatchDefense[string_columns].fillna('UNK')

# Ensure the data types are correct for numeric columns
ARGteamMatchDefense[numeric_columns] = ARGteamMatchDefense[numeric_columns].astype(float)

print("Actual columns in ARGteamMatchDefense:")
print(ARGteamMatchDefense.columns.tolist())

#passing_types match stats
ARGteamMatchGoalShotCreation = ARGstats.read_team_match_stats(stat_type="goal_shot_creation")

# Reset the index to turn multi-index into columns
ARGteamMatchGoalShotCreation.reset_index(inplace=True)

# Check if the columns are a MultiIndex
if isinstance(ARGteamMatchGoalShotCreation.columns, pd.MultiIndex):
    # Flatten the multi-level column headers
    ARGteamMatchGoalShotCreation.columns = [''.join(map(str, col)).strip() for col in ARGteamMatchGoalShotCreation.columns]
ARGteamMatchGoalShotCreation.columns = add_prefix_to_columns(ARGteamMatchGoalShotCreation.columns, prefix_tm, conditions)

# Identify numeric columns
numeric_columns = ARGteamMatchGoalShotCreation.select_dtypes(include=['number']).columns

# Identify string columns
string_columns = ARGteamMatchGoalShotCreation.select_dtypes(include=['object', 'string']).columns

# Replace NaN with 0 in numeric columns
ARGteamMatchGoalShotCreation[numeric_columns] = ARGteamMatchGoalShotCreation[numeric_columns].fillna(0)

# Replace NaN with UNK in string columns
ARGteamMatchGoalShotCreation[string_columns] = ARGteamMatchGoalShotCreation[string_columns].fillna('UNK')

# Ensure the data types are correct for numeric columns
ARGteamMatchGoalShotCreation[numeric_columns] = ARGteamMatchGoalShotCreation[numeric_columns].astype(float)

print("Actual columns in ARGteamMatchGoalShotCreation:")
print(ARGteamMatchGoalShotCreation.columns.tolist())


ARGteamMatchshooting = ARGstats.read_team_match_stats(stat_type="shooting")

# Reset the index to turn multi-index into columns
ARGteamMatchshooting.reset_index(inplace=True)

# Check if the columns are a MultiIndex
if isinstance(ARGteamMatchshooting.columns, pd.MultiIndex):
    # Flatten the multi-level column headers
    ARGteamMatchshooting.columns = [''.join(map(str, col)).strip() for col in ARGteamMatchshooting.columns]
ARGteamMatchshooting.columns = add_prefix_to_columns(ARGteamMatchshooting.columns, prefix_tm, conditions)

ARGteamMatchshooting = ARGteamMatchshooting.rename(columns={'matchStandardSoT%': 'matchStandardSoTpc'})

# Identify numeric columns
numeric_columns = ARGteamMatchshooting.select_dtypes(include=['number']).columns

# Identify string columns
string_columns = ARGteamMatchshooting.select_dtypes(include=['object', 'string']).columns

# Replace NaN with 0 in numeric columns
ARGteamMatchshooting[numeric_columns] = ARGteamMatchshooting[numeric_columns].fillna(0)

# Replace NaN with UNK in string columns
ARGteamMatchshooting[string_columns] = ARGteamMatchshooting[string_columns].fillna('UNK')

# Ensure the data types are correct for numeric columns
ARGteamMatchshooting[numeric_columns] = ARGteamMatchshooting[numeric_columns].astype(float)

print("Actual columns in ARGteamMatchshooting:")
print(ARGteamMatchshooting.columns.tolist())

ARGteamMatchKeeper = ARGstats.read_team_match_stats(stat_type="shooting")

# Reset the index to turn multi-index into columns
ARGteamMatchKeeper.reset_index(inplace=True)

# Check if the columns are a MultiIndex
if isinstance(ARGteamMatchKeeper.columns, pd.MultiIndex):
    # Flatten the multi-level column headers
    ARGteamMatchKeeper.columns = [''.join(map(str, col)).strip() for col in ARGteamMatchKeeper.columns]
ARGteamMatchKeeper.columns = add_tkmprefix_to_columns(ARGteamMatchKeeper.columns, prefix_tkm, conditions_tkm)
ARGteamMatchKeeper = ARGteamMatchKeeper.rename(columns={'tkmPerformanceSave%': 'tkmPerformanceSavepc'})
ARGteamMatchKeeper = ARGteamMatchKeeper.rename(columns={'tkmPerformancePSxG+/-': 'tkmPerformancePSxGdelta'})
ARGteamMatchKeeper = ARGteamMatchKeeper.rename(columns={'tkmPassesLaunch%': 'tkmPassesLaunchpc'})
ARGteamMatchKeeper = ARGteamMatchKeeper.rename(columns={'tkmLaunchedCmp%': 'tkmLaunchedCmppc'})
ARGteamMatchKeeper = ARGteamMatchKeeper.rename(columns={'tkmCrossesStp%': 'tkmCrossesStppc'})
ARGteamMatchKeeper = ARGteamMatchKeeper.rename(columns={'kmSweeper#OPA': 'kmSweeperOPA'})

# Identify numeric columns
numeric_columns = ARGteamMatchKeeper.select_dtypes(include=['number']).columns

# Identify string columns
string_columns = ARGteamMatchKeeper.select_dtypes(include=['object', 'string']).columns

# Replace NaN with 0 in numeric columns
ARGteamMatchKeeper[numeric_columns] = ARGteamMatchKeeper[numeric_columns].fillna(0)

# Replace NaN with UNK in string columns
ARGteamMatchKeeper[string_columns] = ARGteamMatchKeeper[string_columns].fillna('UNK')

# Ensure the data types are correct for numeric columns
ARGteamMatchKeeper[numeric_columns] = ARGteamMatchKeeper[numeric_columns].astype(float)

ARGteamMatchKeeper = ARGteamMatchKeeper.drop(columns=['tkmPenalty KicksPKatt', 'tkmPenalty KicksPKsv',
                                                      'tkmPenalty KicksPKm', 'tkmLaunchedCmp', 'tkmGoal KicksAvgLen',
                                                       'tkmLaunchedAtt', 'tkmGoal KicksAtt', 'tkmGoal KicksAtt' ])


print("Actual columns in ARGteamMatchKeeper:")
print(ARGteamMatchKeeper.columns.tolist())

ARGteamMatchpassingtypes = ARGstats.read_team_match_stats(stat_type="passing_types")

# Reset the index to turn multi-index into columns
ARGteamMatchpassingtypes.reset_index(inplace=True)

# Check if the columns are a MultiIndex
if isinstance(ARGteamMatchpassingtypes.columns, pd.MultiIndex):
    # Flatten the multi-level column headers
    ARGteamMatchpassingtypes.columns = [''.join(map(str, col)).strip() for col in ARGteamMatchpassingtypes.columns]
ARGteamMatchpassingtypes.columns = add_prefix_to_columns(ARGteamMatchpassingtypes.columns, prefix_tm, conditions)

# Identify numeric columns
numeric_columns = ARGteamMatchpassingtypes.select_dtypes(include=['number']).columns

# Identify string columns
string_columns = ARGteamMatchpassingtypes.select_dtypes(include=['object', 'string']).columns

# Replace NaN with 0 in numeric columns
ARGteamMatchpassingtypes[numeric_columns] = ARGteamMatchpassingtypes[numeric_columns].fillna(0)

# Replace NaN with UNK in string columns
ARGteamMatchpassingtypes[string_columns] = ARGteamMatchpassingtypes[string_columns].fillna('UNK')

# Ensure the data types are correct for numeric columns
ARGteamMatchpassingtypes[numeric_columns] = ARGteamMatchpassingtypes[numeric_columns].astype(float)

print("Actual columns in ARGteamMatchpassingtypes:")
print(ARGteamMatchpassingtypes.columns.tolist())

ARGteamMatchPassing = ARGstats.read_team_match_stats(stat_type="passing")

# Reset the index to turn multi-index into columns
ARGteamMatchPassing.reset_index(inplace=True)

# Check if the columns are a MultiIndex
if isinstance(ARGteamMatchPassing.columns, pd.MultiIndex):
    # Flatten the multi-level column headers
    ARGteamMatchPassing.columns = [''.join(map(str, col)).strip() for col in ARGteamMatchPassing.columns]
ARGteamMatchPassing.columns = add_prefix_to_columns(ARGteamMatchPassing.columns, prefix_tm, conditions)

# Identify numeric columns
numeric_columns = ARGteamMatchPassing.select_dtypes(include=['number']).columns

# Identify string columns
string_columns = ARGteamMatchPassing.select_dtypes(include=['object', 'string']).columns

# Replace NaN with 0 in numeric columns
ARGteamMatchPassing[numeric_columns] = ARGteamMatchPassing[numeric_columns].fillna(0)

# Replace NaN with UNK in string columns
ARGteamMatchPassing[string_columns] = ARGteamMatchPassing[string_columns].fillna('UNK')

# Ensure the data types are correct for numeric columns
ARGteamMatchPassing[numeric_columns] = ARGteamMatchPassing[numeric_columns].astype(float)

ARGteamMatchPassing = ARGteamMatchPassing.rename(columns={'tmmatchTotalCmp%': 'tmmatchTotalCmppc'})
ARGteamMatchPassing = ARGteamMatchPassing.rename(columns={'matchShortCmp%': 'matchShortCmppc'})
ARGteamMatchPassing = ARGteamMatchPassing.rename(columns={'matchMediumCmp%': 'matchMediumCmppc'})
ARGteamMatchPassing = ARGteamMatchPassing.rename(columns={'matchLongCmp%': 'matchLongCmppc'})

print("Actual columns in ARGteamMatchPassing:")
print(ARGteamMatchPassing.columns.tolist())


# Concatenate with outer join to include all rows
teamMatchstats = pd.concat([ARGteamMatchMisc, ARGteamMatchPossesion, ARGteamSchedule, ARGteamMatchDefense,  
                         ARGteamMatchGoalShotCreation, ARGteamMatchshooting, ARGteamMatchKeeper, ARGteamMatchpassingtypes,
                          ARGteamMatchPassing ], axis=1, join='outer')
teamMatchstats = teamMatchstats.loc[:, ~teamMatchstats.columns.duplicated()]
teamMatchstats = teamMatchstats.drop(columns=[''])
teamMatchstats.columns = teamMatchstats.columns.str.replace('-', '')
teamMatchstats.columns = teamMatchstats.columns.str.replace('(', '')
teamMatchstats.columns = teamMatchstats.columns.str.replace(')', '')

#break 12:47 pm
expected_columns = [
    "player", "match_id", "league", "season", "team", "game", "nation", "pos", "age", "jersey_number", 
    "Playermin", "pmPerformanceGls", "pmPerformanceAst", "pmPerformancePK", "pmPerformancePKatt", 
    "pmPerformanceSh", "pmPerformanceSoT", "pmPerformanceCrdY", "pmPerformanceCrdR", "pmPerformanceTouches", 
    "pmPerformanceTkl", "pmPerformanceInt", "pmPerformanceBlocks", "pmExpectedxG", "pmExpectednpxG", 
    "pmExpectedxAG", "pmSCASCA", "pmSCAGCA", "pmPassesCmp", "pmPassesAtt", "pmpassescmppc", "pmPassesPrgP", 
    "pmCarriesCarries", "pmCarriesPrgC", "pmtakeonsatt", "pmtakeonssucc", "pmPerformance2CrdY", 
    "pmPerformanceFls", "pmPerformanceFld", "pmPerformanceOff", "pmPerformanceCrs", "pmPerformanceTklW", 
    "pmPerformancePKwon", "pmPerformancePKcon", "pmPerformanceOG", "pmPerformanceRecov", "pmAerial DuelsWon", 
    "pmAerial DuelsLost", "pmaerialduelswonpc", "pmTouchesTouches", "pmTouchesDef Pen", "pmTouchesDef 3rd", 
    "pmTouchesMid 3rd", "pmTouchesAtt 3rd", "pmTouchesAtt Pen", "pmTouchesLive", "pmtakeonssuccpc", 
    "pmtakeonstkld", "pmtakeonstkldpc", "pmCarriesTotDist", "pmCarriesPrgDist", "pmCarries1/3", "pmCarriesCPA", 
    "pmCarriesMis", "pmCarriesDis", "pmReceivingRec", "pmReceivingPrgR", "pmTotalCmp", "pmTotalAtt", 
    "pmtotalcmppc", "pmTotalTotDist", "pmTotalPrgDist", "pmShortCmp", "pmShortAtt", "pmshortcmppc", 
    "pmMediumCmp", "pmMediumAtt", "pmmediumcmppc", "pmLongCmp", "pmLongAtt", "pmlongcmppc", "pmAst", "pmxAG", 
    "pmxA", "pmKP", "pm1/3", "pmPPA", "pmCrsPA", "pmPrgP", "pmPass TypesLive", "pmPass TypesDead", "pmPass TypesFK", 
    "pmPass TypesTB", "pmPass TypesSw", "pmPass TypesCrs", "pmPass TypesTI", "pmPass TypesCK", "pmCorner KicksIn", 
    "pmCorner KicksOut", "pmCorner KicksStr", "pmOutcomesCmp", "pmOutcomesOff", "pmOutcomesBlocks", 
    "pmTacklesTkl", "pmTacklesTklW", "pmTacklesTklDef 3rd", "pmTacklesTklMid 3rd", "pmTacklesTklAtt 3rd", 
    "pmChallengesTkl", "pmChallengesAtt", "pmchallengestklpc", "pmChallengesLost", "pmBlocksBlocks", 
    "pmBlocksSh", "pmBlocksPass", "pmInt", "pmTkl+Int", "pmClr", "pmErr"
]  
teamMatchstats = teamMatchstats[expected_columns]
print(teamMatchstats)
print(teamMatchstats.shape[1])

# Convert DataFrame to CSV in memory using StringIO INSTEad of using csv to write to disk
csv_buffer = io.StringIO()
teamMatchstats.to_csv(csv_buffer, index=False, encoding='utf-8', sep='\t')
csv_buffer.seek(0)

# Read the data
data = pd.read_csv(csv_buffer, delimiter='\t')
print(f"Total rows read: {len(data)}")

# Verify the contents of the DataFrame
print(data.head())  

# Write to a new in-memory CSV string using StringIO
output_buffer  = StringIO()
teamMatchstats.to_csv(output_buffer, index=False, sep='\t')
output_buffer.seek(0)

# Verify the contents of the processed data
print(output_buffer.getvalue())

def main():
    try:
        db_password = os.environ.get('DB_PASSWORD')

        # Establish connection to your SQL database
        conn = psycopg2.connect(
            dbname="Tier1", 
            user="postgres",  
            password=db_password,  
            host="localhost",  
            port="5432"
        )

        # Chunk size for processing data in batches
        chunk_size = 500 

        # Iterate over chunks of the DataFrame
        for chunk_start in range(0, len(teamMatchstats), chunk_size):
            chunk_end = min(chunk_start + chunk_size, len(teamMatchstats))
            chunk = teamMatchstats.iloc[chunk_start:chunk_end]

            with conn.cursor() as cur:
                # Create a StringIO object to hold CSV data
                csv_buffer = io.StringIO()
                chunk.to_csv(csv_buffer, sep='\t', index=False, header=False)

                # Reset the buffer position to start
                csv_buffer.seek(0)

                try:
                    # Use copy_from to copy the data from the StringIO buffer to the database
                    cur.copy_from(csv_buffer, "teamMatchstats", sep='\t')
                    conn.commit()
                except psycopg2.IntegrityError as e:
                    # IntegrityError is raised when there's a violation of constraints
                    print(f"IntegrityError: {e}")
                    conn.rollback()  # Rollback the transaction for the current chunk

        print("Data imported successfully")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    main()
end_time = time.time()
elapsed_time = end_time - start_time
print("Script execution time:", elapsed_time, "seconds")