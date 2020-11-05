""" Test college_football_rankings Team class and auxiliary functions. """

import college_football_rankings


class TestCreateTeamsInstances:
    """ Test create_teams_instances function."""

    @staticmethod
    def test_len():
        """ Test return length. """
        teams = college_football_rankings.get_teams()
        assert len(college_football_rankings.create_teams_instances(teams)) == 1665

    @staticmethod
    def test_type():
        """ Test return length. """
        teams = college_football_rankings.get_teams()
        team = college_football_rankings.create_teams_instances(teams)["UAB"]
        assert isinstance(team, college_football_rankings.Team)


class TestFillSchedules:
    """ Test fill_schedules function. """

    @classmethod
    def setup_class(cls):
        """ Get teams and games. """
        year = 2020
        teams = college_football_rankings.get_teams()
        cls.teams = college_football_rankings.create_teams_instances(teams)
        cls.games = college_football_rankings.get_games(year)

    def test_len(self):
        """ Test length. """
        self.teams["UAB"].schedule.clear()
        college_football_rankings.fill_schedules(self.games, self.teams)
        assert len(self.teams["UAB"].schedule.games) > 0

    def test_len_max_week(self):
        """ Test max_week. """
        self.teams["UAB"].schedule.clear()
        college_football_rankings.fill_schedules(self.games, self.teams, 1)
        assert len(self.teams["UAB"].schedule.games) == 1
