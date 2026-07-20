from __future__ import annotations

import argparse

from nova.app import NovaApp


def main() -> None:
    parser = argparse.ArgumentParser(description="Nova typed assistant")
    parser.add_argument("--system-check", action="store_true", help="Run checks and exit")
    parser.add_argument("--voice", action="store_true", help="Run offline Vosk voice mode")
    parser.add_argument("--listen-once", action="store_true", help="Listen for one offline voice command and exit")
    args = parser.parse_args()

    app = NovaApp()
    if args.system_check:
        app.say(app.system_check())
        return
    if args.listen_once:
        from nova.voice_loop import VoiceLoop

        app.say(VoiceLoop(app).listen_once())
        return
    if args.voice:
        app.run_voice()
        return
    app.run_typed()


if __name__ == "__main__":
    main()
