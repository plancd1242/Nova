from __future__ import annotations

import argparse

from nova.app import NovaApp


def main() -> None:
    parser = argparse.ArgumentParser(description="Nova typed assistant")
    parser.add_argument("--system-check", action="store_true", help="Run checks and exit")
    args = parser.parse_args()

    app = NovaApp()
    if args.system_check:
        app.say(app.system_check())
        return
    app.run_typed()


if __name__ == "__main__":
    main()

