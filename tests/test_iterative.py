""" Unit tests for the college_football_rankings.iterative module. """

import college_football_rankings
from college_football_rankings import iterative


class TestIterative:
    """ Test iterative ranking algorithm. """

    @classmethod
    def setup_class(cls):
        """ Get teams and games. """
        year = 2019
        teams = college_football_rankings.get_teams()
        teams = college_football_rankings.create_teams_instances(teams)
        games = college_football_rankings.get_games(year)
        college_football_rankings.fill_schedules(games, teams)
        # Remove teams that won't play any game.
        cls.teams = {
            name: team
            for name, team in teams.items()
            if team.schedule.n_played_games > 0
        }

    def test_power_not_consider_margin(self):
        """ Test power function when it does not consider points margin. """
        iterative.power(self.teams, consider_margin=False, random_state=0)
        assert self.teams["LSU"].power == 1

    def test_ranking_not_consider_margin(self):
        """ Test power function when it considers points margin. """
        ranking = college_football_rankings.evaluate(
            teams=self.teams,
            func=iterative.power,
            consider_margin=False,
            random_state=0,
        )
        assert ranking[0].name == "LSU"
