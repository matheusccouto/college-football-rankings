""" Iterative method for estimating teams power. """

from typing import Any, Dict, Optional

import numpy as np

import college_football_rankings as cfr


class EquilibriumError(Exception):
    """ No equilibrium available. """


def norm(dict_: Dict[Any, float]):
    """ Normalize dictionary values. """
    max_val = max(list(dict_.values()))
    min_val = min(list(dict_.values()))
    diff = max_val - min_val
    if diff == 0:
        return {name: 0.5 for name in dict_.keys()}
    return {key: (val - min_val) / diff for key, val in dict_.items()}


def max_val_diff(dict1: Dict[Any, float], dict2: Dict[Any, float]) -> float:
    """ Calculate the max difference between two dictionaries values. """
    d1_values = dict1.values()
    d2_values = dict2.values()
    return max([abs(d1_val - d2_val) for d1_val, d2_val in zip(d1_values, d2_values)])


def clip(val, min_val, max_val):
    """ Clip value in between specified values. """
    if val > max_val:
        return max_val
    if val < min_val:
        return min_val
    return val


def power(
    teams: Dict[str, cfr.Team],
    consider_margin: bool = False,
    consider_post_win_prob: bool = False,
    random_state: Optional[int] = None,
):
    """ Iterative algorithm to evaluate teams power. """

    # Define random state.
    rnd = np.random.RandomState(random_state)

    # Initialize random power values.
    for team in teams.values():
        # Random values from 0.4 to 0.6.
        team.power = 0.4 + rnd.random() / 10

    for _ in range(100):  # Number of tries.

        # Record current powers in a dict to compare with futures and know when it is
        # ok to stop the iteration.
        current_teams_power = {name: team.power for name, team in teams.items()}

        # Record new calculated powers in a dict to apply only after all team's power
        # have been calculate.
        future_teams_power: Dict[str, float] = {}

        # Iterate over Team instances.
        for name, team in teams.items():

            future_teams_power[name] = 0  # Initial value.

            for game in team.schedule.games:

                # Skip if the game was not played.
                margin = game.margin
                if margin is None:
                    continue

                if not consider_margin:
                    margin = clip(margin, -1, 1)

                if consider_post_win_prob and game.team_post_win_prob is not None:
                    margin *= game.team_post_win_prob

                opponent_power = teams[game.opponent].power

                # Sum (or decrease) power points.
                if margin > 0:
                    # If it beats a high power opponent, it wins more points.
                    future_teams_power[name] += opponent_power * margin
                else:
                    # If it loses to a low power opponent, it loses more points.
                    future_teams_power[name] += (1 - opponent_power) * margin

        # Normalize values.
        future_teams_power_norm = norm(future_teams_power)

        # Apply calculated power.
        for name, team in teams.items():
            team.power = future_teams_power_norm[name]

        # If values are stable enough, stop iteration.
        if max_val_diff(current_teams_power, future_teams_power_norm) < 1e-6:
            return

    # When running out of tries.
    raise cfr.RankingError("Not enough games played to find equilibrium")
