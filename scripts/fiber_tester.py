#!/usr/bin/env python3
"""
Fiber Tester Controller
Main controller logic for fiber optic identification system
Handles color selection, number input, and Morse code transmission preparation
"""

import time
from typing import Dict, List


class FiberTesterController:
    """
    Controller for fiber optic identification system
    Manages color selection, number input, and Morse transmission sequences
    """

    VALID_COLORS = ["Red", "Green", "Blue"]

    # Morse code timing patterns (in milliseconds)
    DOT_DURATION = 120
    DASH_DURATION = 360
    SYMBOL_GAP = 120
    LETTER_GAP = 840

    # Morse code for numbers 0-9
    MORSE_NUMBERS = {
        "0": "-----",
        "1": ".----",
        "2": "..---",
        "3": "...--",
        "4": "....-",
        "5": ".....",
        "6": "-....",
        "7": "--...",
        "8": "---..",
        "9": "----.",
    }

    def __init__(self):
        """Initialize the controller"""
        self.current_color = None
        self.current_number = None
        self.ready_to_send = False
        self.current_sequence = []
        self.transmission_history = []

    def set_color(self, color: str) -> Dict:
        """
        Set the fiber color (Red, Green, Blue)

        Args:
            color: Color name (Red, Green, or Blue)

        Returns:
            dict with status and message
        """
        if color not in self.VALID_COLORS:
            return {
                "success": False,
                "message": f"Invalid color. Choose from: {', '.join(self.VALID_COLORS)}"
            }

        self.current_color = color
        self.ready_to_send = False

        return {
            "success": True,
            "message": f"Color set to {color}",
            "color": self.current_color
        }

    def set_number(self, number: str) -> Dict:
        """
        Set the identification number (0-99)

        Args:
            number: Number as string (0-99)

        Returns:
            dict with status and message
        """
        try:
            num_value = int(number)
            if num_value < 0 or num_value > 99:
                return {
                    "success": False,
                    "message": "Number must be between 0 and 99"
                }

            self.current_number = number
            self.ready_to_send = False

            return {
                "success": True,
                "message": f"Number set to {number}",
                "number": self.current_number
            }

        except ValueError:
            return {
                "success": False,
                "message": "Invalid number format"
            }

    def _number_to_morse(self, number: str) -> str:
        """
        Convert number to Morse code

        Args:
            number: Number string (0-99)

        Returns:
            Morse code string
        """
        morse = []
        for digit in number:
            morse.append(self.MORSE_NUMBERS[digit])

        # Join with letter gap
        return " ".join(morse)

    def _morse_to_sequence(self, morse: str) -> List[Dict]:
        """
        Convert Morse code to timing sequence

        Args:
            morse: Morse code string

        Returns:
            List of timing steps
        """
        sequence = []
        step_num = 1

        for char in morse:
            if char == ".":
                # Dot - short ON
                sequence.append({
                    "step": step_num,
                    "type": "ON",
                    "duration": self.DOT_DURATION,
                    "description": "Dot (short pulse)"
                })
                step_num += 1

                # Symbol gap
                sequence.append({
                    "step": step_num,
                    "type": "OFF",
                    "duration": self.SYMBOL_GAP,
                    "description": "Symbol gap"
                })
                step_num += 1

            elif char == "-":
                # Dash - long ON
                sequence.append({
                    "step": step_num,
                    "type": "ON",
                    "duration": self.DASH_DURATION,
                    "description": "Dash (long pulse)"
                })
                step_num += 1

                # Symbol gap
                sequence.append({
                    "step": step_num,
                    "type": "OFF",
                    "duration": self.SYMBOL_GAP,
                    "description": "Symbol gap"
                })
                step_num += 1

            elif char == " ":
                # Letter gap (already have symbol gap, add remainder)
                sequence.append({
                    "step": step_num,
                    "type": "OFF",
                    "duration": self.LETTER_GAP - self.SYMBOL_GAP,
                    "description": "Letter gap"
                })
                step_num += 1

        # Add final long gap at end
        sequence.append({
            "step": step_num,
            "type": "OFF",
            "duration": 990,
            "description": "End of transmission"
        })

        return sequence

    def prepare_transmission(self) -> Dict:
        """
        Prepare the transmission sequence

        Returns:
            dict with sequence and metadata
        """
        if not self.current_color:
            return {
                "success": False,
                "message": "Color not set"
            }

        if not self.current_number:
            return {
                "success": False,
                "message": "Number not set"
            }

        # Convert number to Morse
        morse = self._number_to_morse(self.current_number)

        # Convert Morse to timing sequence
        self.current_sequence = self._morse_to_sequence(morse)

        # Calculate total duration
        total_duration = sum(step["duration"] for step in self.current_sequence)

        self.ready_to_send = True

        return {
            "success": True,
            "message": f"Transmission prepared: {self.current_color} fiber, number {self.current_number}",
            "color": self.current_color,
            "number": self.current_number,
            "morse": morse,
            "sequence": self.current_sequence,
            "total_duration": total_duration
        }

    def complete_transmission(self) -> Dict:
        """
        Mark transmission as complete and add to history

        Returns:
            dict with completion status
        """
        if not self.ready_to_send:
            return {
                "success": False,
                "message": "No transmission prepared"
            }

        # Add to history
        transmission = {
            "timestamp": time.time(),
            "color": self.current_color,
            "number": self.current_number,
            "sequence_steps": len(self.current_sequence),
            "total_duration": sum(step["duration"] for step in self.current_sequence)
        }

        self.transmission_history.append(transmission)

        # Reset ready flag but keep color and number
        self.ready_to_send = False

        return {
            "success": True,
            "message": f"Transmission complete: {self.current_color} {self.current_number}",
            "transmission": transmission,
            "history": self.transmission_history
        }

    def get_status(self) -> Dict:
        """
        Get current controller status

        Returns:
            dict with current state
        """
        return {
            "color": self.current_color,
            "number": self.current_number,
            "ready_to_send": self.ready_to_send,
            "sequence_length": len(self.current_sequence),
            "history": self.transmission_history
        }

    def get_history(self) -> List[Dict]:
        """
        Get transmission history

        Returns:
            List of past transmissions
        """
        return self.transmission_history

    def reset(self):
        """Reset the controller to initial state"""
        self.current_color = None
        self.current_number = None
        self.ready_to_send = False
        self.current_sequence = []
        # Keep history

    def clear_history(self):
        """Clear transmission history"""
        self.transmission_history = []

