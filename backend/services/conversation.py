from typing import AsyncGenerator
from anthropic.types import MessageParam
from backend.tools import tool_executor
from backend.utils.chat_helpers import add_user_message, add_assistant_message, ChatStreamFn
from backend.models.requests import ToolResultBlock


async def run_conversation(messages: list[MessageParam], stream_fn: ChatStreamFn) -> AsyncGenerator[str, None]:
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
