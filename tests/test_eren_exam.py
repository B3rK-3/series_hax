import sys
import os
import json
from unittest.mock import MagicMock, patch
from datetime import datetime

# Add parent directory to path to import src
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.memory_extractor import MemoryExtractor

# Mock ContactManager
class MockContactManager:
    def get_name(self, phone):
        if phone == "+15550001111":
            return "Eren"
        return None

    def track_unknown(self, phone):
        pass

# Sample data
MESSAGES = [
    {
        "phone": "+15550001111",
        "message": "I'm so stressed about my calc exam on December 4th.",
        "timestamp": "2025-11-20T10:00:00Z"
    }
]

CHAT_HISTORY = []

# Mock Gemini Response
GEMINI_RESPONSE = {
    "candidates": [
        {
            "content": {
                "parts": [
                    {
                        "text": json.dumps({
                            "is_memorable": True,
                            "category": "exam/test",
                            "importance": 8,
                            "summary": "Eren has a calc exam on December 4th",
                            "event_date": "2025-12-04",
                            "status": "upcoming",
                            "emotional_state": "stressed",
                            "reasoning": "Specific event with date and high emotion"
                        })
                    }
                ]
            }
        }
    ]
}

def test_eren_exam_extraction():
    print("Testing MemoryExtractor for Eren's Exam...")
    
    # Setup mocks
    contact_manager = MockContactManager()
    extractor = MemoryExtractor(gemini_api_key="fake_key", contact_manager=contact_manager)
    
    # Mock requests.post
    with patch('requests.post') as mock_post:
        def side_effect(*args, **kwargs):
            # Verify the prompt contains the message
            payload = kwargs.get('json', {})
            prompt = payload.get('contents', [{}])[0].get('parts', [{}])[0].get('text', '')
            
            if "stressed about my calc exam" in prompt:
                mock_response = MagicMock()
                mock_response.ok = True
                mock_response.json.return_value = GEMINI_RESPONSE
                return mock_response
            return MagicMock(ok=False)

        mock_post.side_effect = side_effect
        
        # Run extraction
        memories = extractor.analyze_messages("chat_eren", MESSAGES, CHAT_HISTORY)
        
        # Verify results
        if not memories:
            print("FAILURE: No memories extracted.")
            return

        memory = memories[0]
        print(f"Extracted Memory: {memory.summary}")
        print(f"Category: {memory.category}")
        print(f"Event Date: {memory.event_date}")
        print(f"Importance: {memory.importance}")
        print(f"Emotional State: {memory.structured_data.get('emotional_state')}")

        # Assertions
        assert memory.person == "Eren"
        assert memory.category == "exam/test"
        assert memory.event_date == "2025-12-04"
        assert memory.importance >= 7
        assert memory.structured_data.get('emotional_state') == "stressed"
        
        print("\nSUCCESS: Eren's exam was correctly extracted with high importance and date.")

if __name__ == "__main__":
    test_eren_exam_extraction()
