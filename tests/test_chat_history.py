#!/usr/bin/env python3
"""
Test script for get_chat_history function
"""

from src.series_api import get_chat_history

def test_get_chat_history():
    """Test the get_chat_history function with a sample chat_id"""
    
    # Test with a real chat_id
    # Replace this with an actual chat_id you want to test
    chat_id = 1701434  # Example chat_id
    
    print(f"Fetching chat history for chat_id: {chat_id}")
    print("-" * 50)
    
    messages = get_chat_history(chat_id)
    
    print("-" * 50)
    print(f"Total messages returned: {len(messages)}")
    print()
    
    if messages:
        print("Messages (last 25 or fewer):")
        for i, msg in enumerate(messages, 1):
            print(f"\n{i}. From: {msg.get('sent_from')}")
            print(f"   Text: {msg.get('text')}")
            print(f"   Sent at: {msg.get('sent_at')}")
            print(f"   Delivery status: {msg.get('delivery_status')}")
    else:
        print("No messages returned")

if __name__ == "__main__":
    test_get_chat_history()
