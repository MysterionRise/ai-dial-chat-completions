import json
import aiohttp
import requests

from task.clients.base import BaseClient
from task.constants import DIAL_ENDPOINT
from task.models.message import Message
from task.models.role import Role


class CustomDialClient(BaseClient):
    _endpoint: str

    def __init__(self, deployment_name: str):
        super().__init__(deployment_name)
        self._endpoint = DIAL_ENDPOINT + f"/openai/deployments/{deployment_name}/chat/completions"

    def get_completion(self, messages: list[Message]) -> Message:
        # 1. Create headers dict with api-key and Content-Type
        headers = {
            "api-key": self._api_key,
            "Content-Type": "application/json"
        }

        # 2. Create request_data dictionary
        request_data = {
            "messages": [msg.to_dict() for msg in messages]
        }

        print(f"Request: {self._endpoint}")
        print(f"Headers: {headers}")
        print(f"Body: {json.dumps(request_data, indent=2)}")

        # 3. Make POST request
        response = requests.post(
            self._endpoint,
            headers=headers,
            json=request_data
        )

        # 5. If status code != 200 then raise Exception
        if response.status_code != 200:
            raise Exception(f"HTTP {response.status_code}: {response.text}")

        print(f"Response: {response.json()}")

        # 4. Get content from response, print it and return message with assistant role
        response_json = response.json()
        if not response_json.get("choices"):
            raise Exception("No choices in response found")

        content = response_json["choices"][0]["message"]["content"]
        print(f"AI: {content}")
        return Message(Role.AI, content)

    async def stream_completion(self, messages: list[Message]) -> Message:
        # 1. Create headers dict with api-key and Content-Type
        headers = {
            "api-key": self._api_key,
            "Content-Type": "application/json"
        }

        # 2. Create request_data dictionary with stream=True
        request_data = {
            "stream": True,
            "messages": [msg.to_dict() for msg in messages]
        }

        print(f"Request: {self._endpoint}")
        print(f"Headers: {headers}")
        print(f"Body: {json.dumps(request_data, indent=2)}")

        # 3. Create empty list called 'contents' to store content snippets
        contents = []

        # 4. Create aiohttp.ClientSession()
        async with aiohttp.ClientSession() as session:
            # 5. Inside session, make POST request
            async with session.post(
                self._endpoint,
                json=request_data,
                headers=headers
            ) as response:
                # 6. Get content from chunks and collect them
                async for line in response.content:
                    line_str = line.decode('utf-8').strip()

                    if not line_str or line_str == "data: [DONE]":
                        continue

                    if line_str.startswith("data: "):
                        json_str = line_str[6:]  # Remove 'data: ' prefix (6 chars)
                        try:
                            chunk_data = json.loads(json_str)
                            content_part = self._get_content_snippet(chunk_data)
                            if content_part:
                                print(content_part, end="", flush=True)
                                contents.append(content_part)
                        except json.JSONDecodeError:
                            pass

        # Print empty row (end of streaming)
        print()

        # Return Message with assistant role and collected content
        full_content = "".join(contents)
        return Message(Role.AI, full_content)

    def _get_content_snippet(self, chunk_data: dict) -> str | None:
        """Parse streaming data chunks to extract content."""
        try:
            if "choices" in chunk_data and len(chunk_data["choices"]) > 0:
                choice = chunk_data["choices"][0]
                if "delta" in choice and "content" in choice["delta"]:
                    return choice["delta"]["content"]
        except (KeyError, TypeError, IndexError):
            pass
        return None

