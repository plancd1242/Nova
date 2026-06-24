from __future__ import annotations

import os
import re
from pathlib import Path

import requests

try:
    from dotenv import load_dotenv

    ROOT_DIR = Path(__file__).resolve().parent.parent
    load_dotenv(ROOT_DIR / ".env.local")
    load_dotenv(ROOT_DIR / ".env")
except Exception:
    pass


TAVILY_URL = "https://api.tavily.com/search"


def _clean_query(command: str) -> str:
    text = command.strip()

    text = re.sub(r"^hey nova[,]?\s*", "", text, flags=re.I)
    text = re.sub(r"^(search for|search|look up|lookup|find|what is|who is|tell me about)\s+", "", text, flags=re.I)

    return text.strip()


def search(command: str) -> str:
    query = _clean_query(command)

    if not query:
        return "Tell me what to search for."

    api_key = os.getenv("TAVILY_API_KEY", "").strip()

    if not api_key or api_key.startswith("put_"):
        return "Tavily search is not set up yet. Add TAVILY_API_KEY to .env.local."

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "query": query,
        "search_depth": "basic",
        "topic": "general",
        "max_results": 3,
        "include_answer": "basic",
        "include_raw_content": False,
        "include_images": False,
    }

    try:
        response = requests.post(
            TAVILY_URL,
            headers=headers,
            json=payload,
            timeout=12,
        )

        if response.status_code == 401:
            return "Tavily says the API key is wrong or missing."

        if response.status_code == 403:
            return "Tavily says this API key does not have permission to search."

        if response.status_code == 429:
            return "Tavily says too many searches were used. Try again later."

        if response.status_code != 200:
            return f"Tavily search failed with error {response.status_code}."

        data = response.json()

        answer = data.get("answer")
        if answer:
            return answer.strip()

        results = data.get("results", [])
        if not results:
            return "I did not find a good result."

        first = results[0]
        title = first.get("title", "Result")
        content = first.get("content", "")

        if content:
            return f"{title}: {content}"

        return f"I found a result called {title}, but it did not include a summary."

    except requests.exceptions.Timeout:
        return "Tavily search took too long."

    except requests.exceptions.ConnectionError:
        return "I could not connect to Tavily. Check the internet."

    except Exception:
        return "I could not search right now."