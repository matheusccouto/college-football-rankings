""" Iterative method for estimating teams power. """

from typing import Any, Dict, Tuple, Optional

import numpy as np


class EquilibriumError(Exception):
    """ No equilibrium available. """


def norm(dict_: Dict[Any, float]):
    """
    Normalize dictionary values.

    Args:
        dict_: Dictionary. Values must be numbers.

    Returns:
        Dictionary with normalized values.
    """
    max_val = max(list(dict_.values()))
    min_val = min(list(dict_.values()))
    diff = max_val - min_val
    if diff == 0:
        return {name: 0.5 for name in dict_.keys()}
    return {key: (val - min_val) / diff for key, val in dict_.items()}


def max_val_diff(dict1: Dict[Any, float], dict2: Dict[Any, float]) -> float:
    """
    Calculate the max difference between two dictionaries values.

    Args:
        dict1: Dictionary 1.
        dict2: Dictionary 2.

    Returns:
        Max difference.
    """
    d1_values = dict1.values()
    d2_values = dict2.values()
    return max([abs(d1_val - d2_val) for d1_val, d2_val in zip(d1_values, d2_values)])


def power(
    teams_records: Dict[str, Dict[int, Tuple[Optional[str], Optional[int]]]],
    score: bool = False,
    random_state: Optional[int] = None,
) -> Dict[str, float]:
    """
    Iterative algorithm to evaluate teams power.

    Args:
        teams_records: Game records from each team.
        score: Consider points difference or simple if won or lost.
        random_state: Random state for initial values.

    Returns:
        Dictionary where the key is the team name and value is its power.
    """
    # Random state.
    rnd = np.random.RandomState(random_state)

    for _ in range(3):  # Number of tries to find Nash Equilibrium

        # Create a dict with each team name as key and initial power value
        teams_power = {name: rnd.random() for name in teams_records.keys()}

        # Duplicate this dictionary so old values do not mix with new ones.
        new_teams_power = teams_power.copy()

        for _ in range(100):  # Number of tries.

            # Evaluate each team records considering the power from the rival it faced.
            for name in teams_power.keys():

                team_records = teams_records[name]  # Select team.
                new_teams_power[name] = 0  # Initial value.

                # Iterates over weeks.
                for rival, balance in team_records.values():

                    # If the team played this week, than evaluate how many points it
                    # gains or lose based on the game results.
                    if balance is not None:

                        if not score:
                            # Disregard the amount of points difference in the score.
                            balance = np.clip(balance, -1, 1)

                        # Sum power (or decrease) power points.
                        if balance > 0:
                            # If it beats a high power opponent, it wins more points.
                            new_teams_power[name] += teams_power[rival] * balance
                        else:
                            # If it loses to a low power opponent, it loses more points.
                            new_teams_power[name] += (1 - teams_power[rival]) * balance

            # Normalize values.
            new_teams_power = norm(new_teams_power)

            # If values are stable enough, stop iteration.
            if max_val_diff(teams_power, new_teams_power) < 1e-6:
                return new_teams_power

            # Apply new values over old values.
            teams_power = new_teams_power.copy()

    # When running out of tries.
    raise EquilibriumError("Not enough games to find Equilibrium")
