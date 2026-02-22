import os
import json
import random
import datetime as dt
from dateutil.relativedelta import relativedelta

from nba_api.stats.endpoints import scoreboardv2, boxscoretraditionalv2


def get_target_date():
    today = dt.datetime.utcnow().date()
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

    for gid in game_ids:
        box = boxscoretraditionalv2.BoxScoreTraditionalV2(game_id=gid, timeout=60)
        players_df = box.player_stats.get_data_frame()

        if players_df.empty:
            continue

        players_sorted = players_df.sort_values("PTS", ascending=False)
        top = players_sorted.iloc[0]

        if best_player is None or top["PTS"] > best_player["PTS"]:
            best_player = top

    return best_player


def build_caption(game_date, player):
    date_str = game_date.strftime("%b %d, %Y")

    caption = f"""💥 10 years ago today ({date_str})…

{player['PLAYER_NAME']} caught fire.

🏀 {int(player['PTS'])} PTS
🎯 {int(player['FGM'])}/{int(player['FGA'])} FG
🎯 {int(player['FG3M'])}/{int(player['FG3A'])} from deep
🎁 {int(player['AST'])} AST
🛡 {int(player['STL'])} STL

Peak shot-making.
Peak takeover mode.

📚 NBA history — daily stat rewind.
"""

    return caption


def choose_image():
    urls = os.getenv("IMAGE_URLS")
    if not urls:
        raise Exception("IMAGE_URLS environment variable not set")

    url_list = [u.strip() for u in urls.split(",")]
    return random.choice(url_list)


def main():
    target_date = get_target_date()
    game_ids = fetch_games(target_date)

    if not game_ids:
        print("No NBA games found on that date.")
        return

    top_player = find_top_scorer(game_ids)

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
        "caption": caption
    }

    draft_output["caption_version"] = "v2-hype-emoji"
    
    print(json.dumps(draft_output, indent=2))


if __name__ == "__main__":
    main()
