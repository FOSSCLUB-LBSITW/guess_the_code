import os
import secrets

from flask import Flask, jsonify, render_template, request, session

from guess_the_code import check_guess, generate_code


DIFFICULTIES = {
    "easy": {"length": 3, "max_attempts": 10},
    "medium": {"length": 4, "max_attempts": 10},
    "hard": {"length": 5, "max_attempts": 8},
}

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY") or secrets.token_hex(32)
GAMES = {}


def current_game():
    game_id = session.get("game_id")
    return GAMES.get(game_id)


def game_response(feedback=None):
    game = current_game()
    if game is None:
        return {"game": None}

    response = {
        "game": {
            "difficulty": game["difficulty"],
            "length": game["length"],
            "attempts": game["attempts"],
            "max_attempts": game["max_attempts"],
            "status": game["status"],
            "history": game.get("history", []),
        }
    }
    if feedback is not None:
        response["feedback"] = feedback
    if game["status"] in ("won", "lost"):
        response["game"]["secret"] = game["secret"]
    return response


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/api/state")
def get_state():
    return jsonify(game_response())


@app.post("/api/new-game")
def new_game():
    if not request.is_json:
        return jsonify(error="Expected a JSON request."), 400

    payload = request.get_json()
    difficulty = payload.get("difficulty", "medium") if isinstance(payload, dict) else None
    if difficulty not in DIFFICULTIES:
        return jsonify(error="Choose easy, medium, or hard difficulty."), 400

    settings = DIFFICULTIES[difficulty]
    previous_game_id = session.get("game_id")
    if previous_game_id is not None:
        GAMES.pop(previous_game_id, None)

    game_id = secrets.token_urlsafe(16)
    GAMES[game_id] = {
        "difficulty": difficulty,
        "length": settings["length"],
        "max_attempts": settings["max_attempts"],
        "attempts": 0,
        "history": [],
        "secret": generate_code(settings["length"]),
        "status": "playing",
    }
    session["game_id"] = game_id
    return jsonify(game_response()), 201


@app.post("/api/guess")
def submit_guess():
    if not request.is_json:
        return jsonify(error="Expected a JSON request."), 400

    payload = request.get_json()
    guess = payload.get("guess") if isinstance(payload, dict) else None
    game = current_game()
    if game is None:
        return jsonify(error="Start a new game before guessing."), 409
    if game["status"] != "playing":
        return jsonify(error="This game is over. Start a new game to play again."), 409
    if not isinstance(guess, str) or not guess.isascii() or not guess.isdigit():
        return jsonify(error="Enter numbers only."), 400
    if len(guess) != game["length"]:
        return jsonify(error=f"Enter exactly {game['length']} digits."), 400
    if len(set(guess)) != len(guess):
        return jsonify(error="Each digit must be different."), 400

    game.setdefault("history", [])
    game["attempts"] += 1
    feedback = check_guess(game["secret"], guess)
    game["history"].append({"guess": guess, "feedback": feedback})
    if guess == game["secret"]:
        game["status"] = "won"
    elif game["attempts"] >= game["max_attempts"]:
        game["status"] = "lost"
    return jsonify(game_response(feedback))


if __name__ == "__main__":
    app.run()
