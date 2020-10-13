"""
College football high level API.

Powered by collegefootballdata.com
"""

from typing import Any, Dict, Optional, Sequence

import requests


class CollegeFootballAPI:
    """ College Football API. """

    _path = r"https://api.collegefootballdata.com/"

    def games(
        self,
        year: int,
        week: Optional[int] = None,
        season_type: Optional[str] = None,
        team: Optional[str] = None,
        home: Optional[str] = None,
        away: Optional[str] = None,
        conference: Optional[str] = None,
    ) -> Sequence[Dict[str, Any]]:
        """
        Get games data.

        Args:
            year: Season year.
            week: Week number. None to get all.
            season_type: Season type. Accepts 'regular', 'postseason' or 'both'.
                None to get all.
            team: Team name. None to get all.
            home: Home team name. None to get all.
            away: Away team name. None to get all.
            conference: Conference name. None to get all.

        Returns:
            Sequence of dictionaries with requested games data.
        """
        kwargs: Dict[str, Any] = {
            "week": week,
            "seasonType": season_type,
            "team": team,
            "home": home,
            "away": away,
            "conference": conference,
        }
        url = f"{self._path}games?year={year}"  # Always include year.
        for key, val in kwargs.items():
            if val is None:
                continue  # Ignore if None.
            url += f"&{key}={val}"
        req = requests.get(url, params={"accept": "application/json"}, verify=False)
        return req.json()

    def teams(self, year: int) -> Sequence[Dict[str, Any]]:
        """
        Get teams data.

        Args:
            year: Season year.

        Returns:
            Sequence of dictionaries with requested teams data.
        """
        url = f"{self._path}teams/fbs?year={year}"  # Always include year.
        req = requests.get(url, params={"accept": "application/json"}, verify=False)
        return req.json()

    def rankings(
        self, year: int, week: Optional[int] = None, season_type: Optional[str] = None,
    ) -> Sequence[Dict[str, Any]]:
        """
        Get games data.

        Args:
            year: Season year.
            week: Week number. None to get all.
            season_type: Season type. Accepts 'regular', 'postseason' or 'both'.
                None to get all.

        Returns:
            Sequence of dictionaries with requested games data.
        """
        kwargs: Dict[str, Any] = {
            "week": week,
            "seasonType": season_type,
        }
        url = f"{self._path}rankings?year={year}"  # Always include year.
        for key, val in kwargs.items():
            if val is None:
                continue  # Ignore if None.
            url += f"&{key}={val}"
        req = requests.get(url, params={"accept": "application/json"}, verify=False)
        return req.json()
