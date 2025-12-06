# Python Kafka Consumer Example
# Install: pip install kafka-python

from kafka import KafkaConsumer
import json

# Kafka Configuration
bootstrap_servers = 'pkc-619z3.us-east1.gcp.confluent.cloud:9092'
topic_name = 'team.team.0e56f514cd1d47b99623af887ce23c32'
ssl_user = 'QRHNR6BCKVHD4M3U'
api_secret = 'cfltTIivf3OHq6tr9fpASLxV4pp7vzPfvnz3cwT8+NAoOAJUCZwRuxuk1sSZTK+w'

# Initialize Consumer
consumer = KafkaConsumer(
    topic_name,
    bootstrap_servers=[bootstrap_servers],  # Changed: use list directly
    security_protocol='SASL_SSL',
    sasl_mechanism='PLAIN',
    sasl_plain_username=ssl_user,
    sasl_plain_password=api_secret,
    value_deserializer=lambda m: json.loads(m.decode('utf-8')),
    auto_offset_reset='earliest',
    enable_auto_commit=True,
    group_id='team-cg-0e56f514cd1d47b99623af887ce23c32',
    request_timeout_ms=30000,  # Added: 30 seconds
    api_version_auto_timeout_ms=10000  # Added: API version detection timeout
)

print(f"Listening to topic: {topic_name}")
print("Waiting for messages... (Press Ctrl+C to stop)")

try:
    for message in consumer:
        print(f"\nReceived message:")
        print(f"Topic: {message.topic}")
        print(f"Partition: {message.partition}")
        print(f"Offset: {message.offset}")
        print(f"Value: {message.value}")
except KeyboardInterrupt:
    print("\nStopping consumer...")
finally:
    consumer.close()