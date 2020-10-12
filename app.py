import datetime
from typing import Sequence, Dict, Any

import streamlit as st

import college_football_rankings as cfr

FIRST_YEAR = 1980
THIS_YEAR = datetime.date.today().year


@st.cache(show_spinner=False)
def get_all_games_data(year: int) -> Sequence[Dict[str, Any]]:
    """ Get all games data. Keep on cache until changes args."""
    return cfr.get_all_games_data(year=year)


def get_last_week(games: Sequence[Dict[str, Any]]) -> int:
    """ Get last played regular week. """
    for game in reversed(games):
        if "regular" not in game["season_type"]:
            continue
        if game["home_points"] is None:
            continue
        return game["week"]


st.title("College Football Rankings")

year = st.selectbox("Year", options=range(THIS_YEAR, FIRST_YEAR - 1, -1))
games = get_all_games_data(year)
n_weeks = get_last_week(games)

week = st.slider("Week", min_value=1, max_value=n_weeks, value=n_weeks)

with st.spinner("Evaluating rankings..."):
    ranking = cfr.evaluate(func=cfr.iterative.power, year=year, week=week, score=False)
    st.write(ranking[:25])
