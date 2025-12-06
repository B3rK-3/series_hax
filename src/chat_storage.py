import os
import json

# Local chat storage file
CHATS_FILE = 'data/chats.json'


def load_chats():
    """Load chats from local JSON file."""
    try:
        # Ensure data directory exists
        os.makedirs(os.path.dirname(CHATS_FILE), exist_ok=True)
        if os.path.exists(CHATS_FILE):
            with open(CHATS_FILE, 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading chats: {e}")
    return {}


def save_chats(chats):
    """Save chats to local JSON file."""
    try:
        # Ensure data directory exists
        os.makedirs(os.path.dirname(CHATS_FILE), exist_ok=True)
        with open(CHATS_FILE, 'w') as f:
            json.dump(chats, f, indent=2)
    except Exception as e:
        print(f"Error saving chats: {e}")


def add_message_to_chat(chat_id, message_data):
    """
    Add a message to a chat in local storage.

    Args:
        chat_id: The ID of the chat
        message_data: Dictionary containing message information
    """
    chats = load_chats()
    chat_id_str = str(chat_id)

    if chat_id_str not in chats:
        chats[chat_id_str] = []

    chats[chat_id_str].append(message_data)
    save_chats(chats)
