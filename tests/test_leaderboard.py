import unittest

from cogs.adventure import Adventure, LeaderboardView


class FakeContext:
    author = type("Author", (), {"id": 123})()


class LeaderboardViewTests(unittest.TestCase):
    def test_leaderboard_shows_symbolic_xp_and_ascension(self):
        cog = Adventure.__new__(Adventure)
        entries = [
            ("456", {
                "level": 900,
                "xp": 1200,
                "ascension": 5,
                "symbolic_rewards": {"xp": 1},
            })
        ]
        view = LeaderboardView(cog, FakeContext(), entries)
        embed = view.build_embed()
        self.assertIn("10^(10^100)", embed.description)
        self.assertIn("Ascension 5", embed.description)
        self.assertTrue(view.previous.disabled)
        self.assertTrue(view.next.disabled)

    def test_leaderboard_pages_ten_players_at_a_time(self):
        cog = Adventure.__new__(Adventure)
        entries = [
            (str(index), {"level": index, "xp": index * 10, "symbolic_rewards": {}})
            for index in range(12)
        ]
        view = LeaderboardView(cog, FakeContext(), entries)
        first = view.build_embed().description
        self.assertIn("1.", first)
        self.assertIn("10.", first)
        self.assertNotIn("11.", first)

        view.page = 1
        view.refresh()
        second = view.build_embed().description
        self.assertIn("11.", second)
        self.assertIn("12.", second)
        self.assertTrue(view.next.disabled)


if __name__ == "__main__":
    unittest.main()
