#!/usr/bin/env python3
import sys
sys.path.append('/home/laser-dmx/fiber-laser-dmx/scripts')
from dmx_controller import DMXController
import time

print('🔴 RED FIBERS (CH 1-3) - 3 LOOPS EACH')
dmx = DMXController('/dev/ttyUSB0')
dmx.connect()

for ch in [1,2,3]:
    for loop in range(3):
        print(f'CH{ch} Loop {loop+1}...')
        dmx.pattern_run(ch, loop_indefinitely=False)
        time.sleep(7)
dmx.emergency_stop()
print('✓ REDS DONE!')
