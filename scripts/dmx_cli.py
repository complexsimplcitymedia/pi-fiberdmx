#!/usr/bin/env python
"""
DMX CLI Control Interface
Safe commands for manual channels, pattern execution, emergency stop, status.
"""

import argparse
import sys
import json
from dmx_controller import DMXController, SafetyConfig

def main():
    parser = argparse.ArgumentParser(
        description="DMX CLI Control for 5kW Laser Fiber Identification System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  dmx_cli.py channel 1 on      # Toggle channel 1 ON (manual)
  dmx_cli.py channel 1 off     # Toggle channel 1 OFF
  dmx_cli.py pattern 7 run     # Run pattern for channel 7
  dmx_cli.py pattern 7 stop    # Stop pattern
  dmx_cli.py emergency-stop    # KILL ALL OUTPUT
  dmx_cli.py status            # Show system status
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Channel command (manual ON/OFF for 1-6, 13-15)
    channel_parser = subparsers.add_parser('channel', help='Manual channel control')
    channel_parser.add_argument('channel', type=int, help='Channel number (1-6, 13-15)')
    channel_parser.add_argument('action', choices=['on', 'off', 'toggle'], help='Action')
    
    # Pattern command (7-12)
    pattern_parser = subparsers.add_parser('pattern', help='Pattern execution')
    pattern_parser.add_argument('channel', type=int, help='Channel number (7-12)')
    pattern_parser.add_argument('action', choices=['run', 'stop'], help='Action')
    
    # Emergency stop
    subparsers.add_parser('emergency-stop', help='EMERGENCY: Stop all output immediately')
    
    # Status
    subparsers.add_parser('status', help='Show system status')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Connect to DMX controller
    try:
        controller = DMXController()
        controller.connect()
    except Exception as e:
        print(f"ERROR: Failed to initialize controller: {e}", file=sys.stderr)
        return 1
    
    try:
        if args.command == 'channel':
            if args.action in ['on', 'off', 'toggle']:
                controller.manual_toggle(args.channel)
                print(f"OK: Channel {args.channel} toggled")
            return 0
        
        elif args.command == 'pattern':
            if args.action == 'run':
                controller.pattern_run(args.channel, loop_indefinitely=True)
                print(f"OK: Pattern {args.channel} started")
            elif args.action == 'stop':
                controller.pattern_stop()
                print(f"OK: Pattern stopped")
            return 0
        
        elif args.command == 'emergency-stop':
            controller.emergency_stop()
            print("OK: EMERGENCY STOP executed")
            return 0
        
        elif args.command == 'status':
            status = controller.get_status()
            print(json.dumps(status, indent=2))
            return 0
    
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
