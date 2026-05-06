#!/usr/bin/env python3
"""Run a Morse timing pattern directly over the USB DMX interface."""
import argparse
import signal
import sys
import time

sys.path.insert(0, '/home/laser-dmx/fiber-laser-dmx/scripts')

from dmx_controller import DMXController  # noqa: E402

STOP_REQUESTED = False


def _handle_signal(controller: DMXController, signum, _frame):
    controller.log(f"Signal {signum} received, stopping pattern")
    controller.emergency_stop()
    global STOP_REQUESTED
    STOP_REQUESTED = True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('channel', type=int, help='DMX channel (7-12) to run')
    parser.add_argument('--port', default='/dev/ttyUSB0', help='Serial device for FT232R dongle')
    parser.add_argument('--once', action='store_true', help='Run a single cycle instead of looping')
    args = parser.parse_args()

    controller = DMXController(serial_port=args.port)
    controller.connect()

    signal.signal(signal.SIGINT, lambda s, f: _handle_signal(controller, s, f))
    signal.signal(signal.SIGTERM, lambda s, f: _handle_signal(controller, s, f))

    controller.pattern_run(channel=args.channel, loop_indefinitely=not args.once)

    while not STOP_REQUESTED:
        time.sleep(0.5)


if __name__ == '__main__':
    main()
