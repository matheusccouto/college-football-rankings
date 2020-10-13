import datetime
from typing import Sequence, Dict, Any, Tuple, Optional

import pandas as pd
import streamlit as st

import college_football_rankings as cfr
import college_football_api as cfapi

FIRST_YEAR = 1980
THIS_YEAR = datetime.date.today().year


@st.cache(show_spinner=False)
def get_all_games_data(year: int) -> Sequence[Dict[str, Any]]:
    """ Get all games data. Keep on cache until changes args."""
    return cfr.get_all_games_data(year=year)


@st.cache(show_spinner=False)
def get_polls(year: int, week: int) -> Dict[str, Sequence[str]]:
    """ Get rankings from specified year and week. """
    college_football_api = cfapi.CollegeFootballAPI()
    data = college_football_api.rankings(year=year, week=week)[0]
    polls = data["polls"]
    return {poll["poll"]: [pos["school"] for pos in poll["ranks"]] for poll in polls}


def get_last_week(games: Sequence[Dict[str, Any]]) -> int:
    """ Get last played regular week. """
    for game in reversed(games):
        if "regular" not in game["season_type"]:
            continue
        if game["home_points"] is None:
            continue
        return game["week"]


def append_records(
    team: str, teams_records: Dict[str, str],
):
    """ Append records to school name."""
    try:
        return f"{team} ({teams_records[team]})"
    except KeyError:
        return f"{team} (?)"


def main():
    """ User interface. """

    st.beta_set_page_config(page_title="College Football Rankings")

    st.title("College Football Rankings")

    year = st.selectbox("Year", options=range(THIS_YEAR, FIRST_YEAR - 1, -1))
    games = get_all_games_data(year)
    n_weeks = get_last_week(games)

    week = st.slider("Week", min_value=1, max_value=n_weeks, value=n_weeks)

    with st.spinner("Evaluating rankings..."):
        teams_records = cfr.prepare_data(games, week=week)
        ranking = cfr.evaluate(teams_records, func=cfr.iterative.power, score=False)
        polls = get_polls(year=year, week=week)
        polls = {key: val for key, val in polls.items() if "FCS" not in key}

        ranking_len = max([len(val) for val in polls.values()])
        ranks = {**{"Iterative algorithm": ranking[:ranking_len]}, **polls}

        records = cfr.create_records_dict(teams_records)
        ranks = {
            name: [append_records(team, records) for team in rank]
            for name, rank in ranks.items()
        }

        df = pd.DataFrame(ranks, index=range(1, ranking_len + 1))
        st.table(df)


if __name__ == "__main__":
    main()
