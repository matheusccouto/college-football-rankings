""" Test college_football_rankings polls"""

import college_football_rankings as cfr


class TestCreatePolls:
    """ Test create_polls function. """

    @classmethod
    def setup_class(cls):
        """ Setup tests. """
        cls.polls = cfr.create_polls(2020)

    def test_polls(self):
        """ Test create polls. """
        assert self.polls["AP Top 25"].get_week(7)[0] == "Clemson"

    def test_team_position(self):
        """ Test get a team weekly position. """
        assert self.polls["AP Top 25"].team_position(team="Alabama", week=7)

    def test_team_history(self):
        """ Test get a team weekly position. """
        history = self.polls["AP Top 25"].team_history(team="Alabama")
        assert history[0] == 3
        assert history[7] == 2
