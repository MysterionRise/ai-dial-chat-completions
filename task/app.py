import asyncio

from task.clients.client import DialClient
from task.constants import DEFAULT_SYSTEM_PROMPT
from task.models.conversation import Conversation
from task.models.message import Message
from task.models.role import Role


async def start(stream: bool) -> None:
    # 1.1. Create DialClient
    client = DialClient("gpt-4o")

    # 1.2. Create CustomDialClient (using the custom HTTP implementation)
    from task.clients.custom_client import CustomDialClient
    # custom_client = CustomDialClient("gpt-4o")

    # 2. Create Conversation object
    conversation = Conversation()

    # 3. Get System prompt from console or use default
    system_prompt_input = input("Provide System prompt or press 'enter' to continue.\n> ").strip()
    system_prompt = system_prompt_input if system_prompt_input else DEFAULT_SYSTEM_PROMPT
    conversation.add_message(Message(Role.SYSTEM, system_prompt))

    # 4. Use infinite cycle and get user message from console
    print("\nType your question or 'exit' to quit.")
    while True:
        user_input = input("> ").strip()

        # 5. If user message is `exit` then stop the loop
        if user_input.lower() == "exit":
            print("Exiting the chat. Goodbye!")
            break

        # 6. Add user message to conversation history (role 'user')
        conversation.add_message(Message(Role.USER, user_input))

        # 7. If `stream` param is true -> call DialClient#stream_completion()
        #    else -> call DialClient#get_completion()
        if stream:
            ai_message = await client.stream_completion(conversation.get_messages())
        else:
            ai_message = client.get_completion(conversation.get_messages())

        # 8. Add generated message to history
        conversation.add_message(ai_message)
        print()


asyncio.run(
    start(True)
)
