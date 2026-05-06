#!/usr/bin/env python3
"""
Test script for Fiber Tester Controller
Demonstrates the Python logic functionality
"""

from fiber_tester import FiberTesterController

def test_fiber_tester():
    """Test the fiber tester functionality"""
    print("=== Fiber Tester Controller Test ===\n")

    # Create controller instance
    controller = FiberTesterController()

    # Test 1: Set color
    print("1. Testing color selection:")
    result = controller.set_color("Red")
    print(f"   Set Red: {result['message']}")

    result = controller.set_color("Invalid")
    print(f"   Set Invalid: {result['message']}")

    # Test 2: Set number
    print("\n2. Testing number input:")
    controller.set_color("Green")
    result = controller.set_number("42")
    print(f"   Set 42: {result['message']}")

    result = controller.set_number("150")
    print(f"   Set 150: {result['message']}")

    # Test 3: Prepare transmission
    print("\n3. Testing transmission preparation:")
    controller.set_color("Blue")
    controller.set_number("7")
    result = controller.prepare_transmission()
    print(f"   Prepare Blue 7: {result['message']}")
    print(f"   Sequence length: {len(result['sequence'])} steps")
    print(f"   Total duration: {result['total_duration']}ms")

    # Show first few steps of sequence
    print("   First 5 steps:")
    for i, step in enumerate(result['sequence'][:5]):
        print(f"     {i+1}. {step['type']} - {step['duration']}ms - {step['description']}")

    # Test 4: Complete transmission
    print("\n4. Testing transmission completion:")
    result = controller.complete_transmission()
    print(f"   Complete: {result['message']}")
    print(f"   History: {len(result['history'])} transmissions")

    # Test 5: Multiple transmissions
    print("\n5. Testing multiple transmissions:")
    test_cases = [
        ("Red", "1"),
        ("Green", "23"),
        ("Blue", "99")
    ]

    for color, number in test_cases:
        controller.set_color(color)
        controller.set_number(number)
        controller.prepare_transmission()
        complete_result = controller.complete_transmission()
        print(f"   {color} {number}: {complete_result['message']}")

    # Test 6: Status check
    print("\n6. Final status:")
    status = controller.get_status()
    print(f"   Current color: {status['color']}")
    print(f"   Current number: {status['number']}")
    print(f"   Ready to send: {status['ready_to_send']}")
    print(f"   History count: {len(status['history'])}")

    # Test 7: Show full history
    print("\n7. Transmission history:")
    history = controller.get_history()
    for i, trans in enumerate(history, 1):
        print(f"   {i}. {trans['color']} {trans['number']} - {trans['sequence_steps']} steps, {trans['total_duration']}ms")

if __name__ == "__main__":
    test_fiber_tester()

