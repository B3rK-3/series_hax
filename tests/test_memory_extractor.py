import sys
import os
import json
from unittest.mock import MagicMock, patch

# Add parent directory to path to import src
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.memory_extractor import MemoryExtractor, ExtractedMemory

# Mock ContactManager
class MockContactManager:
    def get_name(self, phone):
        if phone == "+1234567890":
            return "John Doe"
        return None

    def track_unknown(self, phone):
        pass

# Sample data
MESSAGES = [
    {
        "phone": "+1234567890",
        "message": "I have a big exam next Monday.",
        "timestamp": "2023-10-27T10:00:00Z"
    },
    {
        "phone": "+1234567890",
        "message": "Just chilling.",
        "timestamp": "2023-10-27T10:05:00Z"
    }
]

CHAT_HISTORY = [
    {"text": "Hey, how are you?"},
    {"text": "I'm good, just studying."}
]

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
                            "summary": "John has a big exam next Monday",
                            "event_date": "2023-10-30",
                            "status": "upcoming",
                            "emotional_state": "stressed",
                            "reasoning": "Specific event with date"
                        })
                    }
                ]
            }
        }
    ]
}

def test_memory_extraction():
    print("Testing MemoryExtractor...")
    
    # Setup mocks
    contact_manager = MockContactManager()
    extractor = MemoryExtractor(gemini_api_key="fake_key", contact_manager=contact_manager)
    
    # Mock requests.post
    with patch('requests.post') as mock_post:
        def side_effect(*args, **kwargs):
            # Extract the prompt from the payload
            payload = kwargs.get('json', {})
            prompt = payload.get('contents', [{}])[0].get('parts', [{}])[0].get('text', '')
            
            mock_response = MagicMock()
            mock_response.ok = True
            
            if "I have a big exam" in prompt:
                mock_response.json.return_value = GEMINI_RESPONSE
            else:
                mock_response.json.return_value = {
                    "candidates": [{
                        "content": {
                            "parts": [{"text": json.dumps({"is_memorable": False})}]
                        }
                    }]
                }
            return mock_response

        mock_post.side_effect = side_effect
        
        # Run extraction
        memories = extractor.analyze_messages("chat_123", MESSAGES, CHAT_HISTORY)
        
        # Verify results
        print(f"Extracted {len(memories)} memories.")
        for memory in memories:
            print(f"Memory: {memory.summary}")
            print(f"Category: {memory.category}")
            print(f"Importance: {memory.importance}")
            print(f"Original Text: {memory.original_text}")
            
        if len(memories) == 1 and memories[0].summary == "John has a big exam next Monday":
            print("SUCCESS: Memory extracted correctly.")
        else:
            print("FAILURE: Memory extraction failed.")

if __name__ == "__main__":
    test_memory_extraction()
