import os
from datetime import datetime
import statistics
import pandas as pd

from dotenv import load_dotenv

## NOTE ##
# There is a bias that is summoners data will be the
# one updated from date of data consolidation
# not the one used for the matchmaking when the match
# happened

# https://riot-watcher.readthedocs.io
from riotwatcher import LolWatcher, ApiError

load_dotenv()

api_key = os.getenv("LOL_API_KEY")
sum_name = os.getenv("SUM_NAME") # 안드래아스
region = "kr"
queue_type = "RANKED_SOLO_5x5"
fallback_queue_type = "RANKED_FLEX_SR"

lol_watcher = LolWatcher(api_key)

# id = summonerId
sard_sum = lol_watcher.summoner.by_name(region, sum_name)
sard_info = lol_watcher.league.by_summoner(region, sard_sum["id"])
sard_sum_data = None

total_ignored_player = 0

for s in sard_info:
    if s["queueType"] == queue_type:
        sard_sum_data = s

if sard_sum_data == None:
    exit(88)

# Fetch Sardoche matches
matches = lol_watcher.match.matchlist_by_puuid(
    region=region,
    puuid=sard_sum["puuid"],
    start=None,
    count=100,
    queue=None,
    type="ranked"
)

data = {
    "match_id": list(), # the match ID
    "match_date": list(), # the match start date
    "sard_rank": list(), # Sardoche's rank during the match
    "sard_wr": list(), # Sardoche's wr during the match
    "sard_win": list(), # Sardoche win or not
    "sard_team": list(),
    "t1_avg_rank": list(), # Team 1 average rank
    "t2_avg_rank": list(),
    "t1_med_rank": list(), # Team 1 median rank
    "t2_med_rank": list(),
    "t1_best_rank": list(), # Team 1 best rank
    "t2_best_rank": list(),
    "t1_lowest_rank": list(), # Team 1 noobix
    "t2_lowest_rank": list(),
    "t1_avg_role_note": list(), # Team 1 role note (TODO explain calculation)
    "t2_avg_role_note": list(),
    "t1_avg_wr": list(), # Team 1 average win rate
    "t2_avg_wr": list(),
    "t1_med_wr": list(), # Team 1 median win rage
    "t2_med_wr": list(),
    "t1_best_wr": list(), # Team 1 best player
    "t2_best_wr": list(),
    "t1_lowest_wr": list(), # Team 1 lowest win rate
    "t2_lowest_wr": list()
}

tier_val = {
    "IRON": 1,
    "BRONZE": 2,
    "SILVER": 3,
    "GOLD": 3.5,
    "PLATINUM": 4,
    "DIAMOND": 4.5,
    "MASTER": 6,
    "GRANDMASTER": 8,
    "CHALLENGER": 10
}
tier_rank_val = {
    "I": 1,
    "II": 0.8,
    "III": 0.7,
    "IV": 0.5,
    "V": 0.2
}

def get_rank_value(tier, rank, league_points = 0):
    # TODO use league points for calculation
    return tier_val.get(tier) * tier_rank_val.get(rank)

def get_role_note(participant, summoner):
    # type:(dict, dict) -> int
    
    # participant["championId"]
    # participant["lane"]
    # TODO for more precise infos 
    # TODO fetch some past matchs of participant to know which role he is maining
    # champions_mastery = lol_watcher.champion_mastery.by_summoner(region, summoner["summonerId"])
    # this one is hard because of API limitation
    # have to fetch lots of data but wont be able
    # for now just return the champLevel
    return participant["champLevel"]
    
            

# returns (rank value, role note, wr)
def consolidate_player_data(match_id, participant):
    # type:(str, dict) -> list[int]
    
    rank_value = 0
    role_note = 0
    wr = 0
    summoner_data = None
    team = 1 if participant["teamId"] == 100 else 2
    if sard_sum["id"] == participant["summonerId"]:
        sard_rank = get_rank_value(
            sard_sum_data["tier"],
            sard_sum_data["rank"],
            sard_sum_data["leaguePoints"]
        )
        data["sard_rank"].append(sard_rank)
        total_games = sard_sum_data["wins"] + sard_sum_data["losses"]
        wr = (sard_sum_data["wins"] / total_games) * 100
        data["sard_wr"].append(wr)
        data["sard_team"].append(team)
        data["sard_win"].append(participant["win"])
        summoner_data = sard_sum_data
    
    fallback_summoner_data = None
    if summoner_data == None:
        summoner = lol_watcher.league.by_summoner(region, participant["summonerId"])
        # TODO print error if queueType not found
        for s in summoner:
            if s["queueType"] == queue_type:
                summoner_data = s
            elif s["queueType"] == fallback_queue_type:
                fallback_summoner_data = s
        
    if summoner_data == None:
        if fallback_summoner_data != None:
            print(f'no data found for queue {queue_type}. Match {match_id}, summoner id {participant["summonerId"]} (will use {fallback_queue_type} instead)')
            summoner_data = fallback_summoner_data
        else:
            total_ignored_player += 1
            print(f'missing summoner data for Match {match_id}, summoner id {participant["summonerId"]} (this teamate will be ignored in stats)')
            return (None, None, None, None)
    
    rank_value = get_rank_value(
        summoner_data["tier"],
        summoner_data["rank"],
        summoner_data["leaguePoints"]
    )
    
    if wr == 0:
        total_games = summoner_data["wins"] + summoner_data["losses"]
        wr = (summoner_data["wins"] / total_games) * 100
        
    role_note = get_role_note(participant=participant, summoner=summoner_data)
    
    return (team, rank_value, role_note, wr)

def compute_team_data(team_data):
    rank_list = team_data.get("rankValue")
    role_list = team_data.get("roleNote")
    wr_list = team_data.get("wr")
    
    avg_rank = sum(rank_list) / len(rank_list)
    med_rank = statistics.median(rank_list)
    best_rank = max(rank_list)
    lowest_rank = min(rank_list)
    
    avg_role = sum(role_list) / len(role_list)

    avg_wr = sum(wr_list) / len(wr_list)
    med_wr = statistics.median(wr_list)
    best_wr = max(wr_list)
    lowest_wr = min(wr_list)
    
    return {
        "avgRank": avg_rank,
        "medRank": med_rank,
        "bestRank": best_rank,
        "lowestRank": lowest_rank,
        "avgRole": avg_role,
        "avgWr": avg_wr,
        "medWr": med_wr,
        "bestWr": best_wr,
        "lowestWr": lowest_wr
    }
    
    
            
for match in matches:
    data["match_id"].append(match)
    print(f"Computing match {match}")
    
    match_data = lol_watcher.match.by_id(region, match)
    match_data_info = match_data["info"]
    
    data["match_date"].append(datetime.fromtimestamp(match_data_info["gameStartTimestamp"] / 1000))
    
    players_data = {
        "1": {
            "rankValue": list(),
            "roleNote": list(),
            "wr": list()
        },
        "2": {
            "rankValue": list(),
            "roleNote": list(),
            "wr": list()
        }
    }
    
    
    for participant in match_data_info["participants"]:
        player_data = consolidate_player_data(match, participant)
        if player_data[0] != None:
            players_data[str(player_data[0])]["rankValue"].append(player_data[1])
            players_data[str(player_data[0])]["roleNote"].append(player_data[2])
            players_data[str(player_data[0])]["wr"].append(player_data[3])
        
    team_one = compute_team_data(players_data.get("1"))
    team_two = compute_team_data(players_data.get("2"))
    
    data["t1_avg_rank"].append(team_one["avgRank"])
    data["t2_avg_rank"].append(team_two["avgRank"])
    data["t1_med_rank"].append(team_one["medRank"])
    data["t2_med_rank"].append(team_two["medRank"])
    data["t1_best_rank"].append(team_one["bestRank"])
    data["t2_best_rank"].append(team_two["bestRank"])
    data["t1_lowest_rank"].append(team_one["lowestRank"])
    data["t2_lowest_rank"].append(team_two["lowestRank"])
    
    data["t1_avg_role_note"].append(team_one["avgRole"])
    data["t2_avg_role_note"].append(team_two["avgRole"])

    data["t1_avg_wr"].append(team_one["avgWr"])
    data["t2_avg_wr"].append(team_two["avgWr"])
    data["t1_med_wr"].append(team_one["medWr"])
    data["t2_med_wr"].append(team_two["medWr"])
    data["t1_best_wr"].append(team_one["bestWr"])
    data["t2_best_wr"].append(team_two["bestWr"])
    data["t1_lowest_wr"].append(team_one["lowestWr"])
    data["t2_lowest_wr"].append(team_two["lowestWr"])

data = pd.DataFrame(data)

data.to_csv("sardhelp.csv")
        
print(data)

print(f"{total_ignored_player} players were ignored for the stats")