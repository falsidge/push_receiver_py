
import asyncio
from . import register, listen
import json
import aiohttp

credentials = {}
with open("cred.json") as f:
    credentials = json.load(f)

async def main():
    async with aiohttp.ClientSession() as session:
        client = await listen(session, credentials) 
        with client:
            while True:
                recv = await client.recv()
                print(recv)

loop = asyncio.get_event_loop()
loop.run_until_complete(main())