import asyncio
import json
import logging
import os
from openai import OpenAI

# Set up logger
logger = logging.getLogger(__name__)

# Environment variables
LLM_API_KEY = os.environ.get("HELICONE_API_KEY")


def create_openai_client():
    """
    Create and return an OpenAI client configured for Helicone.
    
    Returns:
        OpenAI: Configured OpenAI client
    """
    return OpenAI(
        api_key=LLM_API_KEY,
        base_url="https://ai-gateway.helicone.ai/v1"
    )


async def call_llm(ticker, stories, client):
    """
    Call the LLM to analyze newsletter content for stock-related stories.
    
    Args:
        ticker (str): Stock ticker symbol to check against
        email (str): Newsletter content to analyze
        client (OpenAI): OpenAI client instance
        
    Returns:
        list: List of related stories or empty list if none found
    """
    prompt = f"""
You are a financial analyst. Your job is to carefully review the following newsletters, and create a single newsletter ony containing information related to the attached stocks. 

Newsletters are given to you in the format of:
Author: <Name of orginization>
Story: <Full text of the story>

Stocks are given to you in the format of:
[NVDA, TSLA, AAPL, GOOG, MSFT]

You must create a single newsletter that only contains information related to the attached stocks.

Within the newsletter, each stock must have its own section of information. Try to copy the exact wording of the original story as much as possible. 
Cite the author of the original story when adding it to the newsletter (ex//. According to <Author>, <Story>). Make sure the stories flow naturally and are not forced. 
DO NOT ADD A DUPLICATE STORY TWICE. If a story pertains to multiple stocks create the one section/story for the stock both of the stocks.

The section must be in the format of:

<Stock symbol>
<Story>

If the story relates to multiple stocks, it can look like the following:
<Stock symbol> <Stock symbol>
<Story>

DO NOT MAKE UP ANYTHING. ONLY USE THE INFORMATION PROVIDED TO YOU.
If there is no information related to a stock, DO NOT INCLUDE IT IN THE NEWSLETTER.
If there is no information related to any of the stocks, DO NOT INCLUDE ANYTHING IN THE NEWSLETTER BODY.

CRITICAL FORMATING INFORMATION:
You must return the newsletter in the following json format:

make up a title for the newsletter based on what the stories are about.
```json
  {{
    "title": "title of the newsletter",
    "body": "newsletter body",
  }},
```

If there is no related stories, YOU MUST GIVE BACK AN EMPTY BODY
```json
{{
    "title": "title of the newsletter",
    "body": ""
}}
```

Be conservative and avoid hallucinating connections.

Here are the stocks to check against:
{ticker}

Here is the newsletter content:

{stories}

    """
    max_retries = 5
    for i in range(max_retries):
        try:
            response = client.chat.completions.create(
                model="gpt-4o/openai",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0
            )
            logger.info(response)
            text = response.choices[0].message.content
            cleaned_text = text.replace('```json', '').replace('```', '').replace('```json\n', '').replace('\n```','').strip()
            if cleaned_text.startswith('{') and cleaned_text.endswith('}'):
                return json.loads(cleaned_text)
            await asyncio.sleep(i*2)
        except Exception as e:
            logger.error(f"[ERROR] LLM call failed for ticker {ticker}: {e}")
            await asyncio.sleep(i*2)
    return {
        "title": "title of the newsletter",
        "body": ""
    }
