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
        Sequence of dictionaries with each FBS team data.
    """
    return [data["school"] for data in get_all_teams_data(year)]


def create_teams_records_dict(
    games: Sequence[Dict[str, Any]]
) -> Dict[str, Dict[int, Tuple[Optional[str], Optional[int]]]]:
    """
    Create teams records dictionary.

    Args:
        games:

    Returns:
        Teams records dictionary.
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
            home_points_diff = game["home_points"] - game["away_points"]
            away_points_diff = game["away_points"] - game["home_points"]
        else:
            home_points_diff = None
            away_points_diff = None

        # Update dictionary if there is already an entry for this team.
        if home_team in teams_dict:
            teams_dict[home_team].update({week: (away_team, home_points_diff)})
        else:
            teams_dict[home_team] = {week: (away_team, home_points_diff)}

        # Do the same for away team.
        if away_team in teams_dict:
            teams_dict[away_team].update({week: (home_team, away_points_diff)})
        else:
            teams_dict[away_team] = {week: (home_team, away_points_diff)}

    for records in teams_dict.values():
        for i in range(1, last_week + 1):
            if i not in records:
                records[i] = (None, None)

    return teams_dict


def prepare_data(
    games: Sequence[Dict[str, Any]], week: int
) -> Dict[str, Dict[int, Tuple[Optional[str], Optional[int]]]]:
    """
    Transform game records into team's records.

    Args:
        games: Games data.
        week: Max week to consider.

    Returns:
        Each team's ecord.
    """
    teams_records = create_teams_records_dict(games)
    filter_week(teams_records=teams_records, week=week)
    return teams_records


def filter_week(
    teams_records: Dict[str, Dict[int, Tuple[Optional[str], Optional[int]]]], week: int,
):
    """
    Erase data from every week after the one specified.

    Args:
        teams_records: Each team's records.
        week: Max week to keep.

    Returns:
        Records with weeks above the limit erased.
    """
    for records in teams_records.values():
        for game_week in records.keys():
            if game_week > week:
                records[game_week] = (None, None)


def evaluate(
    teams_records: Dict[str, Dict[int, Tuple[Optional[str], Optional[int]]]],
    func: Callable,
    *args,
    **kwargs,
) -> List[str]:
    """
    Evaluate rankings.

    Args:
        teams_records: Teams records.
        func: Function to evaluate teams power.
        args: Positional argument from func.
        kwargs: Keyword arguments from func.

    Returns:
        Teams rankings.
    """
    # Run power function;
    teams_power = func(teams_records, *args, **kwargs)

    # Unpack and sort teams.
    teams = list(teams_power.keys())
    power = list(teams_power.values())
    return [team for _, team in sorted(zip(power, teams), reverse=True)]


def create_records_dict(
    teams_records: Dict[str, Dict[int, Tuple[Optional[str], Optional[int]]]]
) -> Dict[str, str]:
    """
    Create dictionary with each team's aggregate records.

    Args:
        teams_records: Each team's records.

    Returns:
        Dictionary with team as key and aggregated records as vale.
    """
    records_dict: Dict[str, str] = {}
    for name, records in teams_records.items():
        n_wins = sum([1 for game in records.values() if game[-1] and game[-1] > 0])
        n_loses = sum([1 for game in records.values() if game[-1] and game[-1] < 0])
        records_dict.update({name: f"{n_wins}-{n_loses}"})
    return records_dict
