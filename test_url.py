import asyncio
from openai import AsyncOpenAI

client = AsyncOpenAI(api_key='x', base_url='https://generativelanguage.googleapis.com/v1beta/openai/')

async def main():
    try:
        await client.chat.completions.create(
            model='gemini-1.5-flash',
            messages=[{'role': 'user', 'content': 'hi'}]
        )
    except Exception as e:
        if hasattr(e, 'request'):
            print("URL:", e.request.url)
        else:
            print("Error:", e)

asyncio.run(main())
