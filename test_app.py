import unittest

from app import GAMES, app


class GameApiTests(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()

    def start_game(self, difficulty="medium"):
        return self.client.post("/api/new-game", json={"difficulty": difficulty})

    def test_new_game_uses_selected_difficulty(self):
        for difficulty, length, attempts in (
            ("easy", 3, 10),
            ("medium", 4, 10),
            ("hard", 5, 8),
        ):
            with self.subTest(difficulty=difficulty):
                response = self.start_game(difficulty)
                self.assertEqual(response.status_code, 201)
                game = response.get_json()["game"]
                self.assertEqual(game["length"], length)
                self.assertEqual(game["max_attempts"], attempts)
                self.assertEqual(game["status"], "playing")
                self.assertNotIn("secret", game)
                with self.client.session_transaction() as browser_session:
                    self.assertNotIn("game", browser_session)

    def test_invalid_guess_does_not_consume_attempt(self):
        self.start_game()
        response = self.client.post("/api/guess", json={"guess": "1123"})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json()["error"], "Each digit must be different.")

        with self.client.session_transaction() as browser_session:
            game = GAMES[browser_session["game_id"]]
            self.assertEqual(game["attempts"], 0)

    def test_guess_feedback_and_win(self):
        self.start_game()
        with self.client.session_transaction() as browser_session:
            game = GAMES[browser_session["game_id"]]
            game["secret"] = "1234"

        response = self.client.post("/api/guess", json={"guess": "1243"})
        data = response.get_json()
        self.assertEqual(data["feedback"], ["C", "C", "W", "W"])
        self.assertEqual(data["game"]["status"], "playing")
        self.assertNotIn("secret", data["game"])

        response = self.client.post("/api/guess", json={"guess": "1234"})
        game = response.get_json()["game"]
        self.assertEqual(game["status"], "won")
        self.assertEqual(game["secret"], "1234")

    def test_game_state_restores_guess_history(self):
        self.start_game()
        with self.client.session_transaction() as browser_session:
            game = GAMES[browser_session["game_id"]]
            game["secret"] = "1234"

        self.client.post("/api/guess", json={"guess": "1243"})
        response = self.client.get("/api/state")
        history = response.get_json()["game"]["history"]
        self.assertEqual(history, [{"guess": "1243", "feedback": ["C", "C", "W", "W"]}])

    def test_game_over_reveals_code_and_rejects_more_guesses(self):
        self.start_game()
        with self.client.session_transaction() as browser_session:
            game = GAMES[browser_session["game_id"]]
            game.update(secret="1234", attempts=9)

        response = self.client.post("/api/guess", json={"guess": "5678"})
        self.assertEqual(response.get_json()["game"]["status"], "lost")
        self.assertEqual(response.get_json()["game"]["secret"], "1234")

        response = self.client.post("/api/guess", json={"guess": "5678"})
        self.assertEqual(response.status_code, 409)

    def test_page_renders(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Break the code", response.data)


if __name__ == "__main__":
    unittest.main()
