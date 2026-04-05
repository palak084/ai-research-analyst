import requests
import re
import urllib.parse


def search_related_papers(text: str, max_results: int = 6) -> list:
    """Search DuckDuckGo for related research papers and news articles."""
    # Extract key phrases from the text for search query
    words = text.split()[:200]
    short_text = " ".join(words)

    # Pull out capitalized phrases and common research terms
    key_phrases = re.findall(r'[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*', short_text)
    unique_phrases = list(dict.fromkeys(key_phrases))[:5]

    if unique_phrases:
        query = " ".join(unique_phrases) + " research paper"
    else:
        query = " ".join(words[:15]) + " research"

    try:
        results = _duckduckgo_search(query, max_results)
        return results
    except Exception as e:
        print(f"Web search error: {e}")
        return []


def _duckduckgo_search(query: str, max_results: int = 6) -> list:
    """Use DuckDuckGo HTML search to find results (no API key needed)."""
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                       "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    # Use DuckDuckGo Lite for simpler parsing
    url = "https://lite.duckduckgo.com/lite/"
    params = {"q": query}

    try:
        resp = requests.post(url, data=params, headers=headers, timeout=10)
        resp.raise_for_status()
        html = resp.text

        results = []

        # Parse result links from DuckDuckGo Lite HTML
        link_pattern = re.findall(
            r'<a[^>]+rel="nofollow"[^>]+href="([^"]+)"[^>]*class="result-link"[^>]*>(.*?)</a>',
            html, re.DOTALL
        )

        if not link_pattern:
            # Fallback pattern for DDG lite
            link_pattern = re.findall(
                r'<a[^>]+rel="nofollow"[^>]+href="(https?://[^"]+)"[^>]*>(.*?)</a>',
                html, re.DOTALL
            )

        # Parse snippets
        snippet_pattern = re.findall(
            r'<td[^>]*class="result-snippet"[^>]*>(.*?)</td>',
            html, re.DOTALL
        )

        if not snippet_pattern:
            snippet_pattern = re.findall(
                r'<span[^>]*class="link-text"[^>]*>(.*?)</span>',
                html, re.DOTALL
            )

        for i, (href, title) in enumerate(link_pattern[:max_results]):
            clean_title = re.sub(r'<[^>]+>', '', title).strip()
            snippet = ""
            if i < len(snippet_pattern):
                snippet = re.sub(r'<[^>]+>', '', snippet_pattern[i]).strip()

            if clean_title and href.startswith("http"):
                results.append({
                    "title": clean_title,
                    "url": href,
                    "snippet": snippet[:200] if snippet else "",
                    "source": _extract_domain(href)
                })

        return results

    except Exception as e:
        print(f"DuckDuckGo search error: {e}")
        return []


def _extract_domain(url: str) -> str:
    """Extract clean domain name from URL."""
    try:
        parsed = urllib.parse.urlparse(url)
        domain = parsed.netloc.replace("www.", "")
        return domain
    except Exception:
        return ""
