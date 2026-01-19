from aidial_client import Dial, AsyncDial

from task.clients.base import BaseClient
from task.constants import DIAL_ENDPOINT
from task.models.message import Message
from task.models.role import Role


class DialClient(BaseClient):

    def __init__(self, deployment_name: str):
        super().__init__(deployment_name)
        # Documentation: https://pypi.org/project/aidial-client/
        # 1. Create Dial client
        self._client = Dial(
            api_key=self._api_key,
            base_url=DIAL_ENDPOINT
        )
        # 2. Create AsyncDial client
        self._async_client = AsyncDial(
            api_key=self._api_key,
            base_url=DIAL_ENDPOINT
        )

    def get_completion(self, messages: list[Message]) -> Message:
        # 1. Create chat completions with client
        converted_messages = [msg.to_dict() for msg in messages]
        response = self._client.chat.completions.create(
            deployment_name=self._deployment_name,
            messages=converted_messages
        )

        # 3. If choices are not present then raise Exception
        if not response.choices:
            raise Exception("No choices in response found")

        # 2. Get content from response, print it and return message with assistant role
        content = response.choices[0].message.content
        print(f"AI: {content}")
        return Message(Role.AI, content)

    async def stream_completion(self, messages: list[Message]) -> Message:
        # 1. Create chat completions with async client (with stream=True)
        converted_messages = [msg.to_dict() for msg in messages]

        # 2. Create array with `contents` name (collect all content chunks)
        contents = []

        # 3. Make async loop from chunks
        response = await self._async_client.chat.completions.create(
            deployment_name=self._deployment_name,
            messages=converted_messages,
            stream=True
        )

        async for chunk in response:
            # 4. Print content chunk and collect it in contents array
            if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                content_part = chunk.choices[0].delta.content
                print(content_part, end="", flush=True)
                contents.append(content_part)

        # 5. Print empty row (end of streaming)
        print()

        # 6. Return Message with assistant role and collected content
        full_content = "".join(contents)
        return Message(Role.AI, full_content)
