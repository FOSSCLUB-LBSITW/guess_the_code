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

    def test_hint_reveals_new_digit_without_its_position_and_consumes_attempt(self):
        self.start_game()
        with self.client.session_transaction() as browser_session:
            game = GAMES[browser_session["game_id"]]
            game["secret"] = "1234"

        revealed_digits = set()
        for expected_count in (1, 2):
            response = self.client.post("/api/hint", json={})
            data = response.get_json()
            self.assertEqual(response.status_code, 200)
            self.assertIn("The code contains the digit ", data["hint"])
            digit = data["hint"].split("digit ")[1][0]
            self.assertIn(digit, "1234")
            self.assertNotIn(digit, revealed_digits)
            self.assertEqual(data["game"]["attempts"], expected_count)
            self.assertEqual(data["game"]["hint_count"], expected_count)
            self.assertEqual(len(data["game"]["hints"]), expected_count)
            self.assertNotIn("secret", data["game"])
            revealed_digits.add(digit)

        self.start_game("easy")
        game = self.client.get("/api/state").get_json()["game"]
        self.assertEqual(game["hint_count"], 0)
        self.assertEqual(game["hints"], [])

    def test_hint_skips_digits_already_proven_by_guess_feedback(self):
        self.start_game()
        with self.client.session_transaction() as browser_session:
            GAMES[browser_session["game_id"]]["secret"] = "1234"

        guess_response = self.client.post("/api/guess", json={"guess": "1456"})
        self.assertEqual(guess_response.get_json()["feedback"], ["C", "W", "X", "X"])

        response = self.client.post("/api/hint", json={})
        data = response.get_json()
        digit = data["hint"].split("digit ")[1][0]
        self.assertIn(digit, "23")
        self.assertEqual(data["game"]["hint_available"], True)

    def test_hint_is_unavailable_when_all_secret_digits_are_already_known(self):
        self.start_game()
        with self.client.session_transaction() as browser_session:
            GAMES[browser_session["game_id"]]["secret"] = "1234"

        self.client.post("/api/guess", json={"guess": "4321"})
        response = self.client.get("/api/state")
        game = response.get_json()["game"]
        self.assertFalse(game["hint_available"])

        response = self.client.post("/api/hint", json={})
        self.assertEqual(response.status_code, 409)
        game = self.client.get("/api/state").get_json()["game"]
        self.assertEqual(game["attempts"], 1)
        self.assertEqual(game["hint_count"], 0)

    def test_hint_on_last_attempt_ends_the_game(self):
        self.start_game()
        with self.client.session_transaction() as browser_session:
            game = GAMES[browser_session["game_id"]]
            game.update(secret="1234", attempts=9)

        response = self.client.post("/api/hint", json={})
        game = response.get_json()["game"]
        self.assertEqual(game["attempts"], game["max_attempts"])
        self.assertEqual(game["status"], "lost")
        self.assertEqual(game["secret"], "1234")
        self.assertEqual(game["hint_count"], 1)

        response = self.client.post("/api/hint", json={})
        self.assertEqual(response.status_code, 409)

    def test_hints_stop_when_all_code_digits_have_been_revealed(self):
        self.start_game()
        with self.client.session_transaction() as browser_session:
            GAMES[browser_session["game_id"]]["secret"] = "1234"

        for _ in range(4):
            response = self.client.post("/api/hint", json={})
            self.assertEqual(response.status_code, 200)

        response = self.client.post("/api/hint", json={})
        self.assertEqual(response.status_code, 409)
        game = self.client.get("/api/state").get_json()["game"]
        self.assertEqual(game["attempts"], 4)
        self.assertEqual(game["hint_count"], 4)
        self.assertEqual(game["status"], "playing")

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

        response = self.client.post("/api/hint", json={})
        self.assertEqual(response.status_code, 409)

    def test_page_renders(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Break the code", response.data)


if __name__ == "__main__":
    unittest.main()
