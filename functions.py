import kafka
import requests
import heapq
import os
import json
import dotenv
from time import time
dotenv.load_dotenv()

# API Configuration
base_url = "https://series-hackathon-service-202642739529.us-east1.run.app"
api_key = '6113d6ed-b505-4b92-ae29-21fbe76eb2fc'
sender = "+16463458837"

# Gemini API Configuration
gemini_api_key = os.getenv('GEMINI_API_KEY', '')  # Set GEMINI_API_KEY environment variable
gemini_model = "gemini-2.5-flash"

# Priority queue: (timestamp, chat_id, phone_number)
priority_queue = []


def insert_to_priority_queue(timestamp, chat_id, phone_number):
    """
    Insert an entry into the priority queue.
    
    Args:
        timestamp: The time when the reminder should trigger
        chat_id: The ID of the chat
        phone_number: The phone number to remind
    """
    heapq.heappush(priority_queue, (timestamp, chat_id, phone_number))
    print(f"Added reminder to queue: chat_id={chat_id}, phone={phone_number}, timestamp={timestamp}")


def get_ai_response(prompt, chat_history):
    """
    Simple function to get AI response for a given prompt and chat history.
    
    Args:
        prompt: The prompt to send to the AI
        chat_history: The chat history for context
        
    Returns:
        The AI response as a string
    """
    if not gemini_api_key:
        print("[AI] ERROR: GEMINI_API_KEY not set. Please set the environment variable.")
        return ""
    
    # Format chat history for the prompt
    history_text = ""
    if chat_history:
        for msg in chat_history:
            text = msg.get('text', '')
            history_text += f"{text}\n"
    
    # Construct the full prompt
    full_prompt = f"""{prompt}

Chat History:
{history_text}"""
    
    # Call Gemini API
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{gemini_model}:generateContent"
    
    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": full_prompt
                    }
                ]
            }
        ]
    }
    
    headers = {
        "Content-Type": "application/json",
    }
    
    try:
        print("[AI] Calling Gemini API...")
        r = requests.post(
            f"{url}?key={gemini_api_key}",
            headers=headers,
            json=payload,
            timeout=30
        )
        print(f"[AI] HTTP {r.status_code}")
        
        if r.ok:
            response_data = r.json()
            try:
                ai_response = response_data['candidates'][0]['content']['parts'][0]['text']
                print(f"[AI] Response: {ai_response}")
                return ai_response.strip()
            except (KeyError, IndexError) as e:
                print(f"[AI] Error parsing Gemini response: {e}")
                return ""
        else:
            print(f"[AI] Error from Gemini API: {r.text}")
            return ""
            
    except Exception as e:
        print(f"[AI] Failed to call Gemini API: {e}")
        return ""


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


def get_chat_history(chat_id):
    """
    Retrieve chat history from the API and return the last 25 messages.
    Paginates through all messages to get them all, then returns the last 25.
    
    Args:
        chat_id: The ID of the chat
        
    Returns:
        List of the last 25 messages in the chat
    """
    url = f"{base_url}/api/chats/{chat_id}/chat_messages"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    
    all_messages = []
    page = 1
    per_page = 100  # Get 100 per page to minimize API calls
    
    try:
        print(f"Fetching chat history for chat {chat_id}")
        
        # Paginate through all messages
        while True:
            params = {
                "page": page,
                "per_page": per_page
            }
            
            r = requests.get(url, headers=headers, params=params, timeout=15)
            print(f"HTTP {r.status_code} - Page {page}")
            
            if r.ok:
                response_data = r.json()
                messages = response_data.get('data', [])
                meta = response_data.get('meta', {})
                
                all_messages.extend(messages)
                print(f"Retrieved {len(messages)} messages on page {page}")
                
                # Check if there are more pages
                total_pages = int(meta.get('total_pages', 1))
                if page >= total_pages:
                    break
                
                page += 1
            else:
                print(f"Error fetching chat history: {r.text}")
                break
        
        # Return only the last 25 messages
        last_messages = all_messages[-25:] if len(all_messages) > 25 else all_messages
        print(f"Retrieved {len(all_messages)} total messages, returning last {len(last_messages)}")
        return last_messages
            
    except Exception as e:
        print(f"Failed to fetch chat history: {e}")
        return []
        return []


def ai_respond(chat_id, message, from_phone, prompt, chat_history):
    """
    Use Google Gemini 2.5 Flash to respond to a personal message.
    
    Args:
        chat_id: The ID of the chat
        message: The message content
        from_phone: The phone number of the sender
        prompt: The AI system prompt
        chat_history: The chat history for context
    """
    print(f"[AI RESPOND] Processing message from {from_phone} in personal chat {chat_id}")
    print(f"[AI RESPOND] Message: {message}")
    
    if not gemini_api_key:
        print("[AI RESPOND] ERROR: GEMINI_API_KEY not set. Please set the environment variable.")
        return
    
    # Format chat history for the prompt
    history_text = ""
    if chat_history:
        for msg in chat_history:
            text = msg.get('text', '')
            history_text += f"{text}\n"
    
    # Construct the full prompt with system prompt and chat history
    full_prompt = f"""{prompt}

Chat History:
{history_text}

Latest message from {from_phone}: {message}

Please respond appropriately."""
    
    # Call Gemini API
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{gemini_model}:generateContent"
    
    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": full_prompt
                    }
                ]
            }
        ]
    }
    
    headers = {
        "Content-Type": "application/json",
    }
    
    try:
        print("[AI RESPOND] Calling Gemini API...")
        r = requests.post(
            f"{url}?key={gemini_api_key}",
            headers=headers,
            json=payload,
            timeout=30
        )
        print(f"[AI RESPOND] HTTP {r.status_code}")
        
        if r.ok:
            response_data = r.json()
            # Extract the generated text
            try:
                ai_response_text = response_data['candidates'][0]['content']['parts'][0]['text']
                print(f"[AI RESPOND] Generated response:\n{ai_response_text}")
                
                # Try to parse as JSON
                try:
                    ai_json = json.loads(ai_response_text[7:-3])
                    action = ai_json.get('action')
                    message_to_send = ai_json.get('message', '')
                    next_message = ai_json.get('next_message', 0)
                    
                    print(f"[AI RESPOND] Parsed JSON - action: {action}, next_message: {next_message}")
                    
                    # Send only the message text
                    send_message_to_chat(chat_id, message_to_send)
                    
                    # If action is "remind", insert into priority queue
                    if action == "remind" and next_message > 0:
                        current_time = time()
                        reminder_timestamp = current_time + next_message
                        insert_to_priority_queue(reminder_timestamp, chat_id, from_phone)
                    
                except json.JSONDecodeError:
                    # Response is not JSON, send as is
                    print("[AI RESPOND] Response is not JSON, sending as plain text")
                    send_message_to_chat(chat_id, ai_response_text)
                
            except (KeyError, IndexError) as e:
                print(f"[AI RESPOND] Error parsing Gemini response: {e}")
                print(f"[AI RESPOND] Full response: {response_data}")
        else:
            print(f"[AI RESPOND] Error from Gemini API: {r.text}")
            
    except Exception as e:
        print(f"[AI RESPOND] Failed to call Gemini API: {e}")


def think_and_act(chat_id, message, from_phone, chat_mapping, priority_queue, reminder_delay, ai_prompt):
    """
    Process a message received from Kafka and manage priority queue for reminders.
    
    Args:
        chat_id: The ID of the chat/conversation
        message: The message content to process
        from_phone: The phone number of the sender
        chat_mapping: Dictionary mapping chat_id to list of phone_numbers in that chat
        priority_queue: Priority queue for tracking reminders (heap)
        reminder_delay: Delay in seconds before sending reminders
        ai_prompt: The AI system prompt
    """
    print(f"Processing message for chat_id: {chat_id}")
    print(f"From phone: {from_phone}")
    print(f"Message: {message}")
    
    # Check if this is a group chat or personal message
    if chat_id in chat_mapping:
        # This is a group chat
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
                    insert_to_priority_queue(reminder_time, chat_id, phone)
    else:
        # This is a personal message
        print(f"Chat ID {chat_id} not found in chat_mapping - treating as personal message")
        
        # Get chat history
        chat_history = get_chat_history(chat_id)
        
        # Call AI respond
        ai_respond(chat_id, message, from_phone, ai_prompt, chat_history)
    
    print(f"Current priority queue size: {len(priority_queue)}")

