"""
Grounding Module - Sources & Insights (Reliable URLs)

Fetches authoritative learning resources AND compelling "Why This Matters" insights
using Google Search grounding. Extracts REAL URLs from grounding_metadata instead
of relying on LLM-generated URLs.
"""

import json
import re
import time
from google.genai import types


def ground_lesson(client, topic: str, core_concept: str) -> dict:
    """
    Generate "Why This Matters" insights with source URLs.

    Returns:
        {
            "insights": [{text, url}],
            "grounded": bool,
            "fetch_time_seconds": float
        }
    """
    start_time = time.time()

    prompt = f"""YOUR TASK: Find 2 persuasive facts that makes someone think "I need to learn this: {topic}"

Find specific examples:
- Which companies or organizations use this concept?
- What measurable outcomes or results has it produced?
- Any case studies, research findings, or industry adoption stats?

Then provide 2 compelling insights with SPECIFIC numbers or facts.

REQUIREMENTS for insights:
- Must include specific numbers, percentages, company names, or study/expert citations
- Show real-world impact or adoption
- Be relatable to the specific concept, not broad of the field
- When possible, use authoritative sources
- CRITICALLY IMPORTANT: The insight sentence must be under 120 characters. Express it a punchy and lean way. 

GOOD examples:
- "Netflix processes 2 billion API requests daily using this pattern"
- "A 2023 Stanford study found this approach improved retention by 34%"

BAD examples (too vague):
- "This is widely used in industry"
- "Many developers prefer this"

Return as JSON: {{"insights": ["insight1", "insight2"]}}"""

    search_tool = types.Tool(google_search=types.GoogleSearch())

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                tools=[search_tool],
                temperature=0.0,
                system_instruction="You are an industry research analyst. Return only valid JSON with an 'insights' array containing exactly 2 strings."
            ),
        )

        # Extract REAL sources from grounding_metadata
        sources = _extract_grounded_sources(response)

        # Extract insights and attach source URLs
        insights = _parse_insights(response.text or "", sources)

        # Extract token usage
        token_usage = None
        if response.usage_metadata:
            token_usage = {
                "total_tokens": response.usage_metadata.total_token_count,
            }

        duration = time.time() - start_time

        print(f"[Grounding] '{topic[:40]}': {len(sources)} sources, {len(insights)} insights ({duration:.1f}s)")

        return {
            "insights": insights[:2],
            "grounded": len(insights) > 0,
            "fetch_time_seconds": round(duration, 2),
            "token_usage": token_usage,
        }

    except Exception as e:
        print(f"[Grounding] Error: {e}")
        return {
            "insights": [],
            "grounded": False,
            "error": str(e)
        }


def _extract_grounded_sources(response) -> list:
    """
    Extract sources from grounding_metadata.grounding_chunks.
    These are the ACTUAL sources Google Search found and used.
    """
    sources = []
    seen_titles = set()

    try:
        metadata = response.candidates[0].grounding_metadata
        if not metadata or not metadata.grounding_chunks:
            return sources

        for chunk in metadata.grounding_chunks:
            if not chunk.web:
                continue

            title = chunk.web.title or 'Unknown'
            uri = chunk.web.uri

            if not uri or title in seen_titles:
                continue
            seen_titles.add(title)

            sources.append({
                "title": title,
                "url": uri,
                "description": "Source from Google Search grounding",
            })

    except Exception as e:
        print(f"[Grounding] Error extracting sources: {e}")

    return sources


def _parse_insights(text: str, sources: list) -> list:
    """Parse insight statements and attach source URLs."""
    try:
        clean_text = re.sub(r'^```json\s*|\s*```$', '', text.strip())
        data = json.loads(clean_text)

        insights = []
        for i, insight in enumerate(data.get("insights", [])[:2]):
            if isinstance(insight, str):
                # Attach source URL if available
                url = sources[i]["url"] if i < len(sources) else None
                insights.append({"text": insight, "url": url})
        return insights
    except (json.JSONDecodeError, AttributeError):
        return []