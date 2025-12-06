import kafka
import requests
import heapq
from time import time

# API Configuration
base_url = "https://series-hackathon-service-202642739529.us-east1.run.app"
api_key = '6113d6ed-b505-4b92-ae29-21fbe76eb2fc'
sender = "+16463458837"


def send_reminder(chat_id, phone_number, phone_to_chat, numbers_in_chat):
    """
    Send a reminder message to a phone number.
    If chat with that phone exists, send to existing chat.
    Otherwise, create a new chat and send the reminder.
    
    Args:
        chat_id: The ID of the original chat
        phone_number: The phone number to send the reminder to
        phone_to_chat: Dictionary mapping phone_number to chat_id
    """
    print(f"Sending reminder to {phone_number} in chat {chat_id}")
    
    reminder_message = f"You haven't responded to your chat with {', '.join([e for e in numbers_in_chat if e != phone_number])} yet! Do you want to continue the conversation?"
    # Check if we already have a chat with this phone number
    if phone_number in phone_to_chat:
        # Use existing chat
        target_chat_id = phone_to_chat[phone_number]
        print(f"Using existing chat {target_chat_id} for {phone_number}")
        send_message_to_chat(target_chat_id, reminder_message)
    else:
        # Create new chat with this phone number
        print(f"Creating new chat for {phone_number}")
        new_chat_id = create_individual_chat(phone_number)
        if new_chat_id:
            phone_to_chat[phone_number] = new_chat_id
            print(f"Added {phone_number} to phone_to_chat: {new_chat_id}")
            send_message_to_chat(new_chat_id, reminder_message)


def send_message_to_chat(chat_id, message_text):
    """
    Send a message to an existing chat.
    
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


def think_and_act(chat_id, message, from_phone, chat_mapping, priority_queue, reminder_delay):
    """
    Process a message received from Kafka and manage priority queue for reminders.
    
    Args:
        chat_id: The ID of the chat/conversation
        message: The message content to process
        from_phone: The phone number of the sender
        chat_mapping: Dictionary mapping chat_id to list of phone_numbers in that chat
        priority_queue: Priority queue for tracking reminders (heap)
        reminder_delay: Delay in seconds before sending reminders
    """
    print(f"Processing message for chat_id: {chat_id}")
    print(f"From phone: {from_phone}")
    print(f"Message: {message}")
    
    # Get phone numbers in this chat from chat_mapping
    print(f"Current chat mapping: {chat_mapping}")
    if chat_id in chat_mapping:
        chat_phones = chat_mapping[chat_id]
        print(f"Chat phones: {chat_phones}")
        
        current_time = time()
        reminder_time = current_time + reminder_delay
        
        # For each phone number that isn't the sender
        for phone in chat_phones:
            if phone != from_phone:
                # Check if this (chat_id, phone) pair already exists in priority queue
                exists = False
                for timestamp, qid, qphone in priority_queue:
                    if qid == chat_id and qphone == phone:
                        exists = True
                        print(f"Entry for {phone} in chat {chat_id} already exists, skipping")
                        break
                
                # Only add if it doesn't exist
                if not exists:
                    heapq.heappush(priority_queue, (reminder_time, chat_id, phone))
                    print(f"Added new reminder for {phone} in chat {chat_id} at {reminder_time}")
    else:
        print(f"Chat ID {chat_id} not found in chat_mapping")
    
    print(f"Current priority queue size: {len(priority_queue)}")

