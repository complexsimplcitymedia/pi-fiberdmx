#!/usr/bin/env python
"""
Generate QLC+ Chasers from master timings and inject into fiber_laser_master_show.qxw
Each chaser represents one channel's ON/OFF pattern with exact timing
"""
import defusedxml.ElementTree as ET
import sys

# Channel 1-12 patterns from Laser_Master_patterns_timings.txt
patterns = {
    1: [(255, 0.12), (0, 0.12), (255, 0.36), (0, 0.12), (255, 0.36), (0, 0.12), (255, 0.36), (0, 0.12), (255, 0.36), (0, 0.99)],
    2: [(255, 0.12), (0, 0.12), (255, 0.12), (0, 0.12), (255, 0.36), (0, 0.12), (255, 0.36), (0, 0.12), (255, 0.36), (0, 0.99)],
    3: [(255, 0.12), (0, 0.12), (255, 0.12), (0, 0.12), (255, 0.12), (0, 0.12), (255, 0.36), (0, 0.12), (255, 0.36), (0, 0.99)],
    4: [(255, 0.12), (0, 0.12), (255, 0.12), (0, 0.12), (255, 0.12), (0, 0.12), (255, 0.12), (0, 0.12), (255, 0.36), (0, 0.99)],
    5: [(255, 0.12), (0, 0.12), (255, 0.12), (0, 0.12), (255, 0.12), (0, 0.12), (255, 0.12), (0, 0.12), (255, 0.12), (0, 0.99)],
    6: [(255, 0.36), (0, 0.12), (255, 0.12), (0, 0.12), (255, 0.12), (0, 0.12), (255, 0.12), (0, 0.12), (255, 0.12), (0, 0.99)],
    7: [(255, 0.12), (0, 0.12), (255, 0.36), (0, 0.12), (255, 0.36), (0, 0.12), (255, 0.36), (0, 0.12), (255, 0.36), (0, 0.99)],
    8: [(255, 0.12), (0, 0.12), (255, 0.12), (0, 0.12), (255, 0.36), (0, 0.12), (255, 0.36), (0, 0.12), (255, 0.36), (0, 0.99)],
    9: [(255, 0.12), (0, 0.12), (255, 0.12), (0, 0.12), (255, 0.12), (0, 0.12), (255, 0.36), (0, 0.12), (255, 0.36), (0, 0.99)],
    10: [(255, 0.12), (0, 0.12), (255, 0.12), (0, 0.12), (255, 0.12), (0, 0.12), (255, 0.12), (0, 0.12), (255, 0.36), (0, 0.99)],
    11: [(255, 0.12), (0, 0.12), (255, 0.12), (0, 0.12), (255, 0.12), (0, 0.12), (255, 0.12), (0, 0.12), (255, 0.12), (0, 0.99)],
    12: [(255, 0.36), (0, 0.12), (255, 0.12), (0, 0.12), (255, 0.12), (0, 0.12), (255, 0.12), (0, 0.12), (255, 0.12), (0, 0.99)],
}

def create_chaser(channel_id, channel_num, pattern):
    """Create a QLC+ Chaser element for a channel with its pattern"""
    chaser = ET.Element("Chaser")
    chaser.set("ID", str(channel_id))
    chaser.set("Name", f"Channel {channel_num} Pattern")
    chaser.set("RunOrder", "Linear")
    chaser.set("FadeInMode", "Common")
    chaser.set("FadeOutMode", "Common")
    chaser.set("Duration", "0")
    chaser.set("FadeInTime", "0")
    chaser.set("FadeOutTime", "0")
    chaser.set("Speed", "0")
    chaser.set("SpeedMode", "Default")
    chaser.set("Direction", "Forward")
    
    for step_num, (brightness, duration) in enumerate(pattern):
        step = ET.SubElement(chaser, "Step")
        step.set("Number", str(step_num))
        step.set("FadeIn", "0")
        step.set("Hold", str(int(duration * 1000)))  # Convert seconds to milliseconds
        step.set("FadeOut", "0")
    
    return chaser

def main():
    # Load existing QLC+ file
    qxw_file = '/home/laser-dmx/fiber-laser-dmx/showfiles/fiber_laser_master_show.qxw'
    
    try:
        tree = ET.parse(qxw_file)
        root = tree.getroot()
        print(f"✓ Loaded {qxw_file}")
    except Exception as e:
        print(f"✗ Failed to load QLC+ file: {e}")
        sys.exit(1)
    
    # Register namespace to preserve formatting
    ET.register_namespace('', 'http://www.qlcplus.org/Workspace')
    
    # Find or create Function section
    ns = {'qlc': 'http://www.qlcplus.org/Workspace'}
    functions = root.find('.//Functions', ns)
    if functions is None:
        functions = root.find('Functions')
    if functions is None:
        # Create Functions element after InputOutputMap
        engine = root.find('Engine')
        if engine is None:
            engine = ET.SubElement(root, 'Engine')
        functions = ET.SubElement(engine, 'Functions')
        print("✓ Created Functions section")
    
    # Add chasers for each channel
    chaser_id = 1000
    for channel_num, pattern in patterns.items():
        chaser = create_chaser(chaser_id, channel_num, pattern)
        functions.append(chaser)
        print(f"✓ Added Chaser for Channel {channel_num} (ID: {chaser_id})")
        chaser_id += 1
    
    # Save updated file
    try:
        tree.write(qxw_file, encoding='UTF-8', xml_declaration=True)
        print(f"\n✓ Updated {qxw_file} with all channel patterns")
        print("Ready to open in QLC+ and trigger patterns manually")
    except Exception as e:
        print(f"✗ Failed to save QLC+ file: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
