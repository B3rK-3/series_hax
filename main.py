# Python Kafka Consumer Example
# Install: pip install kafka-python

from kafka import KafkaConsumer
import json
import requests
import heapq
import threading
import time
from time import sleep
from functions import think_and_act, send_reminder

# API Configuration
base_url = "https://series-hackathon-service-202642739529.us-east1.run.app"
api_key = '6113d6ed-b505-4b92-ae29-21fbe76eb2fc'
sender = "+16463458837"
phone_numbers = ["+12017244539", "+14072724176"]

# Kafka Configuration
bootstrap_servers = 'pkc-619z3.us-east1.gcp.confluent.cloud:9092'
topic_name = 'team.team.0e56f514cd1d47b99623af887ce23c32'
ssl_user = 'QRHNR6BCKVHD4M3U'
api_secret = 'cfltTIivf3OHq6tr9fpASLxV4pp7vzPfvnz3cwT8+NAoOAJUCZwRuxuk1sSZTK+w'

# Dictionary to store chat_id to phone_numbers mapping
chat_mapping = {}

# Dictionary to store phone_number to chat_id mapping (for individual chats)
phone_to_chat = {}

# Priority queue: (timestamp, chat_id, phone_number)
priority_queue = []

# Default delay for reminders (in seconds)
REMINDER_DELAY = 5  # 5 seconds

# Flag to control the monitoring thread
stop_monitoring = False


def create_group_chat():
    """Create a group chat with the phone numbers and return the chat_id."""
    url = f"{base_url}/api/chats"
    payload = {
        "chat": {
            "display_name": "Demo Group Chat",
            "phone_numbers": phone_numbers
        },
        "message": {
            "text": "Group chat created for demo"
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
                timestamp, chat_id, phone = priority_queue[0]
                
                # If the timestamp has expired, pop it and send reminder
                if timestamp <= current_time:
                    heapq.heappop(priority_queue)
                    print(f"\n[REMINDER] Expired reminder for chat_id: {chat_id}, phone: {phone}")
                    send_reminder(chat_id, phone, phone_to_chat, chat_mapping[chat_id])
                    print(f"Priority queue size after removal: {len(priority_queue)}")
            
            # Sleep for a short period to avoid busy waiting
            sleep(1)
            
        except Exception as e:
            print(f"Error in monitoring thread: {e}")
            sleep(1)


# Initialize Consumer
consumer = KafkaConsumer(
    topic_name,
    bootstrap_servers=[bootstrap_servers],
    security_protocol='SASL_SSL',
    sasl_mechanism='PLAIN',
    sasl_plain_username=ssl_user,
    sasl_plain_password=api_secret,
    value_deserializer=lambda m: json.loads(m.decode('utf-8')),
    auto_offset_reset='earliest',
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
        chat_id = int(message_data.get('chat_id'))
        msg = message_data.get('text')
        from_phone = message_data.get('from_phone')
        
        print(f"Chat ID: {chat_id}, From: {from_phone}, Message: {msg}")
        
        # Call think_and_act with chat_id, message, from_phone, chat_mapping, and priority_queue
        if chat_id and msg and from_phone:
            think_and_act(chat_id, msg, from_phone, chat_mapping, priority_queue, REMINDER_DELAY)
            
            # Remove elements from priority queue with same chat_id and from_phone
            # Create a new queue without the matching elements
            new_queue = []
            for item in priority_queue:
                timestamp, qid, phone = item
                if not (qid == chat_id and phone == from_phone):
                    new_queue.append(item)
            
            # Rebuild the heap
            priority_queue.clear()
            heapq.heapify(new_queue)
            priority_queue.extend(new_queue)
            
            print(f"Removed entries for chat_id {chat_id} and phone {from_phone}")
            print(f"Priority queue size: {len(priority_queue)}")
        
except KeyboardInterrupt:
    print("\nStopping consumer...")
    stop_monitoring = True
    monitor_thread.join(timeout=5)
finally:
    consumer.close()
