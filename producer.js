// Node.js Kafka Producer Example
// Install: npm install kafkajs

const { Kafka } = require('kafkajs');

// Kafka Configuration
const kafka = new Kafka({
  clientId: 'team-client-0e56f514cd1d47b99623af887ce23c32',
  brokers: 'pkc-619z3.us-east1.gcp.confluent.cloud:9092'.split(','),
  ssl: true,
  sasl: {
    mechanism: 'plain',
    username: '6113d6ed-b505-4b92-ae29-21fbe76eb2fc',
    password: 'cfltTIivf3OHq6tr9fpASLxV4pp7vzPfvnz3cwT8+NAoOAJUCZwRuxuk1sSZTK+w'
  }
});

const producer = kafka.producer();

async function sendMessage() {
  await producer.connect();
  
  const message = {
    event: 'test_message',
    data: {
      message: 'Hello from Baklava Plaintain!',
      timestamp: new Date().toISOString()
    }
  };

  try {
    const result = await producer.send({
      topic: 'team.team.0e56f514cd1d47b99623af887ce23c32',
      messages: [
        {
          value: JSON.stringify(message)
        }
      ]
    });

    console.log('Message sent successfully!');
    console.log('Result:', result);
  } catch (error) {
    console.error('Error sending message:', error);
  } finally {
    await producer.disconnect();
  }
}

sendMessage();