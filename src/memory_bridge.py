"""
Backward compatibility bridge for memory_engine.py.
Ensures test_recall.py continues to work with the new enhanced memory system.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from memory_engine import engine as legacy_engine
from src.enhanced_memory_engine import EnhancedMemoryEngine
from src.nudge_generator import NudgeGenerator


class MemoryBridge:
    """
    Provides backward-compatible interface to legacy test_recall.py
    while using the enhanced memory system under the hood.
    """

    def __init__(self):
        self.legacy = legacy_engine
        self.enhanced = EnhancedMemoryEngine()

    def save_memory(self, user_name, message_text):
        """Save to legacy system for compatibility."""
        self.legacy.save_memory(user_name, message_text)

    def analyze_user_traits(self, target_person):
        """Use legacy analysis for now."""
        return self.legacy.analyze_user_traits(target_person)

    def generate_recall_nudge(self, target_person):
        """
        Generate nudge using enhanced system if possible,
        fallback to legacy if no enhanced memories exist.
        """
        try:
            # Try enhanced nudge first
            nudge = NudgeGenerator.generate_contextual_nudge(
                target_person,
                self.enhanced
            )

            # If we got a generic nudge, try legacy as backup
            if "maybe reach out and see how they're doing" in nudge.lower():
                # Fall back to legacy
                return self.legacy.generate_recall_nudge(target_person)

            return nudge

        except Exception as e:
            print(f"[BRIDGE] Error generating enhanced nudge, using legacy: {e}")
            return self.legacy.generate_recall_nudge(target_person)


# Export as drop-in replacement
engine = MemoryBridge()
