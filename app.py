""" College Football Rankings web app. """

import datetime
import os
from typing import Sequence, Dict, Any, Tuple, Optional

import pandas as pd
import streamlit as st

import college_football_api as cfapi
import college_football_rankings as cfr

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
    """ Get last regular week. """
    for game in reversed(games):
        if "regular" not in game["season_type"]:
            continue
        return game["week"]


def get_last_played_week(games: Sequence[Dict[str, Any]]) -> int:
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


def schedule_to_dataframe(
    schedule: Dict[int, Tuple[Optional[str], Optional[Tuple[int, int]]]],
    ranking: Sequence[str],
    week: int,
) -> pd.DataFrame:
    """ Transform schedule data into a DataFrame. """
    cleaned: Dict[int, Tuple[str, str]] = {}
    for i in range(1, week + 1):
        # If the team didn't play this week, leave it blank.
        if i not in schedule:
            cleaned[i] = ("-", "-")
            continue
        # If rival is None somehow, also forget it.
        rival, score = schedule[i]  # Unpack
        if rival is None:
            cleaned[i] = ("-", "-")
            continue
        # If the team played, clean data.
        # Prepend rank.
        if rival in ranking:
            rival_pos = ranking.index(rival) + 1
            rival = f"#{rival_pos} {rival}"
        # If it is yet to play, erase score.
        if score is None:
            score = "-"
        # Otherwise, format it.
        else:
            score = f"{score[0]} x {score[1]}"
        # Store cleaned data.
        cleaned[i] = (rival, score)
    data_frame = pd.DataFrame(cleaned).transpose()
    data_frame.columns = ["Opponent", "Score"]
    return data_frame


def main():
    """ User interface. """
    # Page configuration.
    st.beta_set_page_config(
        page_title="College Football Rankings",
        page_icon=os.path.join("img", "favicon.png"),
    )

    st.title(":football: College Football Rankings")

    # Download season data.
    year = st.selectbox("Year", options=range(THIS_YEAR, FIRST_YEAR - 1, -1))
    games = get_all_games_data(year)
    # Find out the number of regular weeks.
    n_weeks = get_last_week(games)
    n_played_weeks = get_last_played_week(games)

    # Select week.
    week = st.slider(
        "Week", min_value=1, max_value=n_played_weeks, value=n_played_weeks
    )

    st.header(":trophy: Rankings")
    with st.spinner("Evaluating rankings..."):
        # Get polls for selected year and week.
        polls = get_polls(year=year, week=week)
        # Keep only relevant polls
        to_keep = ["Playoff Committee Rankings", "AP Top 25", "Coaches Poll"]
        polls = {key: val for key, val in polls.items() if key in to_keep}
        # Get that year's poll length.
        ranking_len = max([len(val) for val in polls.values()])

        # Prepare teams schedules data.
        teams_schedules = cfr.create_teams_schedule_dict(games)
        cfr.filter_week(teams_margins=teams_schedules, week=week)
        teams_margins = cfr.create_teams_margins_dict(teams_schedules)

        # Evaluate iterative ranking.
        ranking = cfr.evaluate(teams_margins, func=cfr.iterative.power, score=False)

        # Merge rankings into a single dictionary.
        ranks = {**{"Iterative algorithm": ranking[:ranking_len]}, **polls}

        # Append the records to the teams names in the rankings.
        records = cfr.create_records_dict(teams_margins)
        ranks_with_records = {
            name: [append_records(team, records) for team in rank]
            for name, rank in ranks.items()
        }

        # Transform data into a dataframe and show it.
        data_frame = pd.DataFrame(ranks_with_records, index=range(1, ranking_len + 1))
        st.table(data_frame)

        # Select team to see schedule.
        st.header(":date: Schedule")
        team = st.selectbox("Select team", options=sorted(teams_schedules.keys()))

        # Select ranking to show next to the teams name.
        show_ranking = st.selectbox("Select ranking", options=list(ranks.keys()))
        selected_ranking = ranks[show_ranking]

        schedule_df = schedule_to_dataframe(
            teams_schedules[team], ranking=selected_ranking, week=n_weeks
        )
        st.table(schedule_df)


if __name__ == "__main__":
    main()
