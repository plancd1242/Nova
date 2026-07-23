from __future__ import annotations

import unittest

from nova.speech_to_text import get_speech_to_text
from nova.vosk_model_manager import VoskModelManager
from nova.wake_word import WakeWordDetector
from nova.microphone import Microphone


class VoiceInputTests(unittest.TestCase):
    def test_voice_commands_disabled_fallback(self) -> None:
        self.assertEqual(get_speech_to_text().status(), "Voice commands are disabled.")

    def test_wake_word_matching(self) -> None:
        detector = WakeWordDetector()
        self.assertTrue(detector._contains_wake_word("hey nova what time is it"))
        self.assertTrue(detector._contains_wake_word("nova tell me a joke"))
        self.assertFalse(detector._contains_wake_word("tell me a joke"))

    def test_vosk_model_shape_detection(self) -> None:
        from pathlib import Path
        from tempfile import TemporaryDirectory

        manager = VoskModelManager()
        with TemporaryDirectory() as tmp:
            model = Path(tmp) / "model"
            (model / "conf").mkdir(parents=True)
            (model / "am").mkdir()
            self.assertTrue(manager._looks_like_model(model))

    def test_microphone_sample_rate_falls_back_to_default(self) -> None:
        class FakeSoundDevice:
            def check_input_settings(self, *, device, channels, dtype, samplerate):
                _ = device, channels, dtype
                if samplerate == 16000:
                    raise OSError("paInvalidSampleRate")

        mic = Microphone()
        rate = mic._supported_sample_rate(FakeSoundDevice(), {"default_samplerate": 48000})
        self.assertEqual(rate, 48000)


if __name__ == "__main__":
    unittest.main()
