import asyncio
import os

import aiohttp

BASE_URL = os.environ.get("API_BASE", "http://localhost:8501")
TOKEN = os.environ.get("API_TOKEN")


async def main():
    headers = {}
    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"

    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(f"{BASE_URL}/api/v1/part-locations") as resp:
            resp.raise_for_status()
            data = await resp.json()
            print(data)

if __name__ == "__main__":
    asyncio.run(main())
