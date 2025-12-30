"""
Further Reading Module - High-Quality Learning Resources

Same pattern as grounding.py: JSON from LLM, URLs from grounding_metadata.
"""

import json
import re
import time
from google.genai import types


def get_further_reading(client, topic: str) -> dict:
    start_time = time.time()

    prompt = f"""YOUR TASK: Search the web for 3 authoritative learning resources about: {topic}

Find:
- Official documentation or tutorials
- In-depth expert articles
- University or research publications

For each resource you find, provide:
1. A short descriptive title (under 50 chars)
2. One specific fact or quote from that page (to verify you actually read it)

Return as JSON: {{"resources": [
  {{"title": "descriptive title", "fact": "specific fact from page"}},
  {{"title": "descriptive title", "fact": "specific fact from page"}},
  {{"title": "descriptive title", "fact": "specific fact from page"}}
]}}"""

    search_tool = types.Tool(google_search=types.GoogleSearch())

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                tools=[search_tool],
                temperature=0.0,
                system_instruction="You are a resource curator. You MUST use web search to find real resources. Return only valid JSON with a 'titles' array containing exactly 3 strings.",
            ),
        )
        _debug_grounding_metadata(response)

        urls = _extract_urls(response)

        titles = _parse_titles(response.text or "")

        print(f"[Further Reading] {len(urls)} URLs, {len(titles)} titles")
        if not titles and response.text:
            print(f"[Further Reading] Response: {response.text[:200]}")
        sources = []
        for i, url in enumerate(urls[:3]):
            title = titles[i] if i < len(titles) else "Resource"
            sources.append({"title": title, "url": url})

        duration = time.time() - start_time
        tokens = response.usage_metadata.total_token_count if response.usage_metadata else None

        print(f"[Further Reading] '{topic}' ({duration:.1f}s, {tokens or '?'} tokens)")
        for s in sources:
            print(f"  → {s['title']}")

        return {
            "sources": sources,
            "fetch_time_seconds": round(duration, 2),
            "token_usage": {"total_tokens": tokens} if tokens else None,
        }

    except Exception as e:
        print(f"[Further Reading] Error: {e}")
        return {"sources": [], "error": str(e)}


def _extract_urls(response) -> list:
    """Extract URLs from grounding_metadata - same as grounding.py."""
    urls = []
    seen = set()
    try:
        metadata = response.candidates[0].grounding_metadata
        if metadata and metadata.grounding_chunks:
            for chunk in metadata.grounding_chunks:
                if chunk.web and chunk.web.uri and chunk.web.uri not in seen:
                    seen.add(chunk.web.uri)
                    urls.append(chunk.web.uri)
    except Exception as e:
        print(f"[Further Reading] URL extraction error: {e}")
    return urls


def _debug_grounding_metadata(response):
    """Debug helper to see what's in the response."""
    try:
        candidate = response.candidates[0] if response.candidates else None
        if not candidate:
            print("[Further Reading] DEBUG: No candidates in response")
            return

        metadata = candidate.grounding_metadata
        if not metadata:
            print("[Further Reading] DEBUG: No grounding_metadata - model may not have triggered search")
            return

        # Check for grounding chunks (contains URLs)
        chunk_count = len(metadata.grounding_chunks) if metadata.grounding_chunks else 0
        print(f"[Further Reading] DEBUG: {chunk_count} grounding_chunks")

        # Check for search queries (shows what was searched)
        if hasattr(metadata, "web_search_queries") and metadata.web_search_queries:
            print(f"[Further Reading] DEBUG: search queries: {metadata.web_search_queries}")
        else:
            print("[Further Reading] DEBUG: No web_search_queries - search may not have triggered")

    except Exception as e:
        print(f"[Further Reading] DEBUG error: {e}")


def _parse_titles(text: str) -> list:
    """Parse titles from JSON - handles preamble text before JSON block."""
    try:
        # Extract JSON from anywhere in the response
        json_match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
        if json_match:
            clean = json_match.group(1)
        else:
            # Try to find JSON object with "resources" key
            json_match = re.search(r'\{[^{}]*"resources"\s*:', text, re.DOTALL)
            if json_match:
                # Find the full JSON object
                clean = text[json_match.start():]
                obj_match = re.match(r'\{.*\}', clean, re.DOTALL)
                if obj_match:
                    clean = obj_match.group(0)
                else:
                    clean = text.strip()
            else:
                clean = re.sub(r'^```json\s*|\s*```$', '', text.strip())

        data = json.loads(clean)
        # Extract just the titles, ignore the facts (facts force grounding but we discard them)
        return [r["title"] for r in data.get("resources", []) if isinstance(r, dict) and "title" in r]
    except (json.JSONDecodeError, AttributeError, KeyError) as e:
        print(f"[Further Reading] JSON parse error: {e}")
        return []
