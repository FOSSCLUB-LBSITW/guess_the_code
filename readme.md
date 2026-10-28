# Guess the Code

Guess the Code is a digit guessing game. Crack the secret code using clues that show whether each digit is in the correct position, in the wrong position, or not present.

## Run the web app

Requires Python 3.10 or later.

1. Install the dependencies:
   ```bash
   python -m pip install -r requirements.txt
   ```
2. Set a persistent Flask session key for deployment (recommended):
   ```bash
   # macOS/Linux
   export FLASK_SECRET_KEY="replace-with-a-long-random-value"
   ```
   ```powershell
   # Windows PowerShell
   $env:FLASK_SECRET_KEY = "replace-with-a-long-random-value"
   ```
3. Start the server:
   ```bash
   python app.py
   ```
4. Open http://127.0.0.1:5000.

The web game offers Easy (3 digits, 10 attempts), Medium (4 digits, 10 attempts), and Hard (5 digits, 8 attempts). Codes and guesses use unique digits. The original terminal version remains available with `python guess_the_code.py`.

Active games are held in server memory, so restarting the app clears them. Use a single application process with this in-memory game store.

Run the API and game tests with:

```bash
python -m unittest
```

## Requirement
Fork this repository and make your changes in your fork.
Deploy your modified project and make sure it is publicly accessible.
Your fork and your deployed version should correspond to the code you are submitting.
**Include the live deployed link in _About_ of the forked repo.**
The deployed link will be checked before the PR is reviewed/merged.
