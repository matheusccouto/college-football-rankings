""" User interface. """

import datetime
from typing import Dict, Sequence

import streamlit as st

import college_football_rankings as cfr


def year_selector(first_year: int, last_year: int):
    """ Year selector widget. """
    return st.selectbox("Select year", options=range(last_year, first_year - 1, -1))


def week_selector(n_weeks: int):
    """ Week selector widget. """
    return st.slider("Select week", min_value=1, max_value=n_weeks, value=n_weeks)


def format_html_table(html):
    """ Format a html table. """
    html = html.replace("<table", "<table width=100%")
    html = html.replace("<table", '<table style="text-align: right;"')
    return html


def create_html_tag(team: cfr.Team):
    """ Create html tag with logo, team name and record. """
    return f'<img src="{team.logo_light}" height="16"> {team.name} {team.record}'


def add_logos_and_records(names: Sequence, teams: Dict[str, cfr.Team]) -> Sequence:
    """ Add teams logo and records to every team name. """
    values = [create_html_tag(teams[team]) if team in teams else "" for team in names]
    return values
