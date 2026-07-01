import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from anthropic.types import MessageParam
from backend.services.conversation import run_conversation


class _MockStream:
    """Async-iterable stream mock that also supports get_final_message()."""

    def __init__(self, chunks: list, stop_reason: str = "end_turn", tool_blocks: list | None = None):
        self._iter = iter(chunks)
        final = MagicMock()
        final.stop_reason = stop_reason
        final.content = tool_blocks or []
        self._final = final

    def __aiter__(self):
        return self

    async def __anext__(self):
        try:
            return next(self._iter)
        except StopIteration:
            raise StopAsyncIteration

    async def get_final_message(self):
        return self._final


def _make_stream(chunks: list, stop_reason: str = "end_turn", tool_blocks: list | None = None):
    """Return an async context manager that yields a _MockStream."""
    stream = _MockStream(chunks, stop_reason, tool_blocks)
    ctx = AsyncMock()
    ctx.__aenter__ = AsyncMock(return_value=stream)
    ctx.__aexit__ = AsyncMock(return_value=False)
    return ctx


def _text_chunk(text: str) -> MagicMock:
    chunk = MagicMock()
    chunk.type = "text"
    chunk.text = text
    return chunk


def _messages() -> list[MessageParam]:
    return [{"role": "user", "content": "What is aspirin?"}]


@pytest.mark.asyncio
async def test_yields_text_chunks():
    stream_fn = MagicMock(return_value=_make_stream(
        [_text_chunk("Aspirin"), _text_chunk(" is an NSAID.")]
    ))
    output = []
    async for chunk in run_conversation(_messages(), stream_fn):
        output.append(chunk)
    assert "Aspirin" in output
    assert " is an NSAID." in output


@pytest.mark.asyncio
async def test_on_assistant_message_callback_called():
    stream_fn = MagicMock(return_value=_make_stream([_text_chunk("Hello patient.")]))
    callback = AsyncMock()
    with patch("backend.services.conversation.text_from_message", return_value="Hello patient."):
        async for _ in run_conversation(_messages(), stream_fn, on_assistant_message=callback):
            pass
    callback.assert_awaited_once_with("Hello patient.")


@pytest.mark.asyncio
async def test_on_assistant_message_not_called_when_none():
    stream_fn = MagicMock(return_value=_make_stream([_text_chunk("No callback.")]))
    results = []
    async for chunk in run_conversation(_messages(), stream_fn, on_assistant_message=None):
        results.append(chunk)
    assert len(results) > 0


@pytest.mark.asyncio
async def test_exits_when_messages_list_empty():
    stream_fn = MagicMock()
    results = []
    async for chunk in run_conversation([], stream_fn):
        results.append(chunk)
    assert results == []
    stream_fn.assert_not_called()


@pytest.mark.asyncio
async def test_exits_when_last_message_not_user():
    stream_fn = MagicMock()
    messages: list[MessageParam] = [{"role": "assistant", "content": "I already responded."}]
    results = []
    async for chunk in run_conversation(messages, stream_fn):
        results.append(chunk)
    assert results == []
    stream_fn.assert_not_called()


@pytest.mark.asyncio
async def test_tool_use_loop_runs_then_ends():
    tool_block = MagicMock()
    tool_block.type = "tool_use"
    tool_block.name = "search_journals"
    tool_block.id = "tu_1"
    tool_block.input = {"query": "aspirin", "max_results": 1}

    tool_stream = _make_stream(
        [_text_chunk("")],
        stop_reason="tool_use",
        tool_blocks=[tool_block],
    )
    end_stream = _make_stream([_text_chunk("Final answer.")])

    call_count = 0

    def stream_fn(messages):
        nonlocal call_count
        call_count += 1
        return tool_stream if call_count == 1 else end_stream

    mock_result = MagicMock()
    mock_result.model_dump = MagicMock(
        return_value={"type": "tool_result", "tool_use_id": "tu_1", "content": "results"}
    )

    with (
        patch("backend.services.conversation.tool_executor", new=AsyncMock(return_value=mock_result)),
        patch("backend.services.conversation.add_assistant_message"),
        patch("backend.services.conversation.text_from_message", return_value=""),
    ):
        results = []
        async for chunk in run_conversation(_messages(), stream_fn):
            results.append(chunk)

    assert call_count == 2
    assert "Final answer." in results
