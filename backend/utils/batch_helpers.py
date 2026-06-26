import asyncio
from anthropic import AsyncAnthropic
from anthropic.types import MessageParam
from anthropic.types.messages.message_batch import MessageBatch
from anthropic.types.messages.message_batch_individual_response import MessageBatchIndividualResponse
from anthropic.types.messages.batch_create_params import Request
from anthropic.types.message_create_params import MessageCreateParamsNonStreaming

client = AsyncAnthropic()
model = "claude-sonnet-4-5"


def build_request(custom_id: str, messages: list[MessageParam], system: str | None = None) -> Request:
    params: MessageCreateParamsNonStreaming = {
        "model": model,
        "max_tokens": 1024,
        "messages": messages,
    }
    if system:
        params["system"] = system
    return {"custom_id": custom_id, "params": params}


async def create_batch(requests: list[Request]) -> MessageBatch:
    return await client.messages.batches.create(requests=requests)


async def get_batch(batch_id: str) -> MessageBatch:
    return await client.messages.batches.retrieve(batch_id)

async def list_batches() -> list[MessageBatch]:
    batches = []
    async for batch in await client.messages.batches.list():
        batches.append(batch)
    return batches

async def list_active_batches() -> list[MessageBatch]:
    batches = []
    async for batch in await client.messages.batches.list():
        if batch.processing_status == "in_progress":
            batches.append(batch)
    return batches

async def wait_for_batch(batch_id: str, poll_interval: int = 30) -> MessageBatch:
    while True:
        batch = await get_batch(batch_id)
        if batch.processing_status == "ended":
            return batch
        await asyncio.sleep(poll_interval)


async def get_batch_results(batch_id: str) -> list[MessageBatchIndividualResponse]:
    results = []
    async for result in await client.messages.batches.results(batch_id):
        results.append(result)
    return results


async def cancel_batch(batch_id: str) -> MessageBatch:
    return await client.messages.batches.cancel(batch_id)
