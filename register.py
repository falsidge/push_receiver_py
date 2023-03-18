from . import register, listen
import aiohttp
import asyncio
import json

clientid = 0

async def main():
    async with aiohttp.ClientSession() as session:
        creds = (await register(session,clientid))
        with open("cred.json",'w') as f:
            json.dump(creds,f)

loop = asyncio.get_event_loop()
loop.run_until_complete(main())
