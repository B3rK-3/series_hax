import kafka
import requests
import heapq
import os
import json
import dotenv
from time import time
dotenv.load_dotenv()

# API Configuration
base_url = os.getenv('SERIES_BASE_URL')
api_key = os.getenv('SERIES_API_KEY')
sender = os.getenv('SENDER_PHONE')

# Gemini API Configuration
gemini_api_key = os.getenv('GEMINI_API_KEY', '')
gemini_model = "gemini-2.5-flash"

# Priority queue: (timestamp, chat_id, phone_number, delay_seconds)
priority_queue = []

# Local chat storage file
CHATS_FILE = 'chats.json'


def load_chats():
    """Load chats from local JSON file."""
    try:
        if os.path.exists(CHATS_FILE):
            with open(CHATS_FILE, 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading chats: {e}")
    return {}


def save_chats(chats):
    """Save chats to local JSON file."""
    try:
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


def insert_to_priority_queue(timestamp, chat_id, phone_number, delay_seconds=0):
    """
    Insert an entry into the priority queue.
    
    Args:
        timestamp: The time when the reminder should trigger
        chat_id: The ID of the chat
        phone_number: The phone number to remind
        delay_seconds: The delay in seconds before the reminder should trigger
    """
    heapq.heappush(priority_queue, (timestamp, chat_id, phone_number, delay_seconds))
    print(f"Added reminder to queue: chat_id={chat_id}, phone={phone_number}, timestamp={timestamp}, delay={delay_seconds}s")


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


def chat_analyze(phone_number, chat_history):
    """
    Analyze a user's chat behavior using the reputation prompt and Gemini API.
    
    Args:
        phone_number: The phone number of the user to analyze
        chat_history: The chat history to analyze
        
    Returns:
        The analysis result from Gemini (typically a JSON with reputation score)
    """
    if not gemini_api_key:
        print("[ANALYZE] ERROR: GEMINI_API_KEY not set. Please set the environment variable.")
        return ""
    
    # Load reputation prompt
    try:
        with open('reputation_prompt.txt', 'r') as f:
            reputation_prompt = f.read()
    except Exception as e:
        print(f"[ANALYZE] Error loading reputation_prompt.txt: {e}")
        return ""
    
    # Format chat history for the prompt
    history_text = ""
    if chat_history:
        for msg in chat_history:
            text = msg.get('text', '')
            history_text += f"{text}\n"
    
    # Construct the full prompt
    full_prompt = f"""{reputation_prompt}

User Phone: {phone_number}

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
        print(f"[ANALYZE] Calling Gemini API to analyze {phone_number}...")
        r = requests.post(
            f"{url}?key={gemini_api_key}",
            headers=headers,
            json=payload,
            timeout=30
        )
        print(f"[ANALYZE] HTTP {r.status_code}")
        
        if r.ok:
            response_data = r.json()
            print(f"[ANALYZE] Gemini response received")
            try:
                analysis_result = response_data['candidates'][0]['content']['parts'][0]['text']
                if analysis_result.startswith("```json") and analysis_result.endswith("```"):
                    analysis_result = analysis_result[7:-3]
                analysis_result_json = json.loads(analysis_result)

                reputation_reduction = analysis_result_json.get("score", None)
                reasoning = analysis_result_json.get("reasoning", "")

                print(f"\n{'='*60}")
                print(f"[ANALYZE] User Reputation Analysis")
                print(f"{'='*60}")
                print(f"Phone Number: {phone_number}")
                print(f"Reputation Score: {reputation_reduction}")
                print(f"Reasoning: {reasoning}")
                print(f"{'='*60}\n")
                
                return analysis_result.strip()
            except (KeyError, IndexError) as e:
                print(f"[ANALYZE] Error parsing Gemini response: {e}")
                return ""
        else:
            print(f"[ANALYZE] Error from Gemini API: {r.text}")
            return ""
            
    except Exception as e:
        print(f"[ANALYZE] Failed to call Gemini API: {e}")
        return ""


def send_reminder(chat_id, phone_number, phone_to_chat, numbers_in_chat, delay_seconds):
    """
    Send a reminder message to a phone number.
    Before sending, check if the user responded within the delay window.
    If they did, cancel the reminder.
    If chat with that phone exists, send to existing chat.
    Otherwise, create a new chat and send the reminder.
    
    Args:
        chat_id: The ID of the original chat
        phone_number: The phone number to send the reminder to
        phone_to_chat: Dictionary mapping phone_number to chat_id
        numbers_in_chat: List of phone numbers in the chat
        delay_seconds: Delay in seconds before reminder should trigger
    """
    print(f"\n[REMINDER] Checking if reminder should be sent to {phone_number} in chat {chat_id}")
    
    # Get the current time minus (delay_seconds + 1 second)
    from datetime import datetime
    current_time = time()
    cutoff_time = current_time - (delay_seconds + 1)
    
    # Get chat history
    chat_history = get_chat_history(chat_id)
    
    # Check if the user (phone_number) responded after the cutoff time
    user_responded_after_cutoff = False
    if chat_history:
        for msg in chat_history:
            msg_from = msg.get('sent_from', '')
            msg_sent_at = msg.get('sent_at', '')
            
            # Parse the timestamp if it exists
            if msg_sent_at:
                try:
                    # Handle multiple timestamp formats
                    msg_timestamp = 0
                    
                    # Try ISO format with timezone (2025-12-06 06:42:12 -0600)
                    if ' ' in msg_sent_at and '-' in msg_sent_at.split()[-1]:
                        try:
                            msg_time = datetime.strptime(msg_sent_at, '%Y-%m-%d %H:%M:%S %z')
                            msg_timestamp = msg_time.timestamp()
                        except ValueError:
                            pass
                    
                    # Try ISO format with T separator
                    elif 'T' in msg_sent_at:
                        msg_time = datetime.fromisoformat(msg_sent_at.replace('Z', '+00:00'))
                        msg_timestamp = msg_time.timestamp()
                    
                    # Try numeric timestamp
                    else:
                        msg_timestamp = float(msg_sent_at)
                        
                except Exception as e:
                    print(f"[REMINDER] Error parsing timestamp '{msg_sent_at}': {e}")
                    msg_timestamp = 0
                
                # Check if this message is from the user and after cutoff
                if msg_from == phone_number and msg_timestamp > cutoff_time:
                    print(f"[REMINDER] User {phone_number} responded at {msg_sent_at} (after cutoff)")
                    user_responded_after_cutoff = True
                    break
    
    # If user responded after cutoff, cancel the reminder
    if user_responded_after_cutoff:
        print(f"[REMINDER] ✓ User {phone_number} already responded! Canceling reminder.")
        return
    
    print(f"[REMINDER] ✗ No response from {phone_number} after cutoff. Sending reminder...")
    
    reminder_message = f"You haven't responded to your chat with {', '.join([e for e in numbers_in_chat if e != phone_number])} yet! Do you want to continue the conversation?"
    # Check if we already have a chat with this phone number
    if phone_number in phone_to_chat:
        # Use existing chat
        target_chat_id = phone_to_chat[phone_number]
        print(f"[REMINDER] Using existing chat {target_chat_id} for {phone_number}")
        send_message_to_chat(target_chat_id, reminder_message)
    else:
        # Create new chat with this phone number
        print(f"[REMINDER] Creating new chat for {phone_number}")
        new_chat_id = create_individual_chat(phone_number)
        if new_chat_id:
            phone_to_chat[phone_number] = new_chat_id
            print(f"[REMINDER] Added {phone_number} to phone_to_chat: {new_chat_id}")
            send_message_to_chat(new_chat_id, reminder_message)
    
    print(f"[REMINDER] Reminder sent to {phone_number}\n")


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
            from datetime import datetime
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
                        insert_to_priority_queue(reminder_timestamp, chat_id, from_phone, next_message)
                    
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
        
        # Get chat history and analyze the sender
        chat_history = get_chat_history(chat_id)
        print(f"Analyzing chat behavior for {from_phone}")
        chat_analyze(from_phone, chat_history)
        
        current_time = time()
        reminder_time = current_time + reminder_delay
        
        # For each phone number that isn't the sender
        for phone in chat_phones:
            if phone != from_phone:
                # Check if this (chat_id, phone) pair already exists in priority queue
                exists = False
                for timestamp, qid, qphone, delay_seconds in priority_queue:
                    if qid == chat_id and qphone == phone:
                        exists = True
                        print(f"Entry for {phone} in chat {chat_id} already exists, skipping")
                        break
                
                # Only add if it doesn't exist
                if not exists:
                    insert_to_priority_queue(reminder_time, chat_id, phone, reminder_delay)
    else:
        # This is a personal message
        print(f"Chat ID {chat_id} not found in chat_mapping - treating as personal message")
        
        # Get chat history
        chat_history = get_chat_history(chat_id)
        
        # Call AI respond
        ai_respond(chat_id, message, from_phone, ai_prompt, chat_history)
    
    print(f"Current priority queue size: {len(priority_queue)}")


def get_convo_starters(chat_history):
    """
    Generate conversation starters based on chat history using Gemini API.
    
    Args:
        chat_history: The chat history to analyze
        
    Returns:
        List of conversation starter strings
    """
    if not gemini_api_key:
        print("[CONVO] ERROR: GEMINI_API_KEY not set.")
        return []
    
    # Format chat history
    history_text = ""
    if chat_history:
        for msg in chat_history:
            text = msg.get('text', '')
            history_text += f"{text}\n"
    
    prompt = f"""Based on the following chat history, generate 3 creative and engaging conversation starters to keep the chat going. Make them relevant to the context and short (1-2 sentences each).

Chat History:
{history_text}

Please provide exactly 3 conversation starters, one per line."""
    
    # Call Gemini API
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{gemini_model}:generateContent"
    
    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": prompt
                    }
                ]
            }
        ]
    }
    
    headers = {
        "Content-Type": "application/json",
    }
    
    try:
        print("[CONVO] Calling Gemini API for conversation starters...")
        r = requests.post(
            f"{url}?key={gemini_api_key}",
            headers=headers,
            json=payload,
            timeout=30
        )
        print(f"[CONVO] HTTP {r.status_code}")
        
        if r.ok:
            response_data = r.json()
            try:
                response_text = response_data['candidates'][0]['content']['parts'][0]['text']
                # Split by newlines and filter out empty lines
                starters = [line.strip() for line in response_text.split('\n') if line.strip()]
                print(f"[CONVO] Generated {len(starters)} conversation starters")
                return starters
            except (KeyError, IndexError) as e:
                print(f"[CONVO] Error parsing Gemini response: {e}")
                return []
        else:
            print(f"[CONVO] Error from Gemini API: {r.text}")
            return []
            
    except Exception as e:
        print(f"[CONVO] Failed to call Gemini API: {e}")
        return []


def scan_inactive_chats(chat_mapping, last_activity_tracker, last_activity_threshold, phone_to_chat):
    """
    Scan all chats in chat_mapping and check for inactive conversations.
    If a chat hasn't had activity in more than last_activity_threshold seconds,
    generate conversation starters and send them to the participants.
    
    Args:
        chat_mapping: Dictionary mapping chat_id to phone_numbers
        last_activity_tracker: Dictionary tracking last activity time for each chat_id
        last_activity_threshold: Seconds of inactivity before sending starters
    """
    current_time = time()
    
    for chat_id, phone_numbers in chat_mapping.items():
        # Get last activity time for this chat (default to current time if not tracked)
        last_activity = last_activity_tracker.get(chat_id, current_time)
        time_since_activity = current_time - last_activity
        
        print(f"[SCAN] Chat {chat_id}: {time_since_activity:.1f}s since last activity (threshold: {last_activity_threshold}s)")
        
        if time_since_activity > last_activity_threshold:
            print(f"[SCAN] Chat {chat_id} is inactive! Getting conversation starters...")
            
            # Get chat history
            chat_history = get_chat_history(chat_id)
            
            # Generate conversation starters
            starters = get_convo_starters(chat_history)
            
            if starters:
                # Format starters into a message
                starters_str = ""
                for i, starter in enumerate(starters, 1):
                    starters_str += f"{i}. {starter}\n"
                
                # Send to all phone numbers in the chat
                for phone in phone_numbers:
                    print(f"[SCAN] Sending conversation starters to {phone}")

                    starter_message = f"You haven't messaged  {', '.join([e for e in phone_numbers if e != phone])} in a while!  How about we continue the conversation? Here are some ideas:\n\n{starters_str}"
                    individual_chat_id = phone_to_chat.get(phone)
                    if individual_chat_id:
                        send_message_to_chat(individual_chat_id, starter_message)
                    else:
                        print(f"[SCAN] No individual chat found for phone {phone}")
                
                # Update last activity time for this chat
                last_activity_tracker[chat_id] = current_time
            else:
                print(f"[SCAN] Failed to generate conversation starters for chat {chat_id}")
        else:
            # Update last activity time if this is a new chat
            if chat_id not in last_activity_tracker:
                last_activity_tracker[chat_id] = current_time

