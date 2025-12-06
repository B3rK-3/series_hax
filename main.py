# Python Kafka Consumer Example
# Install: pip install kafka-python

from kafka import KafkaConsumer
import json
import requests
from functions import think_and_act

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

print(f"Listening to topic: {topic_name}")
print("Waiting for messages... (Press Ctrl+C to stop)")

try:
    for message in consumer:
        print(f"\nReceived message:")
        print(f"Topic: {message.topic}")
        print(f"Partition: {message.partition}")
        print(f"Offset: {message.offset}")
        print(f"Value: {message.value}")
        
        # Extract chat_id and message from the received message
        chat_id = message.value.get('chat_id')
        msg = message.value.get('message')
        
        # Call think_and_act with chat_id and message
        if chat_id and msg:
            think_and_act(chat_id, msg)
        
except KeyboardInterrupt:
    print("\nStopping consumer...")
finally:
    consumer.close()
