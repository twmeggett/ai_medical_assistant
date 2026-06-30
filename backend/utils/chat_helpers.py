import os
from typing import Callable, Literal
from dotenv import load_dotenv
from anthropic import AsyncAnthropic
from anthropic.types import MessageParam, TextBlock, TextBlockParam, ToolUseBlockParam
from anthropic.lib.streaming._messages import AsyncMessageStreamManager

load_dotenv()

ChatStreamFn = Callable[..., AsyncMessageStreamManager]
client = AsyncAnthropic()
model = os.getenv("CLAUDE_HAIKU_MODEL", "claude-haiku-4-5-20251001")


def chat_stream(
    messages: list[MessageParam],
    /,
    *,
    system: str | list[dict] | None = None,
    temperature: float = 1.0,
    stop_sequences: list[str] | None = None,
    tools: list[dict] | None = None,
    tool_choice: Literal["any", "auto", "tool", "none"] | None = None,
):
    params: dict[str, object] = {
        "model": model,
        "max_tokens": 1000,
        "messages": messages,
        "temperature": temperature,
    }

    if stop_sequences:
        params["stop_sequences"] = stop_sequences
    if tool_choice:
        params["tool_choice"] = tool_choice
    if tools:
        params["tools"] = tools
    if system:
        params["system"] = system

    return client.messages.stream(**params)  # type: ignore[arg-type]


def add_user_message(history: list[MessageParam], message) -> list[MessageParam]:
    user_message: MessageParam
    if isinstance(message, list):
        user_message = {"role": "user", "content": message}
    else:
        user_message = {"role": "user", "content": [{"type": "text", "text": message}]}
    return [*history, user_message]


def add_assistant_message(messages: list[MessageParam], message) -> None:
    assistant_message: MessageParam

    if isinstance(message, list):
        assistant_message = {
            "role": "assistant",
            "content": message,
        }
    elif hasattr(message, "content"):
        content_list: list[TextBlockParam | ToolUseBlockParam] = []
        for block in message.content:
            if block.type == "text":
                content_list.append({"type": "text", "text": block.text})
            elif block.type == "tool_use":
                content_list.append(
                    {
                        "type": "tool_use",
                        "id": block.id,
                        "name": block.name,
                        "input": block.input,
                    }
                )
        assistant_message = {
            "role": "assistant",
            "content": content_list,
        }
    else:
        assistant_message = {
            "role": "assistant",
            "content": [{"type": "text", "text": message}],
        }
    messages.append(assistant_message)


def text_from_message(message) -> str:
    return "\n".join([block.text for block in message.content if isinstance(block, TextBlock)])
