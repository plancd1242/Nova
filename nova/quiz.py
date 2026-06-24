from __future__ import annotations

QUIZ_LEVELS = {
    1: [
        {"question": "What is 5 plus 7?", "answers": ["12", "twelve"]},
        {"question": "How do you spell cat?", "answers": ["cat", "c a t"]},
        {"question": "What do bees make?", "answers": ["honey"]},
    ],
    2: [
        {"question": "What is the square root of 81?", "answers": ["9", "nine"]},
        {"question": "What part of a computer stores files?", "answers": ["storage", "drive", "ssd", "hard drive"]},
        {"question": "What carries electricity through a circuit?", "answers": ["wire", "wires"]},
    ],
    3: [
        {"question": "What does GPIO stand for?", "answers": ["general purpose input output", "general-purpose input/output"]},
        {"question": "What is 3 squared plus 4 squared?", "answers": ["25", "twenty five", "twenty-five"]},
        {"question": "What planet is known as the red planet?", "answers": ["mars"]},
    ],
}


class QuizSession:
    def __init__(self) -> None:
        self.active = False
        self.awaiting_next_level = False
        self.level = 1
        self.index = 0
        self.score = 0

    def start(self) -> str:
        self.active = True
        self.awaiting_next_level = False
        self.level = 1
        self.index = 0
        self.score = 0
        return f"Quiz mode started. Level {self.level}. {self.current_question()}"

    def current_question(self) -> str:
        return QUIZ_LEVELS[self.level][self.index]["question"]

    def answer(self, text: str) -> tuple[str, str]:
        lower = text.strip().lower()
        if self.awaiting_next_level:
            if lower in {"yes", "y", "sure", "ok", "okay"} and self.level < max(QUIZ_LEVELS):
                self.level += 1
                self.index = 0
                self.score = 0
                self.awaiting_next_level = False
                return "party", f"Quiz mode continued. Level {self.level}. {self.current_question()}"
            self.active = False
            self.awaiting_next_level = False
            return "waiting", "Okay. Quiz mode is finished."

        question = QUIZ_LEVELS[self.level][self.index]
        correct = lower in {answer.lower() for answer in question["answers"]}
        if correct:
            self.score += 1
            prefix = "Correct!"
            led = "done"
        else:
            prefix = f"Incorrect. The answer was {question['answers'][0]}."
            led = "warning"
        self.index += 1
        if self.index >= len(QUIZ_LEVELS[self.level]):
            total = len(QUIZ_LEVELS[self.level])
            if self.level < max(QUIZ_LEVELS):
                self.awaiting_next_level = True
                return led, f"{prefix} Your score was {self.score} out of {total}. Want to do level {self.level + 1}? It's a little harder."
            self.active = False
            return led, f"{prefix} Your score was {self.score} out of {total}. Quiz mode is finished."
        return led, f"{prefix} Next question. {self.current_question()}"

