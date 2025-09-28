import requests
from flask import Flask, request, jsonify, render_template
from urllib.parse import urljoin, urlparse

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/inspect", methods=["POST"])
def inspect():
    target_url = request.json.get("url")
    if not target_url.startswith("http"):
        target_url = "http://" + target_url

    try:
        # Fetch the main page
        resp = requests.get(target_url, timeout=10, headers={
            "User-Agent": "Mozilla/5.0 (NetworkInspector)"
        })
        base_url = resp.url
    except Exception as e:
        return jsonify({"error": f"Failed to fetch target URL: {str(e)}"}), 400

    results = []
    # Start with main page
    results.append({
        "url": base_url,
        "status": resp.status_code,
        "size": len(resp.content),
        "type": resp.headers.get("Content-Type")
    })

    # Extract linked resources (basic: img, script, link)
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(resp.text, "html.parser")

    resource_urls = []
    for tag, attr in [("img", "src"), ("script", "src"), ("link", "href")]:
        for el in soup.find_all(tag):
            if el.get(attr):
                full_url = urljoin(base_url, el[attr])
                resource_urls.append(full_url)

    resource_urls = list(set(resource_urls))  # deduplicate

    for u in resource_urls[:20]:  # limit to 20 resources
        try:
            r = requests.get(u, timeout=10, headers={
                "User-Agent": "Mozilla/5.0 (NetworkInspector)"
            })
            results.append({
                "url": u,
                "status": r.status_code,
                "size": len(r.content),
                "type": r.headers.get("Content-Type")
            })
        except Exception as e:
            results.append({"url": u, "error": str(e)})

    return jsonify({"results": results})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
