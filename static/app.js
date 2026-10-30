const difficultySelect = document.querySelector("#difficulty");
const guessForm = document.querySelector("#guess-form");
const guessInput = document.querySelector("#guess-input");
const attemptCount = document.querySelector("#attempt-count");
const attemptTotal = document.querySelector("#attempt-total");
const attemptProgress = document.querySelector("#attempt-progress");
const attemptTrack = document.querySelector(".attempt-track");
const message = document.querySelector("#message");
const historyList = document.querySelector("#guess-history");
const historyEmpty = document.querySelector("#history-empty");
const restartButton = document.querySelector("#restart-button");
const submitButton = guessForm.querySelector("button");

function showMessage(text, kind = "") {
  message.textContent = text;
  message.dataset.kind = kind;
}

function updateGame(game) {
  attemptCount.textContent = game.attempts;
  attemptTotal.textContent = game.max_attempts;
  const darkness = game.status === "won"
    ? 0
    : Math.min(game.attempts / game.max_attempts, 1) * 0.72;
  document.documentElement.style.setProperty("--lighting-darkness", darkness);
  const progress = (game.attempts / game.max_attempts) * 100;
  attemptProgress.style.width = `${progress}%`;
  attemptTrack.setAttribute("aria-valuemax", game.max_attempts);
  attemptTrack.setAttribute("aria-valuenow", game.attempts);
  guessInput.maxLength = game.length;
  guessInput.placeholder = `${game.length} digits`;
  difficultySelect.value = game.difficulty;

  const isPlaying = game.status === "playing";
  guessInput.disabled = !isPlaying;
  submitButton.disabled = !isPlaying;
  difficultySelect.disabled = false;
}

function addHistory(guess, feedback) {
  historyEmpty.hidden = true;
  const item = document.createElement("li");
  const guessText = document.createElement("span");
  guessText.className = "history-guess";
  guessText.textContent = guess;

  const marks = document.createElement("span");
  marks.className = "feedback";
  marks.setAttribute("aria-label", `Clues: ${feedback.join(", ")}`);
  feedback.forEach((value) => {
    const mark = document.createElement("span");
    mark.className = `feedback-mark ${value === "C" ? "correct" : value === "W" ? "misplaced" : "absent"}`;
    mark.textContent = value;
    marks.append(mark);
  });

  item.append(guessText, marks);
  historyList.prepend(item);
}

async function postJson(url, body) {
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.error || "Something went wrong. Please try again.");
  }
  return data;
}

async function startNewGame() {
  restartButton.disabled = true;
  try {
    const data = await postJson("/api/new-game", { difficulty: difficultySelect.value });
    updateGame(data.game);
    historyList.replaceChildren();
    historyEmpty.hidden = false;
    guessInput.value = "";
    showMessage("A new code is ready. Make your first guess!");
    guessInput.focus();
  } catch (error) {
    showMessage(error.message, "error");
  } finally {
    restartButton.disabled = false;
  }
}

guessForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const guess = guessInput.value.trim();
  submitButton.disabled = true;

  try {
    const data = await postJson("/api/guess", { guess });
    updateGame(data.game);
    addHistory(guess, data.feedback);

    if (data.game.status === "won") {
      showMessage(`You cracked the code in ${data.game.attempts} ${data.game.attempts === 1 ? "attempt" : "attempts"}! The code was ${data.game.secret}.`, "success");
    } else if (data.game.status === "lost") {
      showMessage(`No attempts left. The code was ${data.game.secret}. Start a new game to try again.`, "info");
    } else {
      showMessage("Clues added. Use them to narrow down your next guess.");
      guessInput.value = "";
      guessInput.focus();
    }
  } catch (error) {
    showMessage(error.message, "error");
  } finally {
    submitButton.disabled = guessInput.disabled;
  }
});

restartButton.addEventListener("click", startNewGame);
difficultySelect.addEventListener("change", startNewGame);

fetch("/api/state")
  .then((response) => response.json())
  .then((data) => {
    if (data.game) {
      updateGame(data.game);
      data.game.history.forEach(({ guess, feedback }) => addHistory(guess, feedback));
      if (data.game.status === "won") {
        showMessage(`You cracked the code! The code was ${data.game.secret}.`, "success");
      } else if (data.game.status === "lost") {
        showMessage(`Game over. The code was ${data.game.secret}. Start a new game to try again.`, "info");
      }
    } else {
      startNewGame();
    }
  })
  .catch(() => showMessage("Couldn't connect to the game. Refresh the page to try again.", "error"));
