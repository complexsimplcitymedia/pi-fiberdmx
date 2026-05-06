#!/usr/bin/env python3
"""Run fiber DMX Morse patterns directly over the FT232R interface"""

import argparse
import sys
import time

from dmx_controller import DMXController
from dmx_patterns import PatternParser


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Play fiber Morse code patterns over DMX without QLC+"
    )
    parser.add_argument(
        "channels",
        help="Comma-separated list of channels to run (7-12) or 'all'",
    )
    parser.add_argument(
        "--serial",
        default="/dev/ttyUSB0",
        help="Serial device for FT232R DMX dongle (default: /dev/ttyUSB0)",
    )
    parser.add_argument(
        "--repeat",
        type=int,
        default=1,
        help="Number of times to run each channel (default: 1)",
    )
    parser.add_argument(
        "--gap",
        type=float,
        default=1.0,
        help="Seconds to wait between channel runs (default: 1.0)",
    )
    return parser.parse_args()


def resolve_channels(selection: str) -> list[int]:
    if selection.lower() == "all":
        return list(range(7, 13))
    try:
        channels = [int(x.strip()) for x in selection.split(",") if x.strip()]
    except ValueError as exc:
        raise SystemExit(f"Invalid channel list '{selection}': {exc}") from exc

    for ch in channels:
        if ch < 7 or ch > 12:
            raise SystemExit("Channels must be in the range 7-12")
    return channels


def pattern_duration(pattern) -> float:
    return sum(seg.duration for seg in pattern)


def main() -> int:
    args = parse_args()
    channels = resolve_channels(args.channels)

    parser = PatternParser()
    controller = DMXController(serial_port=args.serial)

    try:
        controller.connect()
    except Exception as exc:  # pragma: no cover
        print(f"Failed to connect to {args.serial}: {exc}", file=sys.stderr)
        return 1

    try:
        for channel in channels:
            pattern = parser.get_pattern(channel)
            if not pattern:
                print(f"No pattern defined for channel {channel}", file=sys.stderr)
                continue

            duration = pattern_duration(pattern)
            print(
                f"Running channel {channel} pattern for {duration:.2f}s "
                f"(repeat {args.repeat}x)",
                flush=True,
            )

            for iteration in range(args.repeat):
                controller.pattern_run(channel, loop_indefinitely=False)

                while controller.running_pattern:
                    time.sleep(0.05)

                if iteration < args.repeat - 1:
                    time.sleep(args.gap)

            # Small gap before next channel
            time.sleep(args.gap)

    except KeyboardInterrupt:
        print("\nInterrupted; stopping patterns")
    finally:
        controller.pattern_stop()
        controller.emergency_stop()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
