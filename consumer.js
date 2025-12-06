// Node.js Kafka Consumer Example
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

const consumer = kafka.consumer({ 
  groupId: 'team-cg-0e56f514cd1d47b99623af887ce23c32'
});

async function consumeMessages() {
  await consumer.connect();
  await consumer.subscribe({ 
    topic: 'team.team.0e56f514cd1d47b99623af887ce23c32',
    fromBeginning: true 
  });

  console.log('Listening to topic: team.team.0e56f514cd1d47b99623af887ce23c32');
  console.log('Waiting for messages... (Press Ctrl+C to stop)');

  await consumer.run({
    eachMessage: async ({ topic, partition, message }) => {
      console.log('\nReceived message:');
      console.log('Topic:', topic);
      console.log('Partition:', partition);
      console.log('Offset:', message.offset);
      console.log('Value:', message.value.toString());
    }
  });
}

consumeMessages().catch(console.error);