""" Rankings web app section. """

from typing import Dict, List, Optional

import pandas as pd
import streamlit as st

import college_football_rankings as cfr
import ui


def get_team_position(team: str, ranking: List[str]) -> Optional[int]:
    """ Get team position in a ranking. """
    if team not in ranking:
        return None
    return ranking.index(team) + 1


def table(rankings: Dict[str, List[str]], teams: Dict[str, cfr.Team]):
    """ Write schedule table. """
    # Select team to see schedule.
    options = sorted(teams.keys())
    team_name = st.selectbox("Select team", options=options)
    team = teams[team_name]

    # Select ranking to show next to the teams name.
    options = list(rankings.keys())
    ranking_name = st.selectbox("Select ranking", options=options)

    if not ranking_name:
        return

    games = team.schedule.games
    opponents = [game.opponent for game in games]
    scores = [
        f"{game.team_points} x {game.opponent_points}" if game.team_points else ""
        for game in games
    ]

    # Get ranking positions.
    ranking = rankings[ranking_name]
    opponents_pos = [get_team_position(opp, ranking) for opp in opponents]
    opponents_pos = [str(pos) if pos else "" for pos in opponents_pos]

    # Add logos.
    opponents = ui.add_logos_and_records(opponents, teams)

    schedule_df = pd.DataFrame(
        {"Opponent": opponents, "Ranking": opponents_pos, "Score": scores}
    )

    schedule_html_table = schedule_df.to_html(escape=False, index=False)
    schedule_html_table = ui.format_html_table(schedule_html_table)
    st.write(schedule_html_table, unsafe_allow_html=True)
