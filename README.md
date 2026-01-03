# series_hax

This project was built for the **series.so exclusive hackathon**, an elite gathering of 100 developers.

## Overview

`series_hax` is a messaging integration layer that bridges Kafka event streams with the Series iMessage API. It allows for automated message processing, group chat creation, and intelligent response generation.

### Key Features

-   **Kafka Integration**: Listens to real-time message topics.
-   **Series iMessage API**: Sends and receives messages via the Series platform.
-   **Dynamic Response Logic**: Plug-and-play function architecture for processing incoming messages (see `functions.py`).
-   **Group Chat Management**: Programmatic creation and management of group conversations.

## Architecture

-   `main.py`: The core Kafka consumer and event loop.
-   `producer.py`: Utility for pushing messages to the Kafka topic.
-   `send_sms.py`: Quick-start script for testing outbound iMessage delivery.
-   `functions.py`: Contains the logic for processing messages (e.g., `think_and_act`).

## Setup

1. **Install dependencies**:

    ```bash
    pip install -r requirements.txt
    ```

2. **Environment Variables**:
   Create a `.env` file with the following:

    ```env
    SERIES_BASE_URL=your_series_base_url
    SERIES_API_KEY=your_series_api_key
    KAFKA_BOOTSTRAP_SERVERS=your_kafka_bootstrap_servers
    KAFKA_TOPIC_NAME=your_kafka_topic_name
    KAFKA_USERNAME=your_kafka_username
    KAFKA_SECRET=your_kafka_secret
    ```

3. **Run the Consumer**:
    ```bash
    python main.py
    ```

## Hackathon Context

Developed during the First Series.so Hackathon, this project explores the boundaries of programmatic messaging and real-time event processing.
