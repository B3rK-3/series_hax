from kafka import KafkaConsumer
import json
import requests
import heapq
import threading
import time
from time import sleep
from datetime import datetime, timezone
import os
from dotenv import load_dotenv
from src import (
    think_and_act, send_reminder, priority_queue, get_chat_history,
    get_ai_response, scan_inactive_chats, add_message_to_chat,
    ContactManager, MemoryExtractor, EnhancedMemoryEngine
)

# Load environment variables
load_dotenv()

# Load AI prompt from file
with open('config/ai_prompt.txt', 'r') as f:
    ai_prompt = f.read()

# API Configuration
base_url = os.getenv('SERIES_BASE_URL')
api_key = os.getenv('SERIES_API_KEY')
sender = os.getenv('SENDER_PHONE')
phone_numbers = os.getenv('PHONE_NUMBERS', '').split(',')
gemini_api_key = os.getenv('GEMINI_API_KEY', '')

# Kafka Configuration
bootstrap_servers = os.getenv('KAFKA_BOOTSTRAP_SERVERS')
topic_name = os.getenv('KAFKA_TOPIC')
ssl_user = os.getenv('KAFKA_SSL_USER')
api_secret = os.getenv('KAFKA_API_SECRET')

# Dictionary to store chat_id to phone_numbers mapping
chat_mapping = {}

# Dictionary to store phone_number to chat_id mapping (for individual chats)
phone_to_chat = {}

# Default delay for reminders (in seconds)
REMINDER_DELAY = 5  # 5 seconds

# Conversation starters configuration
CONVO_STARTERS = 60 * 60  # Check every 60 seconds
LAST_ACTIVITY = 15  # Consider chat inactive after 10 seconds

# Dictionary to track last activity time for each chat
last_activity_tracker = {}

# Flag to control the monitoring thread
stop_monitoring = False

# Memory extraction system
memory_extraction_queue = []
memory_extraction_enabled = os.getenv('MEMORY_EXTRACTION_ENABLED', 'true').lower() == 'true'
contact_manager = ContactManager()
memory_extractor = MemoryExtractor(gemini_api_key, contact_manager)
enhanced_memory = EnhancedMemoryEngine()


def create_group_chat():
    """Create a group chat with the phone numbers and individual chats for each phone number."""
    url = f"{base_url}/api/chats"
    payload = {
        "chat": {
            "display_name": "Demo Group Chat",
            "phone_numbers": phone_numbers
        },
        "message": {
            "text": "Group chat created!"
        },
        "send_from": sender
    }
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    
    try:
        print(f"Creating group chat with phone numbers: {phone_numbers}")
        r = requests.post(url, headers=headers, json=payload, timeout=15)
        print(f"HTTP {r.status_code}")
        
        if r.ok:
            response_data = r.json()
            chat_id = response_data.get('data', {}).get('id')
            
            if chat_id:
                chat_mapping[chat_id] = phone_numbers
                print(f"Group chat created successfully. Chat ID: {chat_id}")
                print(f"Chat mapping: {chat_mapping}")
                
                # Create individual chats for each phone number
                for phone in phone_numbers:
                    individual_payload = {
                        "chat": {
                            "phone_numbers": [phone]
                        },
                        "message": {
                            "text": "Hello!"
                        },
                        "send_from": sender
                    }
                    
                    try:
                        print(f"Creating individual chat with {phone}")
                        ind_r = requests.post(url, headers=headers, json=individual_payload, timeout=15)
                        print(f"HTTP {ind_r.status_code}")
                        
                        if ind_r.ok:
                            ind_response_data = ind_r.json()
                            ind_chat_id = ind_response_data.get('data', {}).get('id')
                            
                            if ind_chat_id:
                                phone_to_chat[phone] = ind_chat_id
                                print(f"Individual chat created for {phone}. Chat ID: {ind_chat_id}")
                            else:
                                print(f"Error: No chat ID in response for {phone}")
                        else:
                            print(f"Error creating individual chat for {phone}: {ind_r.text}")
                            
                    except Exception as e:
                        print(f"Failed to create individual chat for {phone}: {e}")
                
                print(f"Phone to chat mapping: {phone_to_chat}")
                return chat_id
            else:
                print("Error: No chat ID in response")
                return None
        else:
            print(f"Error creating chat: {r.text}")
            return None
            
    except Exception as e:
        print(f"Failed to create group chat: {e}")
        return None


def monitor_priority_queue():
    """Monitor the priority queue for expired timestamps and send reminders."""
    global stop_monitoring
    
    while not stop_monitoring:
        try:
            current_time = time.time()
            
            # Check if there are any items in the queue
            if priority_queue:
                # Peek at the top of the queue (smallest timestamp)
                timestamp, chat_id, phone, delay_seconds = priority_queue[0]
                
                # If the timestamp has expired, pop it and send reminder
                if timestamp <= current_time:
                    heapq.heappop(priority_queue)
                    print(f"\n[REMINDER] Expired reminder for chat_id: {chat_id}, phone: {phone}, delay: {delay_seconds}s")
                    if chat_id in chat_mapping:
                        send_reminder(chat_id, phone, phone_to_chat, chat_mapping[chat_id], delay_seconds)
                    else:
                        chat_history = get_chat_history(chat_id)
                        print("Chat history for AI response:", chat_history)
                        prompt = "what is the phone number the user has to respond to? give only the phone number"
                        response_phone = get_ai_response(prompt, chat_history)
                        
                        # Find chat_id where both response_phone and phone exist in chat_mapping
                        found_chat_id = None
                        for cid, phones in chat_mapping.items():
                            if response_phone in phones and phone in phones:
                                found_chat_id = cid
                                break
                        
                        print(f"[MONITOR] Found chat_id containing both {response_phone} and {phone}: {found_chat_id}")
                        
                        send_reminder(found_chat_id, phone, phone_to_chat, [response_phone], delay_seconds)
                    print(f"Priority queue size after removal: {len(priority_queue)}")
            
            # Sleep for a short period to avoid busy waiting
            sleep(1)
            
        except Exception as e:
            print(f"Error in monitoring thread: {e}")
            sleep(1)


def scan_chats_for_inactivity():
    """Periodically scan chats for inactivity and send conversation starters."""
    global stop_monitoring

    while not stop_monitoring:
        try:
            scan_inactive_chats(chat_mapping, last_activity_tracker, LAST_ACTIVITY, phone_to_chat)
            # Sleep for CONVO_STARTERS seconds before checking again
            sleep(CONVO_STARTERS)
        except Exception as e:
            print(f"Error in chat inactivity scanner: {e}")
            sleep(CONVO_STARTERS)


def extract_memories_worker():
    """Background worker for batch memory extraction."""
    global stop_monitoring

    while not stop_monitoring:
        try:
            # Process whenever we have messages
            if memory_extraction_queue:
                print(f"[MEMORY] Processing batch of {len(memory_extraction_queue)} messages...")

                # Group messages by chat_id
                grouped = {}
                batch = memory_extraction_queue.copy()
                memory_extraction_queue.clear()

                for item in batch:
                    chat_id = item['chat_id']
                    if chat_id not in grouped:
                        grouped[chat_id] = []
                    grouped[chat_id].append(item)

                # Extract memories for each chat
                for chat_id, messages in grouped.items():
                    chat_history = get_chat_history(chat_id)
                    memories = memory_extractor.analyze_messages(chat_id, messages, chat_history)

                    for memory in memories:
                        enhanced_memory.save_memory(memory)

                print(f"[MEMORY] Batch processing complete")

            sleep(30)  # Check every 30 seconds

        except Exception as e:
            print(f"[MEMORY] Error in extraction worker: {e}")
            sleep(30)


# Initialize Consumer
consumer = KafkaConsumer(
    topic_name,
    bootstrap_servers=[bootstrap_servers],
    security_protocol='SASL_SSL',
    sasl_mechanism='PLAIN',
    sasl_plain_username=ssl_user,
    sasl_plain_password=api_secret,
    value_deserializer=lambda m: json.loads(m.decode('utf-8')),
    auto_offset_reset='latest',
    enable_auto_commit=True,
    group_id='team-cg-0e56f514cd1d47b99623af887ce23c32',
    request_timeout_ms=30000,
    api_version_auto_timeout_ms=10000
)

print("Creating group chat...")
create_group_chat()

# Start monitoring thread
print("Starting priority queue monitoring thread...")
monitor_thread = threading.Thread(target=monitor_priority_queue, daemon=True)
monitor_thread.start()

# Start inactivity scanner thread
print("Starting chat inactivity scanner thread...")
scanner_thread = threading.Thread(target=scan_chats_for_inactivity, daemon=True)
scanner_thread.start()

# Start memory extraction thread
if memory_extraction_enabled:
    print("Starting memory extraction worker...")
    extraction_thread = threading.Thread(target=extract_memories_worker, daemon=True)
    extraction_thread.start()
else:
    print("Memory extraction disabled")

print(f"Listening to topic: {topic_name}")
print("Waiting for messages... (Press Ctrl+C to stop)")

try:
    for message in consumer:
        print(f"\nReceived message:")
        print(f"Topic: {message.topic}")
        print(f"Partition: {message.partition}")
        print(f"Offset: {message.offset}")
        print(f"Value: {message.value}")
        
        # Extract data from the received message
        message_data = message.value.get('data', {})
        from_phone = message_data.get('from_phone')
        chat_id = int(message_data.get('chat_id'))
        msg = message_data.get('text')
        sent_at = message_data.get('sent_at')
        print(f"Parsed - Chat ID: {chat_id}, From: {from_phone}, Message: {msg}, Sent At: {sent_at}")
        
        # Check if message is not older than 1 minute
        if sent_at:
            try:
                # Parse the sent_at timestamp
                sent_time = datetime.strptime(sent_at, '%Y-%m-%d %H:%M:%S %z')
                current_time = datetime.now(timezone.utc)
                time_diff = (current_time - sent_time).total_seconds()
                print(f"Message time difference: {time_diff} seconds")
                
                if time_diff > 5:
                    print(f"Ignoring message from {time_diff:.1f}s ago (older than 1 minute)")
                    continue
            except Exception as e:
                print(f"Error parsing timestamp: {e}")
        
        print(f"Chat ID: {chat_id}, From: {from_phone}, Message: {msg}")
        
        # Add message to local chat history
        if chat_id and msg and from_phone:
            add_message_to_chat(chat_id, {
                'text': msg,
                'sent_from': from_phone,
                'sent_at': sent_at
            })

            # Queue for memory extraction
            if memory_extraction_enabled:
                memory_extraction_queue.append({
                    'chat_id': chat_id,
                    'phone': from_phone,
                    'message': msg,
                    'timestamp': sent_at
                })

        # Call think_and_act with chat_id, message, from_phone, chat_mapping, and priority_queue
        if chat_id and msg and from_phone:
            # Update last activity time for this chat
            last_activity_tracker[chat_id] = time.time()
            
            # Remove elements from priority queue with same chat_id and from_phone
            # Create a new queue without the matching elements
            # new_queue = []
            # for item in priority_queue:
            #     timestamp, qid, phone, delay_seconds = item
            #     if not (qid == chat_id and phone == from_phone):
            #         new_queue.append(item)
            
            # # Rebuild the heap
            # priority_queue.clear()
            # heapq.heapify(new_queue)
            # priority_queue.extend(new_queue)


            think_and_act(chat_id, msg, from_phone, chat_mapping, priority_queue, REMINDER_DELAY, ai_prompt)
            
            # Rebuild the heap after think_and_act may have modified it
            heapq.heapify(priority_queue)
            
            print(f"Removed entries for chat_id {chat_id} and phone {from_phone}")
            print(f"Priority queue size: {len(priority_queue)}")
        
except KeyboardInterrupt:
    print("\nStopping consumer...")
    stop_monitoring = True
    monitor_thread.join(timeout=5)
finally:
    consumer.close()
