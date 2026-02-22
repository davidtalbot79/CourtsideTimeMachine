import os
import json
import random
import datetime as dt
from dateutil.relativedelta import relativedelta

from nba_api.stats.endpoints import scoreboardv2, boxscoretraditionalv2


def get_target_date():
    today = dt.datetime.now(dt.timezone.utc).date()
    return today - relativedelta(years=10)


def fetch_games(game_date):
    date_str = game_date.strftime("%m/%d/%Y")
    scoreboard = scoreboardv2.ScoreboardV2(game_date=date_str, timeout=60)
    games_df = scoreboard.game_header.get_data_frame()

    if games_df.empty:
        return []

    return games_df["GAME_ID"].tolist()


def find_top_scorer(game_ids):
    best_player = None
    best_game_id = None

    for gid in game_ids:
        box = boxscoretraditionalv2.BoxScoreTraditionalV2(game_id=gid, timeout=60)
        players_df = box.player_stats.get_data_frame()

        if players_df.empty:
            continue

        players_sorted = players_df.sort_values("PTS", ascending=False)
        top = players_sorted.iloc[0]

        if best_player is None or top["PTS"] > best_player["PTS"]:
            best_player = top
            best_game_id = gid

    return best_player, best_game_id


def build_caption(game_date, player):
    date_str = game_date.strftime("%b %d, %Y")

    caption = f"""💥 10 YEARS AGO TODAY ({date_str})

{player['PLAYER_NAME']} caught fire.

🏀 {int(player['PTS'])} PTS
🎯 {int(player['FGM'])}/{int(player['FGA'])} FG
🎯 {int(player['FG3M'])}/{int(player['FG3A'])} from deep
🎁 {int(player['AST'])} AST
🛡 {int(player['STL'])} STL

This wasn’t just a good night.
This was peak shot-making.

📚 NBA history — daily stat rewind.
"""
    return caption


def choose_image():
    urls = os.getenv("IMAGE_URLS")
    if not urls:
        raise Exception("IMAGE_URLS environment variable not set")

    url_list = [u.strip() for u in urls.split(",")]
    return random.choice(url_list)

def get_final_score_line(game_id):
    box = boxscoretraditionalv2.BoxScoreTraditionalV2(game_id=game_id, timeout=60)
    teams_df = box.team_stats.get_data_frame()

    # Expect 2 rows: the two teams
    if teams_df is None or teams_df.empty or len(teams_df) < 2:
        return None

    t1 = teams_df.iloc[0]
    t2 = teams_df.iloc[1]

    team1 = t1["TEAM_ABBREVIATION"]
    team2 = t2["TEAM_ABBREVIATION"]
    pts1 = int(t1["PTS"])
    pts2 = int(t2["PTS"])

    # Put winner first
    if pts2 > pts1:
        team1, team2, pts1, pts2 = team2, team1, pts2, pts1

    return f"{team1} {pts1} — {team2} {pts2}"

def main():
    target_date = get_target_date()
    game_ids = fetch_games(target_date)

    if not game_ids:
        print("No NBA games found on that date.")
        return

    top_player, top_game_id = find_top_scorer(game_ids)

    score_line = get_final_score_line(top_game_id) if top_game_id else None
    
    if top_player is None:
        print("No player data found.")
        return

    caption = build_caption(target_date, top_player)
    image_url = choose_image()

    draft_output = {
    "target_date": str(target_date),
    "image_url": image_url,
    "top_scorer": top_player["PLAYER_NAME"],
    "points": int(top_player["PTS"]),
    "score_line": score_line,
    "caption": caption
}

    draft_output["caption_version"] = "v2-hype-emoji"
    
    print(json.dumps(draft_output, indent=2))


if __name__ == "__main__":
    main()
