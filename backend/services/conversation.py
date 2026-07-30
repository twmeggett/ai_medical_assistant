from typing import AsyncGenerator, Awaitable, Callable
from anthropic.types import MessageParam
from backend.tools import tool_executor
from backend.utils.chat_helpers import add_user_message, add_assistant_message, text_from_message, ChatStreamFn
from backend.models import ToolResultBlock


MAX_TOOL_ITERATIONS = 15


async def run_conversation(
    messages: list[MessageParam],
    stream_fn: ChatStreamFn,
    on_assistant_message: Callable[[str], Awaitable[None]] | None = None,
    max_iterations: int = MAX_TOOL_ITERATIONS,
) -> AsyncGenerator[str, None]:
    for _ in range(max_iterations):
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
            if response_text and on_assistant_message:
                await on_assistant_message(response_text)

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
                messages = add_user_message(messages, [b.model_dump() for b in tool_result_blocks])
            else:
                break
    else:
        yield "\n>>> Reached the maximum number of tool calls for this turn; stopping here."
