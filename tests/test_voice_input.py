from __future__ import annotations

import unittest

from nova.speech_to_text import get_speech_to_text
from nova.wake_word import WakeWordDetector


class VoiceInputTests(unittest.TestCase):
    def test_voice_commands_disabled_fallback(self) -> None:
        self.assertEqual(get_speech_to_text().status(), "Voice commands are disabled.")

    def test_wake_word_matching(self) -> None:
        detector = WakeWordDetector()
        self.assertTrue(detector._contains_wake_word("hey nova what time is it"))
        self.assertTrue(detector._contains_wake_word("nova tell me a joke"))
        self.assertFalse(detector._contains_wake_word("tell me a joke"))


if __name__ == "__main__":
    unittest.main()
