import asyncio
import gzip
from typing import Optional, Callable
import nats
from nats.errors import TimeoutError

NATS_URL = "nats://nats:4222"  # This should come from env in production

async def connect_to_nats() -> nats.NATS:
    return await nats.connect(NATS_URL)

async def publish_with_compression(nc: nats.NATS, subject: str, payload: bytes, priority: str = 'medium') -> None:
    compressed = gzip.compress(payload)
    priority_subject = f"{priority}.{subject}"
    await nc.publish(priority_subject, compressed)

async def subscribe_with_decompression(nc: nats.NATS, subject: str, queue: Optional[str] = None, cb: Callable = None) -> None:
    async def handler(msg):
        decompressed = gzip.decompress(msg.data)
        if cb:
            await cb(decompressed, msg)

    await nc.subscribe(subject, queue=queue, cb=handler)

# Example usage
# async def main():
#     nc = await connect_to_nats()
#     await publish_with_compression(nc, 'events', b'{"data": "important"}', priority='high')
#     await subscribe_with_decompression(nc, 'high.events', cb=process_message)
#     await nc.drain()