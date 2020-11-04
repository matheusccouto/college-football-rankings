"""
Estimate college football rankings.
"""
import dataclasses
from typing import Callable, Dict, List, Optional, Sequence

import cfbd


@dataclasses.dataclass
class Game:
    """ Game data."""

    season: int
    week: int
    season_type: str
    start_date: str
    start_time_tbd: bool
    neutral_site: bool
    conference_game: bool
    attendance: int
    venue: str
    team_points: int
    team_line_scores: List[int]
    team_post_win_prob: float
    opponent: str
    opponent_conference: str
    opponent_points: int
    opponent_line_scores: List[int]
    opponent_post_win_prob: float
    excitement_index: float

    @property
    def margin(self) -> Optional[int]:
        """ Score margin. """
        if self.team_points is None or self.opponent_points is None:
            return None
        return self.team_points - self.opponent_points


class Schedule:
    """ Team's schedule. """

    def __init__(self, team: str):
        self.team = team
        self.games: List[Game] = []

    @property
    def n_played_games(self):
        """ Number of already played games this season. """
        return len([game for game in self.games if game.team_points is not None])

    @property
    def n_games(self):
        """ Number of games this season. """
        return len(self.games)

    def filter_score(self, max_week: int):
        """ Clear schedule games score. """
        for game in self.games:
            if game.week > max_week:
                game.team_points = None
                game.team_line_scores = None
                game.team_post_win_prob = None
                game.opponent_points = None
                game.opponent_line_scores = None
                game.opponent_post_win_prob = None
                game.attendance = None
                game.excitement_index = None

    def add_game(self, game: cfbd.Game):
        """ Add games to schedule. """
        if game.home_team == self.team:
            team_points = game.home_points
            team_line_scores = game.home_line_scores
            team_post_win_prob = game.home_post_win_prob
            opponent = game.away_team
            opponent_conference = game.away_conference
            opponent_points = game.away_points
            opponent_line_scores = game.away_line_scores
            opponent_post_win_prob = game.away_post_win_prob
        else:
            team_points = game.away_points
            team_line_scores = game.away_line_scores
            team_post_win_prob = game.away_post_win_prob
            opponent = game.home_team
            opponent_conference = game.home_conference
            opponent_points = game.home_points
            opponent_line_scores = game.home_line_scores
            opponent_post_win_prob = game.home_post_win_prob

        game_pov = Game(
            season=game.season,
            week=game.week,
            season_type=game.season_type,
            start_date=game.start_date,
            start_time_tbd=game.start_time_tbd,
            neutral_site=game.neutral_site,
            conference_game=game.conference_game,
            attendance=game.attendance,
            venue=game.venue,
            team_points=team_points,
            team_line_scores=team_line_scores,
            team_post_win_prob=team_post_win_prob,
            opponent=opponent,
            opponent_conference=opponent_conference,
            opponent_points=opponent_points,
            opponent_line_scores=opponent_line_scores,
            opponent_post_win_prob=opponent_post_win_prob,
            excitement_index=game.excitement_index,
        )
        self.games.append(game_pov)
        self.games = list(sorted(self.games, key=lambda x: x.start_date))


class Team:
    """ Team object. """

    def __init__(
        self,
        name: str,
        logos: Optional[List[str]] = None,
        alt_name: Optional[str] = None,
    ):
        self.name = name
        self.alt_name = alt_name
        self.power = 0
        self.schedule = Schedule(name)

        if logos:
            self.logo_light = logos[0]
            self.logo_dark = logos[1]
        else:
            self.logo_light = None
            self.logo_dark = None

    def __repr__(self) -> str:
        return self.name

    @property
    def wins(self) -> int:
        """ Get number of wins."""
        return len(
            [
                game
                for game in self.schedule.games
                if game.margin is not None and game.margin > 0
            ]
        )

    @property
    def draws(self) -> int:
        """ Get number of draws."""
        return len(
            [
                game
                for game in self.schedule.games
                if game.margin is not None and game.margin == 0
            ]
        )

    @property
    def losses(self) -> int:
        """ Get number of losses."""
        return len(
            [
                game
                for game in self.schedule.games
                if game.margin is not None and game.margin < 0
            ]
        )

    @property
    def record(self) -> str:
        """ Get team record. """
        wins = str(self.wins)
        draws = str(self.draws)
        losses = str(self.losses)
        if draws:
            "-".join([wins, draws, losses])
        return "-".join([wins, losses])


class Ranking:
    """ Yearly rankings. """

    def __init__(self, name: str):
        self.name = name
        self._rankings: Dict[int, List[str]] = {}

    def add_week(self, week: int, rankings: Sequence[str]):
        """ Add weekly rankings. """
        self._rankings[week] = list(rankings)

    def get_week(self, week: int) -> List[str]:
        """ Get rankings from an specified week. """
        if week not in self._rankings:
            return []
        return self._rankings[week]

    def team_position(self, team: str, week: int) -> Optional[int]:
        """ Get team position in a specific week. """
        if week not in self._rankings:
            return None
        if team not in self._rankings[week]:
            return None
        return self._rankings[week].index(team) + 1

    def team_history(self, team: str) -> List[Optional[int]]:
        """ Team ranking history. """
        return [self.team_position(team, week) for week in self._rankings]


def get_games(*args, **kwargs) -> List[cfbd.Game]:
    """ Get games data. """
    config = cfbd.Configuration()
    config.verify_ssl = False
    api = cfbd.GamesApi(cfbd.ApiClient(config))
    return api.get_games(*args, **kwargs)


def get_teams(**kwargs) -> List[cfbd.Team]:
    """ Get teams data. """
    config = cfbd.Configuration()
    config.verify_ssl = False
    api = cfbd.TeamsApi(cfbd.ApiClient(config))
    return api.get_teams(**kwargs)


def get_rankings(*args, **kwargs) -> List[cfbd.RankingWeek]:
    """ Get rankings data. """
    config = cfbd.Configuration()
    config.verify_ssl = False
    api = cfbd.RankingsApi(cfbd.ApiClient(config))
    return api.get_rankings(*args, **kwargs)


def create_teams_instances(teams: List[cfbd.Team]) -> Dict[str, Team]:
    """ Create FPS teams instance. """
    return {team.school: Team(team.school, team.logos) for team in teams}


def clean_scores(teams: Dict[str, Team], max_week: int):
    """ Clear all teams schedules. """
    for team in teams.values():
        team.schedule.filter_score(max_week)


def fill_schedules(
    games: List[cfbd.Game], teams: Dict[str, Team],
):
    """ Fill all teams schedules with games. """
    for game in games:
        teams[game.home_team].schedule.add_game(game)
        teams[game.away_team].schedule.add_game(game)


def filter_schedules(teams: Dict[str, Team], max_week: int):
    """ Filter data from played games up to a specified wek.. """
    for team in teams.values():
        team.schedule.filter_score(max_week)


def clean_teams(teams: Dict[str, Team]) -> Dict[str, Team]:
    """ Remove entries that didn't play a single game that season. """
    return {name: team for name, team in teams.items() if team.schedule.n_games > 0}


def last_played_week(games: List[cfbd.Game]) -> int:
    """ Get last played week. """
    last_regular_week = 0
    last_off_season_week = 0

    for game in games:

        if game.home_points is None:
            continue

        if "regular" in game.season_type:
            if game.week > last_regular_week:
                last_regular_week = game.week

        else:
            if game.week > last_off_season_week:
                last_off_season_week = game.week

    return last_regular_week + last_off_season_week


def create_polls(year: int, max_week: Optional[int] = None) -> Dict[str, Ranking]:
    """ Create polls instances. """
    week_list = get_rankings(year=year)

    # Create instances.
    instances = {
        "Playoff Committee Rankings": Ranking(name="Playoff Committee Rankings"),
        "AP Top 25": Ranking(name="AP Top 25"),
        "Coaches Poll": Ranking(name="Coaches Poll"),
    }

    for week in week_list:

        week_number = week.week - 1
        if max_week:
            if week_number > max_week:
                return instances

        for poll in week.polls:
            if poll.poll in instances:
                ranks = {rank.rank: rank.school for rank in poll.ranks}
                ranks = [ranks[rank] for rank in sorted(ranks)]
                instances[poll.poll].add_week(week_number, ranks)

    return instances


class RankingError(Exception):
    """ Exception that indicates that something prevented ranking calculation. """


def evaluate(teams: Dict[str, Team], func: Callable, *args, **kwargs) -> List[Team]:
    """ Evaluate rankings. """
    func(teams, *args, **kwargs)
    return list(sorted(teams.values(), key=lambda obj: obj.power, reverse=True))


def set_week_and_eval(
    week: int, teams: Dict[str, Team], func: Callable, *args, **kwargs
) -> List[Team]:
    """ Set games for an specific week and evaluate. """
    filter_schedules(teams=teams, max_week=week)
    # teams = clean_teams(teams=teams)
    return evaluate(teams, func, *args, **kwargs)
