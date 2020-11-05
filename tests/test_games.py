""" Test college_rankings_class.Game class and auxiliary functions. """

import college_football_rankings as cfr


class TestWeeks:
    """ Test iterative ranking algorithm. """

    @classmethod
    def setup_class(cls):
        """ Get teams and games. """
        year = 2017
        cls.games = cfr.get_games(year, season_type="both")

    def test_last_played_week(self):
        """ Test last played week. """
        assert cfr.last_played_week(games=self.games) == 16
