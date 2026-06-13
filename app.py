from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import json

app = Flask(__name__)
CORS(app)

SENSENOVA_API_KEY = "sk-K8UazZC4hpm44BcEs0HAmUgiPKYZAg6i"
BRIGHT_DATA_API_KEY = "e17beaf0-5eec-4461-952d-312f5a22c094"

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

def check_claim_with_sensenova(claim, web_results):
    url = "https://api.velaalpha.cc/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {SENSENOVA_API_KEY}",
        "Content-Type": "application/json"
    }
    prompt = f"""
You are a fact-checking assistant. Given a claim and some context, determine if the claim is still accurate.

Claim: {claim}

Context:
{json.dumps(web_results, indent=2)[:3000]}

Respond ONLY with a JSON object, no markdown, no extra text:
{{"verdict": "true", "explanation": "one sentence explanation"}}

verdict must be exactly one of: true, outdated, false
"""
    payload = {
        "model": "sensenova-6.7-flash-lite",
        "messages": [
            {"role": "system", "content": "You are a precise fact-checking assistant."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3
    }
    response = requests.post(url, headers=headers, json=payload)
    result = response.json()
    print("SenseNova response:", json.dumps(result, indent=2)[:500])

    if "choices" not in result:
        return {"verdict": "false", "explanation": f"SenseNova error: {result}"}

    content = result["choices"][0]["message"]["content"]
    content = content.replace("```json", "").replace("```", "").strip()
    return json.loads(content)

@app.route("/check", methods=["POST"])
def check():
    data = request.json
    claim = data.get("claim", "")
    if not claim:
        return jsonify({"error": "No claim provided"}), 400
    web_results = search_web(claim)
    verdict = check_claim_with_sensenova(claim, web_results)
    return jsonify({
        "claim": claim,
        "verdict": verdict["verdict"],
        "explanation": verdict["explanation"]
    })

if __name__ == "__main__":
    app.run(port=5000, debug=True)