from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import json

app = Flask(__name__)
CORS(app)

SENSENOVA_API_KEY = ""
BRIGHT_DATA_API_KEY = ""

def search_web(query):
    url = "https://api.brightdata.com/serp/req"
    headers = {
        "Authorization": f"Bearer {BRIGHT_DATA_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "zone": "serp_api1",
        "query": query,
        "search_engine": "google",
        "country": "us",
        "format": "json"
    }
    response = requests.post(url, headers=headers, json=payload)
    print("Bright Data status:", response.status_code)
    print("Bright Data response:", response.text[:500])

    if response.status_code != 200:
        return [f"Could not fetch live results for: {query}"]
    return response.json()

def extract_sources_from_explanation(explanation):
    """Extract sources and URLs from AI explanation text"""
    import re
    sources = []
    seen = set()
    
    source_urls = {
        "NASA": "https://nasa.gov",
        "NOAA": "https://noaa.gov",
        "USGS": "https://usgs.gov",
        "EPA": "https://epa.gov",
        "Wikipedia": "https://wikipedia.org",
        "BBC": "https://bbc.com/news",
        "Reuters": "https://reuters.com",
        "AP News": "https://apnews.com",
        "Nature": "https://nature.com",
        "Science": "https://science.org",
        "National Geographic": "https://nationalgeographic.com",
    }
    
    # Strategy 1: Extract URLs with context from explanation
    url_pattern = r'(?:https?://[^\s\)]+|www\.[^\s\)]+)'
    urls_in_text = re.findall(url_pattern, explanation)
    
    # Try to match URLs with their preceding context
    for url in urls_in_text:
        # Find what comes before the URL (the source name)
        idx = explanation.find(url)
        if idx > 0:
            # Look back for a source name or title
            before_url = explanation[max(0, idx-100):idx]
            # Find the last capitalized phrase before the URL
            phrases = re.findall(r'\b([A-Z][a-zA-Z\s]+)(?:\s*[:\(\[]|$)', before_url)
            if phrases:
                title = phrases[-1].strip()
                if title not in seen and len(title) > 2:
                    seen.add(title)
                    sources.append({
                        "title": title,
                        "url": url if url.startswith('http') else 'https://' + url,
                        "snippet": ""
                    })
    
    # Strategy 2: Find source mentions with pattern like "Source Name (url)"
    citations = re.findall(r'\(([^)]+)\)', explanation)
    for citation in citations:
        if any(source.lower() in citation.lower() for source in source_urls.keys()):
            for source in source_urls.keys():
                if source.lower() in citation.lower() and source not in seen:
                    seen.add(source)
                    sources.append({
                        "title": source,
                        "url": source_urls[source],
                        "snippet": ""
                    })
    
    # Strategy 3: Find direct source mentions
    for source_name, url in source_urls.items():
        if source_name not in seen and re.search(r'\b' + re.escape(source_name) + r'\b', explanation):
            seen.add(source_name)
            sources.append({
                "title": source_name,
                "url": url,
                "snippet": ""
            })
    
    # Strategy 4: Extract Wikipedia article names
    wiki_articles = re.findall(r'Wikipedia[:\s]+([^(\n]+)', explanation)
    for article in wiki_articles:
        article = article.strip()
        if article and article not in seen:
            seen.add(article)
            wiki_url = f"https://en.wikipedia.org/wiki/{article.replace(' ', '_')}"
            sources.append({
                "title": f"Wikipedia: {article}",
                "url": wiki_url,
                "snippet": ""
            })
    
    # If still no sources, provide generic search
    if not sources:
        sources = [{
            "title": "Learn more online",
            "url": f"https://www.google.com/search?q={explanation.split()[0].replace(' ', '+')}",
            "snippet": ""
        }]
    
    print(f"Extracted {len(sources)} sources: {[s['title'] for s in sources]}")
    return sources

def extract_sources(web_results):
    """Extract URLs and titles from search results"""
    sources = []
    try:
        if isinstance(web_results, dict):
            # Handle different API response formats
            results = web_results.get("results", [])
            if not results:
                results = web_results.get("organic", [])
            
            for item in results[:5]:  # Top 5 sources
                url = item.get("url") or item.get("link")
                title = item.get("title") or item.get("name")
                
                if url and title:
                    source = {
                        "title": title,
                        "url": url,
                        "snippet": item.get("description", item.get("snippet", ""))[:150]
                    }
                    sources.append(source)
        
        print(f"Extracted {len(sources)} sources from API")
    except Exception as e:
        print(f"Error extracting sources: {e}")
    
    return sources

def check_claim_with_sensenova(claim, web_results):
    url = "https://api.velaalpha.cc/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {SENSENOVA_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Extract sources for citation
    sources = extract_sources(web_results)
    sources_text = "\n".join([f"- {s['title']}: {s['url']}" for s in sources]) if sources else "No sources found"
    
    prompt = f"""
You are a precise fact-checking assistant. Given a claim and recent search results, determine if the claim is accurate.

Claim: {claim}

Recent Sources:
{sources_text}

Context:
{json.dumps(web_results, indent=2)[:2500]}

Analyze based on the sources and provide a scientific assessment.

IMPORTANT: Include specific article titles, sources, and URLs in your explanation when possible. Format them like:
- "According to [SOURCE_NAME] article 'Article Title' (article-url): ..."
- Reference Wikipedia articles as "Wikipedia: Topic Name"
- Include DOI numbers for scientific papers
- Include NASA/NOAA mission names

Respond ONLY with a JSON object, no markdown, no extra text:
{{"verdict": "true", "explanation": "evidence-based explanation with specific article and source references", "article_links": {{"Source Name": "https://specific-article-url", "Another Source": "https://another-url"}}}}

verdict must be exactly one of: true, outdated, false

Include article_links as a dict mapping source names to their specific URLs.
"""
    payload = {
        "model": "sensenova-6.7-flash-lite",
        "messages": [
            {"role": "system", "content": "You are a precise scientific fact-checking assistant. Always cite specific articles and sources with URLs in your explanations. Make sure to reference actual scientific articles and resources."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3
    }
    response = requests.post(url, headers=headers, json=payload)
    result = response.json()
    print("SenseNova response:", json.dumps(result, indent=2)[:500])

    if "choices" not in result:
        return {"verdict": "false", "explanation": f"SenseNova error: {result}", "sources": [], "article_links": {}}

    content = result["choices"][0]["message"]["content"]
    content = content.replace("```json", "").replace("```", "").strip()
    data = json.loads(content)
    
    # If no sources from API, try to extract from explanation
    if not sources:
        sources = extract_sources_from_explanation(data.get("explanation", ""))
        print(f"Extracted {len(sources)} sources from explanation")
    
    # Merge article links from AI response with extracted sources
    article_links = data.get("article_links", {})
    for title, link in article_links.items():
        if not any(s["title"].lower() == title.lower() for s in sources):
            sources.append({
                "title": title,
                "url": link,
                "snippet": ""
            })
    
    data["sources"] = sources
    return data

@app.route("/check", methods=["POST"])
def check():
    data = request.json
    claim = data.get("claim", "")
    if not claim:
        return jsonify({"error": "No claim provided"}), 400
    
    web_results = search_web(claim)
    print(f"\n=== Web Results for '{claim}' ===")
    print(f"Type: {type(web_results)}")
    print(f"Keys: {web_results.keys() if isinstance(web_results, dict) else 'Not a dict'}")
    print(f"Content: {json.dumps(web_results, indent=2)[:1000]}")
    print("=" * 50)
    
    verdict = check_claim_with_sensenova(claim, web_results)
    
    print(f"\n=== Verdict ===")
    print(f"Verdict: {verdict.get('verdict')}")
    print(f"Sources: {verdict.get('sources')}")
    print("=" * 50)
    
    response = {
        "claim": claim,
        "verdict": verdict["verdict"],
        "explanation": verdict["explanation"],
        "sources": verdict.get("sources", [])
    }
    
    print(f"\n=== Final Response ===")
    print(json.dumps(response, indent=2))
    print("=" * 50)
    
    return jsonify(response)

if __name__ == "__main__":
    app.run(port=5000, debug=True)