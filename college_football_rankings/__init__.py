"""
Estimate and predict college football rankings.

Powered by collegefootballdata.com
"""
from typing import Any, Dict, Sequence, Tuple, Optional, List, Callable

import college_football_api as cf_api
from college_football_rankings import iterative


class NoGameError(Exception):
    """ This team didn't play this week: """


def get_all_games_data(year: int) -> Sequence[Dict[str, Any]]:
    """
    Get all games data.

    Args:
        year: Season year.

    Returns:
        Sequence of dictionaries with each game data.
    """
    api = cf_api.CollegeFootballAPI()
    return api.games(year=year, season_type="regular")


def get_all_teams_data(year: int) -> Sequence[Dict[str, Any]]:
    """
    Get all teams data.

    Args:
        year: Season year.

    Returns:
        Sequence of dictionaries with each FBS team data.
    """
    api = cf_api.CollegeFootballAPI()
    return api.teams(year=year)


def get_all_teams_names(year: int) -> Sequence[str]:
    """
    Get all teams names.

    Args:
        year: Season year.

    Returns:
        Sequence of FBS teams names.
    """
    return [data["school"] for data in get_all_teams_data(year)]


def get_all_teams_logos(year: int) -> Dict[str, str]:
    """
    Get all teams logo.

    Args:
        year: Season year.

    Returns:
        Sequence of FBS teams logo URL.
    """
    return {data["school"]: data["logos"][0] for data in get_all_teams_data(year)}


def create_teams_schedule_dict(
    games: Sequence[Dict[str, Any]]
) -> Dict[str, Dict[int, Tuple[Optional[str], Optional[Tuple[int, int]]]]]:
    """
    Create teams schedules dictionary.

    Args:
        games: Games data.

    Returns:
        Teams schedules dictionary.
    """
    teams_dict: Dict[str, Dict[int, Tuple[Optional[str], Optional[int]]]] = {}
    last_week = 0  # Measure the last week from season.
    for game in games:

        week = game["week"]
        home_team = game["home_team"]
        away_team = game["away_team"]

        # Update last_week.
        if week > last_week:
            last_week = week

        # If points is None. It means the game didn't happened yet, or was cancelled.
        if game["home_points"] is not None:
            home_score = (game["home_points"], game["away_points"])
            away_score = (game["away_points"], game["home_points"])
        else:
            home_score = None
            away_score = None

        # Update dictionary if there is already an entry for this team.
        if home_team in teams_dict:
            teams_dict[home_team].update({week: (away_team, home_score)})
        else:
            teams_dict[home_team] = {week: (away_team, home_score)}

        # Do the same for away team.
        if away_team in teams_dict:
            teams_dict[away_team].update({week: (home_team, away_score)})
        else:
            teams_dict[away_team] = {week: (home_team, away_score)}

    for schedules in teams_dict.values():
        for i in range(1, last_week + 1):
            if i not in schedules:
                schedules[i] = (None, None)

    return teams_dict


def create_teams_margins_dict(
    teams_schedules: Dict[
        str, Dict[int, Tuple[Optional[str], Optional[Tuple[int, int]]]]
    ]
) -> Dict[str, Dict[int, Tuple[Optional[str], Optional[int]]]]:
    """
    Create teams margins dictionary.

    Args:
        teams_schedules: Teams schedule data.

    Returns:
        Teams margins dictionary.
    """
    teams_dict: Dict[str, Dict[int, Tuple[Optional[str], Optional[int]]]] = {}
    # Iterate through all teams.
    for team, schedules in teams_schedules.items():
        margins: Dict[int, Tuple[Optional[str], Optional[int]]] = {}
        # Calculates margin.
        for week, data in schedules.items():
            rival, score = data  # Unpack
            if score is not None:
                margins[week] = (rival, score[0] - score[-1])
            else:
                margins[week] = data
        teams_dict[team] = margins

    return teams_dict


def filter_week(
    teams_margins: Dict[str, Dict[int, Tuple[Optional[str], Optional[int]]]], week: int,
):
    """
    Erase data from every week after the one specified.

    Args:
        teams_margins: Each team's margins.
        week: Max week to keep.

    Returns:
        Margins with weeks above the limit erased.
    """
    for margins in teams_margins.values():
        for game_week in margins.keys():
            if game_week > week:
                rival = margins[game_week][0]
                margins[game_week] = (rival, None)


def evaluate(
    teams_margins: Dict[str, Dict[int, Tuple[Optional[str], Optional[int]]]],
    func: Callable,
    *args,
    **kwargs,
) -> List[str]:
    """
    Evaluate rankings.

    Args:
        teams_margins: Teams margins.
        func: Function to evaluate teams power.
        args: Positional argument from func.
        kwargs: Keyword arguments from func.

    Returns:
        Teams rankings.
    """
    # Run power function;
    teams_power = func(teams_margins, *args, **kwargs)

    # Unpack and sort teams.
    teams = list(teams_power.keys())
    power = list(teams_power.values())
    return [team for _, team in sorted(zip(power, teams), reverse=True)]


def create_records_dict(
    teams_margins: Dict[str, Dict[int, Tuple[Optional[str], Optional[int]]]]
) -> Dict[str, str]:
    """
    Create dictionary with each team's aggregate records.

    Args:
        teams_margins: Each team's margins for every game.

    Returns:
        Dictionary with team as key and aggregated records as vale.
    """
    records_dict: Dict[str, str] = {}
    for name, margins in teams_margins.items():
        n_wins = sum([1 for game in margins.values() if game[-1] and game[-1] > 0])
        n_loses = sum([1 for game in margins.values() if game[-1] and game[-1] < 0])
        records_dict.update({name: f"{n_wins}-{n_loses}"})
    return records_dict
