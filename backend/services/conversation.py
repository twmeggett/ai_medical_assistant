import asyncpg
from typing import AsyncGenerator
from anthropic.types import MessageParam
from backend.tools import tool_executor
from backend.utils.chat_helpers import add_user_message, add_assistant_message, text_from_message, ChatStreamFn
from backend.models import ToolResultBlock, ChatMessage, ConversationHistory
from backend.models.domain import MessageRole
from backend.db.connector import get_pool
from backend.db.conversations import create_conversation, get_full_conversation
from backend.db.messages import save_message


async def run_conversation(conversation_id: str, user_prompt: str, stream_fn: ChatStreamFn) -> AsyncGenerator[str, None]:
    async with get_pool().acquire() as conn:
        conversation = await get_full_conversation(conn, conversation_id)
        if conversation is None:
            raise ValueError(f"Conversation {conversation_id} not found")

        user_message = conversation.add_message(MessageRole.USER, user_prompt)
        await save_message(conn, conversation_id, user_message)

    conversation.truncate_to_token_budget()
    messages: list[MessageParam] = conversation.to_anthropic_messages()

    while True:
        if not messages or messages[-1].get("role") != "user":
            break

        async with stream_fn(messages) as stream:
            async for chunk in stream:
                if chunk.type == "text":
                    yield chunk.text
                if chunk.type == "content_block_start":
                    if chunk.content_block.type == "tool_use":
                        yield f'\n>>> Tool Call: "{chunk.content_block.name}"'
                if chunk.type == "input_json" and chunk.partial_json:
                    yield chunk.partial_json
                if chunk.type == "content_block_stop":
                    yield "\n"

            response = await stream.get_final_message()

            add_assistant_message(messages, response)

            response_text = text_from_message(response)
            if response_text:
                async with get_pool().acquire() as conn:
                    assistant_message = conversation.add_message(MessageRole.ASSISTANT, response_text)
                    await save_message(conn, conversation_id, assistant_message)

            if response.stop_reason == "tool_use":
                tool_result_blocks: list[ToolResultBlock] = []
                for block in response.content:
                    if block.type != "tool_use":
                        continue
                    tool_result_blocks.append(
                        await tool_executor(
                            tool_name=block.name,
                            tool_use_id=block.id,
                            raw_input=block.input,
                        )
                    )
                messages = add_user_message(messages, tool_result_blocks)
            else:
                break


async def start_conversation(pool: asyncpg.Pool, msg: ChatMessage, user_id="1"):
    conversation = ConversationHistory(user_id=user_id)
    async with pool.acquire() as conn:
        async with conn.transaction():
            await create_conversation(conn, conversation)
            for msg in conversation.messages:
                await save_message(conn, conversation.conversation_id, msg)
