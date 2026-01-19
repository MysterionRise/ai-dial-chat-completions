# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python CLI application for building a chat interface that integrates with the DIAL API (EPAM's OpenAI-compatible chat completion service). The application supports both synchronous and streaming responses from LLMs.

## Setup and Common Commands

### Environment Setup

**Python version requirement: 3.11 or 3.12** (The aidial-client library has compatibility issues with Python 3.14+)

```bash
# Create virtual environment with Python 3.12
python3.12 -m venv .venv

# Activate virtual environment (macOS/Linux)
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Running the Application

```bash
# Run with streaming enabled (real-time response output)
python -m task.app

# Alternative: explicit streaming mode
python -m task.app --stream true
```

### Configuration

The application loads the DIAL API key from a `.env` file in the project root using `python-dotenv`. Create a `.env` file:

```bash
# .env
DIAL_API_KEY="your_api_key_here"
```

Alternatively, set as an environment variable:

```bash
export DIAL_API_KEY="your_api_key_here"
```

The API key is read from the `DIAL_API_KEY` environment variable in `task/constants.py`. Without it, the application will raise a `ValueError` when initializing any client.

## Architecture Overview

### Data Models Layer (`task/models/`)

- **`role.py`**: `Role` enum defines message roles (`SYSTEM`, `USER`, `AI`)
- **`message.py`**: `Message` dataclass represents a single message with `role` and `content` fields. Has `to_dict()` method for API serialization
- **`conversation.py`**: `Conversation` dataclass manages conversation history with unique ID and list of messages. Provides `add_message()` and `get_messages()` methods

### Client Layer (`task/clients/`)

The application uses two interchangeable implementations of the DIAL API client, both inheriting from `BaseClient`:

1. **`DialClient` (in `client.py`)**: Uses the `aidial-client` library
   - `get_completion(messages)`: Synchronous API call
   - `stream_completion(messages)`: Asynchronous streaming API call with real-time output

2. **`CustomDialClient` (in `custom_client.py`)**: Raw HTTP implementation using `requests` and `aiohttp`
   - Manually constructs HTTP requests to `https://ai-proxy.lab.epam.com/openai/deployments/{deployment}/chat/completions`
   - Includes headers with `api-key` and `Content-Type: application/json`
   - Streams responses parse the `data: ` prefix (6 characters) from each chunk, ending with `data: [DONE]`

### Application Flow (`task/app.py`)

The `start(stream: bool)` async function orchestrates the conversation loop:

1. Initializes a client and conversation object
2. Loads or uses default system prompt
3. Enters loop: reads user input, adds to conversation history
4. Calls either `get_completion()` or `stream_completion()` depending on `stream` parameter
5. Adds AI response to conversation history
6. Continues until user enters "exit"

### Key Implementation Details

- **Message serialization**: Use `message.to_dict()` to convert `Message` objects to API-compatible dictionaries
- **Streaming response handling**: Raw streaming chunks are prefixed with `data: ` (remove 6 characters to get JSON); final chunk is `data: [DONE]`
- **Conversation context**: All messages are accumulated in the `Conversation` object and sent with each API request so the LLM maintains context
- **Error handling**: Both clients should raise `Exception` if response status is not 200 or if choices are missing from the response

## Testing Scenarios

README.md includes two test scenarios in the "Testing" section:
- **Calculator**: Tests numeric-only responses with multi-turn math operations
- **Ongoing Technical Troubleshooting**: Tests natural language Q&A with context retention across turns

Run these by providing the appropriate system prompt when the app starts.

## Dependencies

- `requests==2.28.0`: Synchronous HTTP requests
- `aiohttp==3.13.2`: Asynchronous HTTP requests
- `aidial-client==0.3.0`: Official DIAL client library

Refer to the [aidial-client documentation](https://pypi.org/project/aidial-client/) for API usage patterns when implementing the `DialClient` wrapper.

## DIAL API Reference

- **Endpoint**: `POST https://ai-proxy.lab.epam.com/openai/deployments/{deployment}/chat/completions`
- **Authentication**: `api-key` header (from `DIAL_API_KEY` environment variable)
- **Response format (non-streaming)**: Standard OpenAI chat completion format with `choices[0].message.content`
- **Response format (streaming)**: Server-sent events with JSON chunks prefixed by `data: ` string
