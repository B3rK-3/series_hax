# Python Kafka Producer Example
# Install: pip install kafka-python

from kafka import KafkaProducer
import json

# Kafka Configuration
bootstrap_servers = 'pkc-619z3.us-east1.gcp.confluent.cloud:9092'
topic_name = 'team.team.0e56f514cd1d47b99623af887ce23c32'
api_key = 'QRHNR6BCKVHD4M3U'
api_secret = 'cfltTIivf3OHq6tr9fpASLxV4pp7vzPfvnz3cwT8+NAoOAJUCZwRuxuk1sSZTK+w'

# Initialize Producer
print("Initializing Kafka producer...")
print(f"Connecting to: {bootstrap_servers}")
producer = KafkaProducer(
    bootstrap_servers=[bootstrap_servers],  # Changed: use list directly
    security_protocol='SASL_SSL',
    sasl_mechanism='PLAIN',
    sasl_plain_username=api_key,
    sasl_plain_password=api_secret,
    value_serializer=lambda v: json.dumps(v).encode('utf-8'),
    request_timeout_ms=30000,  # 30 seconds
    max_block_ms=30000,  # 30 seconds for metadata
    api_version_auto_timeout_ms=10000  # API version detection timeout
)
print("Producer initialized successfully!")

# Send a message
print(f"Sending message to topic: {topic_name}")
message = {
    'event': 'test_message',
    'data': {
        'message': '222222!',
        'timestamp': '2024-01-01T00:00:00Z'
    }
}

try:
    # Force metadata refresh before sending
    print("Fetching topic metadata...")
    producer.partitions_for(topic_name)
    print("Metadata fetched successfully!")

    # Send the message
    print("Sending message...")
    future = producer.send(topic_name, value=message)
    record_metadata = future.get(timeout=30)
    print(f"Message sent successfully!")
    print(f"Topic: {record_metadata.topic}")
    print(f"Partition: {record_metadata.partition}")
    print(f"Offset: {record_metadata.offset}")
except Exception as e:
    print(f"Error sending message: {e}")
    import traceback
    traceback.print_exc()
finally:
    print("Closing producer...")
    producer.close()
    print("Producer closed.")