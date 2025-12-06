import os
import requests
import dotenv
from datetime import datetime
from src.chat_storage import load_chats, add_message_to_chat

dotenv.load_dotenv()

# API Configuration
base_url = os.getenv('SERIES_BASE_URL')
api_key = os.getenv('SERIES_API_KEY')
sender = os.getenv('SENDER_PHONE')


def send_message_to_chat(chat_id, message_text):
    """
    Send a message to an existing chat and store it in local JSON.

    Args:
        chat_id: The ID of the chat to send to
        message_text: The text of the message to send
    """
    url = f"{base_url}/api/chats/{chat_id}/chat_messages"
    payload = {
        "message": {
            "text": message_text
        }
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    try:
        print(f"Sending message to chat {chat_id}: {message_text}")
        r = requests.post(url, headers=headers, json=payload, timeout=15)
        print(f"HTTP {r.status_code}")

        if r.ok:
            print(f"Message sent successfully to chat {chat_id}")

            # Add message to local chat history
            message_data = {
                'text': message_text,
                'sent_from': sender,
                'sent_at': datetime.now().isoformat()
            }
            add_message_to_chat(chat_id, message_data)

            return True
        else:
            print(f"Error sending message: {r.text}")
            return False

    except Exception as e:
        print(f"Failed to send message: {e}")
        return False


def create_individual_chat(phone_number):
    """
    Create a new individual chat with a phone number.

    Args:
        phone_number: The phone number to create a chat with

    Returns:
        chat_id if successful, None otherwise
    """
    url = f"{base_url}/api/chats"
    payload = {
        "chat": {
            "phone_numbers": [phone_number]
        },
        "message": {
            "text": "Reminder system activated"
        },
        "send_from": sender
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    try:
        print(f"Creating individual chat with {phone_number}")
        r = requests.post(url, headers=headers, json=payload, timeout=15)
        print(f"HTTP {r.status_code}")

        if r.ok:
            response_data = r.json()
            chat_id = response_data.get('data', {}).get('id')

            if chat_id:
                print(f"Individual chat created successfully. Chat ID: {chat_id}")
                return chat_id
            else:
                print("Error: No chat ID in response")
                return None
        else:
            print(f"Error creating chat: {r.text}")
            return None

    except Exception as e:
        print(f"Failed to create individual chat: {e}")
        return None


def get_chat_history(chat_id):
    """
    Retrieve chat history from local JSON storage and return the last 25 messages.

    Args:
        chat_id: The ID of the chat

    Returns:
        List of the last 25 messages in the chat
    """
    chats = load_chats()
    chat_id_str = str(chat_id)

    print(f"Fetching chat history for chat {chat_id} from local storage")

    if chat_id_str in chats:
        all_messages = chats[chat_id_str]
        # Return only the last 25 messages
        last_messages = all_messages[-25:] if len(all_messages) > 25 else all_messages
        print(f"Retrieved {len(all_messages)} total messages, returning last {len(last_messages)}")
        return last_messages
    else:
        print(f"Chat {chat_id} not found in local storage")
        return []
