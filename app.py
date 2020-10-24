""" College Football Rankings web app. """

import copy
import datetime
import os
from typing import Sequence, Dict, Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st

import college_football_api as cfapi
import college_football_rankings as cfr

FIRST_YEAR = 1980
THIS_YEAR = datetime.date.today().year
RANKING_LEN = 25


@st.cache(show_spinner=False, allow_output_mutation=True)
def evaluate(teams_margins, name, *args, **kwargs):
    """ Run evaluate multiple times using cache. """
    rankings = dict()
    for i, margin in enumerate(teams_margins):
        try:
            rankings.update({i + 1: {name: cfr.evaluate(margin, *args, **kwargs)}})
        except cfr.iterative.EquilibriumError:
            pass
    return rankings


@st.cache(show_spinner=False)
def get_all_games_data(year):
    """ Get all games data. Keep on cache until changes args."""
    return cfr.get_all_games_data(year=year)


@st.cache(show_spinner=False)
def get_all_teams_logos(year):
    """ Get all teams logo. Keep on cache until changes args."""
    return cfr.get_all_teams_logos(year=year)


@st.cache(show_spinner=False, allow_output_mutation=True)
def get_polls(year):
    """ Get rankings from specified year and week. """
    college_football_api = cfapi.CollegeFootballAPI()
    data = college_football_api.rankings(year=year)

    # Polls to keep
    to_keep = ["Playoff Committee Rankings", "AP Top 25", "Coaches Poll"]

    weeks = dict()
    for week in data:
        polls = dict()
        for poll in week["polls"]:
            if poll["poll"] not in to_keep:
                continue
            polls.update({poll["poll"]: [pos["school"] for pos in poll["ranks"]]})
        weeks.update({week["week"] - 1: polls})
    return weeks


def get_last_week(games):
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
    team, teams_records,
):
    """ Append records to school name."""
    try:
        return f"{team} ({teams_records[team]})"
    except KeyError:
        return f"{team} (?)"


def schedule_to_dataframe(
    schedule, week,
):
    """ Transform schedule data into a DataFrame. """
    cleaned = {}
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


def create_html_tag(
    team, logos_dict=None, rankings=None, records_dict=None,
):
    """ Create html tag with logo, ranking, team name and record. """
    logo = ""
    if logos_dict is not None:
        try:
            logo = f'<img src="{logos_dict[team]}" height="16"> '
        except KeyError:
            pass
    rank = ""
    if rankings is not None:
        try:
            rank = f"#{rankings.index(team) + 1} "
        except ValueError:
            pass
    record = ""
    if records_dict is not None:
        try:
            record = f" {records_dict[team]}"
        except KeyError:
            pass
    return logo + rank + team + record


def add_logos_and_records(
    series, logos_dict=None, rankings=None, records_dict=None,
):
    """ Add teams logo and records to every item in a pandas Series. """
    values = [
        create_html_tag(team, logos_dict, rankings, records_dict) for team in series
    ]
    return pd.Series(values, index=series.index)


def format_html_table(html):
    """ Format a html table. """
    html = html.replace("<table", "<table width=100%")
    html = html.replace("<table", '<table style="text-align: right;"')
    return html


def all_weeks_margins(teams_schedules, week):
    """ Calculate all weeks margins. """
    margins = []
    team_schedules_copy = copy.deepcopy(teams_schedules)
    for i in range(week, 0, -1):
        cfr.filter_week(teams_margins=team_schedules_copy, week=i)
        teams_margins = cfr.create_teams_margins_dict(team_schedules_copy)
        margins.append(teams_margins)
    return list(reversed(margins))


def merge_rankings(*args):
    """ Merge rankings dict by dict. """
    merged = {}
    for arg in args:
        for key, val in arg.items():
            if key in merged:
                merged[key].update(val)
            else:
                merged[key] = val
    return merged


def time_series(rankings, team, ranking_name, max_pos):
    """ Build team time series ranking. """
    series = {}
    for week, ranks in rankings.items():
        if ranking_name in ranks:
            standings = ranks[ranking_name]
            try:
                position = standings.index(team) + 1
            except ValueError:
                position = np.nan
        else:
            position = np.nan
        if position and position > max_pos:
            position = np.nan
        series.update({week: position})
    return series


def plot_team_series(team_time_series, max_weeks, current_week, last_week):
    """ Plot time series from team rankings. """
    team_time_series = {
        week: rank for week, rank in team_time_series.items() if int(week) <= last_week
    }
    x = sorted(list(team_time_series.keys()))
    y = [y for _, y in sorted(zip(team_time_series.keys(), team_time_series.values()))]

    proj_x = x[current_week:]
    proj_y = y[current_week:]

    x = x[:current_week + 1]
    y = y[:current_week + 1]

    fig, ax = plt.subplots(figsize=(10, 2))

    ax.plot(proj_x, proj_y, color="lightgray", ls="--")
    ax.plot(x, y, color="hotpink")

    ax.set_xlim(0, max_weeks)
    ax.set_ylim(RANKING_LEN + 1, 1)
    for key, val in team_time_series.items():
        if val is None:
            continue
        ax.annotate(
            f"#{val}",
            (key, val),
            va="center",
            ha="center",
            bbox=dict(boxstyle="circle", fc="white", lw=0),
        )
    ax.set_xticks(range(max_weeks + 1))
    ax.set_yticks([])
    ax.xaxis.set_tick_params(length=0)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.spines["bottom"].set_visible(False)
    st.pyplot(fig, clear_figure=True)


def project_future_margins(margins, ranking, selected_week, total_weeks):
    """ Create projected margins. """
    new_margins = []
    for week in range(1, total_weeks + 1, 1):
        # Copy margins.
        projected_margins = copy.deepcopy(
            margins[np.clip(selected_week, None, len(margins)) - 1]
        )
        # Apply projections
        cfr.project_teams_margins(projected_margins, ranking, week)
        new_margins.append(projected_margins)
    return new_margins


def main():
    """ User interface. """
    # Page configuration.
    st.beta_set_page_config(
        page_title="College Football Rankings",
        page_icon=os.path.join("img", "favicon.png"),
    )

    st.title(":football: College Football Rankings")

    # Download season data.
    year = st.selectbox("Select year", options=range(THIS_YEAR, FIRST_YEAR - 1, -1))
    games = get_all_games_data(year)
    logos = get_all_teams_logos(year)
    # Find out the number of regular weeks.
    n_weeks = get_last_week(games)
    n_played_weeks = get_last_played_week(games)


    # Select week.
    week = st.slider(
        "Select week", min_value=1, max_value=n_played_weeks, value=n_played_weeks
    )
    apply_proj = st.checkbox("Apply projections")
    if apply_proj:
        max_weeks = n_weeks
        show_week = st.slider(
            "Select week to project",
            min_value=1,
            max_value=max_weeks,
            value=n_played_weeks,
        )
    else:
        max_weeks = n_played_weeks
        show_week = week

    # Rankings

    # Title
    st.title("")  # Blank line.
    st.header(":trophy: Rankings")

    # Get ranks for selected year and week.
    all_weeks_rankings = get_polls(year=year)

    # Avoid mutating the return of st.cache
    ranks = copy.deepcopy(all_weeks_rankings)

    # Prepare teams schedules data.
    teams_schedules = cfr.create_teams_schedule_dict(games)
    cfr.filter_week(teams_schedules, week)
    margins = all_weeks_margins(teams_schedules, n_weeks)

    # -1 to convert to index starting in 0.
    selected_margins = margins[week - 1]
    # Append the records to the teams names in the rankings.
    records = cfr.create_records_dict(selected_margins)

    # Evaluate custom rankings.
    with st.spinner("Preparing rankings..."):

        # Evaluate Margin Unaware Algorithm.
        margin_unaware = evaluate(
            margins,
            name="Margin Unaware Algorithm",
            func=cfr.iterative.power,
            score=False,
        )
        # Evaluate Margin Aware Algorithm.
        margin_aware = evaluate(
            margins, name="Margin Aware Algorithm", func=cfr.iterative.power, score=True
        )

        # Merge
        ranks = merge_rankings(ranks, margin_unaware, margin_aware)
        # Extract ranks from selected week.
        week_ranks = ranks[np.clip(week, None, n_played_weeks)]

        if apply_proj:
            margins = project_future_margins(
                margins,
                ranking=week_ranks["Margin Unaware Algorithm"],
                selected_week=show_week,
                total_weeks=n_weeks,
            )
            # Evaluate Margin Unaware Algorithm.
            margin_unaware = evaluate(
                margins,
                name="Margin Unaware Algorithm",
                func=cfr.iterative.power,
                score=False,
            )

            margins = project_future_margins(
                margins,
                ranking=week_ranks["Margin Aware Algorithm"],
                selected_week=show_week,
                total_weeks=n_weeks,
            )
            # Evaluate Margin Aware Algorithm.
            margin_aware = evaluate(
                margins,
                name="Margin Aware Algorithm",
                func=cfr.iterative.power,
                score=True,
            )

            # Merge
            ranks = merge_rankings(ranks, margin_unaware, margin_aware)
            # Extract ranks from selected week.
            week_ranks = ranks[show_week]

    # Select ranks to show.
    selected_ranks = st.multiselect("Select rankings", options=list(week_ranks.keys()))
    # Prepare dict with ranks to show.
    selected_ranks = {name: week_ranks[name][:RANKING_LEN] for name in selected_ranks}

    # If selected any ranking.
    if selected_ranks:

        # Transform data into a dataframe and show it.
        index = [f"#{i}" for i in range(1, RANKING_LEN + 1)]
        data_frame = pd.DataFrame(selected_ranks, index=index)
        data_frame = data_frame.apply(
            add_logos_and_records, logos_dict=logos, records_dict=records
        )
        html_table = data_frame.to_html(escape=False)
        html_table = format_html_table(html_table)
        st.write(html_table, unsafe_allow_html=True)

    st.title("")  # Blank line.

    # Select team to see schedule.
    team = st.selectbox(
        "Select team", options=sorted(teams_schedules.keys()), key="schedule team"
    )

    # Select ranking to show next to the teams name.
    ranking_to_show = st.selectbox(
        "Select ranking", options=list(week_ranks.keys()), key="schedule ranking"
    )

    selected_ranking = week_ranks[ranking_to_show][:RANKING_LEN]

    # Schedule

    st.text("")  # Blank line.
    st.header(":date: Schedule")

    schedule_df = schedule_to_dataframe(teams_schedules[team], week=n_weeks)
    schedule_df["Opponent"] = add_logos_and_records(
        schedule_df["Opponent"], logos_dict=logos, rankings=selected_ranking,
    )
    schedule_df = schedule_df.fillna("-")

    schedule_html_table = schedule_df.to_html(escape=False)
    schedule_html_table = format_html_table(schedule_html_table)
    st.write(schedule_html_table, unsafe_allow_html=True)

    st.text("")  # Blank line.
    st.header(":chart_with_upwards_trend:Evolution")

    team_time_series = time_series(ranks, team, ranking_to_show, RANKING_LEN)
    plot_team_series(team_time_series, max_weeks, week, show_week)


if __name__ == "__main__":
    main()
