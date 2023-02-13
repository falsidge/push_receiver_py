import src
import aiohttp
import asyncio
import json

clientid = 0

async def main():
    async with aiohttp.ClientSession() as session:
        creds = (await src.register(session,clientid))
        with open("cred.json",'w') as f:
            json.dump(creds,f)

loop = asyncio.get_event_loop()
loop.run_until_complete(main())
