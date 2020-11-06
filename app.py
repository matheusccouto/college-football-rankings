# TODO Remove power(exponent)
# TODO Add post win prob in schedule
""" Web application main script. """

import os
from typing import Any, Dict, List

import cfbd
import streamlit as st

import college_football_rankings as cfr
import ui
import ui.rankings
import ui.schedule
from college_football_rankings import iterative

FIRST_YEAR: int = 1869
RANKINGS_LEN = 25
ALGORITHM_NAME = "Algorithm"


@st.cache(show_spinner=False, ttl=10800)
def request_games(year: int, season_type: str) -> List[cfbd.Game]:
    """ Request games and keep it in cache for an hour. """
    return cfr.get_games(year=year, season_type=season_type)


@st.cache(show_spinner=False)
def request_teams() -> List[cfbd.Team]:
    """ Request teams and keep it in cache. """
    return cfr.get_teams()


@st.cache(show_spinner=False, ttl=10800)
def request_rankings(year: int) -> List[cfbd.RankingWeek]:
    """ Request rankings and keep it in cache for an hour. """
    return cfr.get_rankings(year=year)


def create_teams(games: List[cfbd.Game]) -> Dict[str, cfr.Team]:
    """ Create teams instances and fill schedules with games. """
    teams = request_teams()
    teams = cfr.create_teams_instances(teams=teams)
    cfr.fill_schedules(games=games, teams=teams)
    return cfr.clean_teams(teams=teams)


def main():
    """ Web app main routine. """

    st.beta_set_page_config(
        page_title="College Football Rankings",
        page_icon=os.path.join("img", "favicon.png"),
    )
    st.title(":football: College Football Rankings")

    # Year
    year = ui.year_selector(first_year=FIRST_YEAR)

    # Games
    games = request_games(year=year, season_type="both")

    # Week
    n_reg_weeks = cfr.last_played_week(games=games, season_type="regular")
    reg_weeks = [f"{i + 1}" for i in range(n_reg_weeks)]

    n_post_weeks = cfr.last_played_week(games=games, season_type="postseason")
    post_weeks = [f"Post {i + 1}" for i in range(n_post_weeks)]

    options = reg_weeks + post_weeks
    week = st.select_slider(label="Select week", options=options, value=options[-1])

    if "Post" in week:
        week = int(week.replace("Post ", ""))
        season_type = "postseason"
    else:
        week = int(week)
        season_type = "regular"

    # Polls
    rankings = cfr.create_polls(year=year, max_week=week)

    # Teams
    teams = create_teams(games=games)
    cfr.filter_schedules(teams=teams, max_week=week, season_type=season_type)

    st.sidebar.title("Algorithm Settings")
    margin = st.sidebar.checkbox("Consider margin")
    post_win_prob = st.sidebar.checkbox("Consider post win probability")

    # Evaluate rankings.
    try:
        rankings[ALGORITHM_NAME] = cfr.Ranking(name=ALGORITHM_NAME)
        ranks = cfr.evaluate(
            teams=teams,
            func=iterative.power,
            consider_margin=margin,
            consider_post_win_prob=post_win_prob,
        )
        rankings[ALGORITHM_NAME].add_week(
            week=week, rankings=[rank.name for rank in ranks]
        )
    except cfr.RankingError:
        st.error("Could not find an equilibrium for algorithm rankings.")

    # Rankings.
    st.text("")
    st.header(":trophy: Rankings")

    # Filter week.
    rankings_week = {
        key: val.get_week(week) for key, val in rankings.items() if val.get_week(week)
    }

    # Rankings comparison.
    ui.rankings.comparison(rankings=rankings_week, teams=teams, length=RANKINGS_LEN)

    st.text("")
    st.header(":date: Schedule")

    ui.schedule.table(rankings=rankings_week, teams=teams)


if __name__ == "__main__":
    main()
