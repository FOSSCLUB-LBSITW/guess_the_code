import random


def generate_code(length=4):
    """Generate a secret code with unique digits."""
    digits = list("0123456789")
    return "".join(random.sample(digits, length))

def check_guess(secret, guess):
    """
    Compare the guess with the secret.

    Returns:
        C = correct digit and correct position
        W = correct digit but wrong position
        X = digit does not exist
    """

    result = []
    for i, digit in enumerate(guess):
        if digit == secret[i]:
            result.append("C")
        elif digit in secret:
            result.append("W")
        else:
            result.append("X")
    return result

def play_game():
    print("🔐 GUESS THE CODE")
    print("----------------")
    print("Guess the secret 4-digit code.")
    print()
    print("C = correct digit + correct position")
    print("W = correct digit + wrong position")
    print("X = digit doesn't exist")
    print()

    secret = generate_code(4)
    attempts = 0
    max_attempts = 10
    while attempts < max_attempts:
        guess = input("Enter your guess: ").strip()

        # Basic validation
        if not guess.isdigit():
            print("Please enter numbers only.")
            continue

        if len(guess) != 4:
            print("Please enter exactly 4 digits.")
            continue

        attempts += 1

        result = check_guess(secret, guess)

        print("Result:", " ".join(result))
        print("Attempts left:", max_attempts - attempts)
        print()

        if guess == secret:
            print("You cracked the code!")
            print("Attempts:", attempts)
            return

    print("Game over!")
    print("The secret code was:", secret)


if __name__ == "__main__":
    play_game()
