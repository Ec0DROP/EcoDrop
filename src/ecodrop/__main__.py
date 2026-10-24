"""Application entry point: ``python -m ecodrop`` or the ``ecodrop`` console script."""

from __future__ import annotations

import argparse
import logging
import sys
from collections.abc import Sequence
from dataclasses import replace

from ecodrop import __version__
from ecodrop.core.config import ENVIRONMENTS, LOG_LEVELS, ConfigError, Settings

logger = logging.getLogger("ecodrop")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ecodrop", description="EcoDrop application.")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument(
        "--env",
        choices=ENVIRONMENTS,
        help="Runtime environment (overrides ECODROP_ENV).",
    )
    parser.add_argument(
        "--log-level",
        choices=LOG_LEVELS,
        type=str.upper,
        help="Logging level (overrides ECODROP_LOG_LEVEL).",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        settings = Settings.from_env()
        overrides = {
            key: value
            for key, value in (("env", args.env), ("log_level", args.log_level))
            if value is not None
        }
        settings = replace(settings, **overrides)
    except ConfigError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 2

    logging.basicConfig(level=settings.log_level, format="%(levelname)s %(name)s: %(message)s")
    logger.info("EcoDrop %s started (env=%s)", __version__, settings.env)
    return 0


if __name__ == "__main__":
    sys.exit(main())
