document.getElementById("checkBtn").addEventListener("click", async () => {
  const input = document.getElementById("claimInput").value.trim();
  if (!input) return;

  document.getElementById("loading").classList.remove("hidden");
  document.getElementById("results").classList.add("hidden");

  try {
    const response = await fetch("http://127.0.0.1:5000/check", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ claim: input })
    });

    const data = await response.json();
    console.log("Response data:", data);
    console.log("Sources:", data.sources);
    document.getElementById("loading").classList.add("hidden");
    displayResults([data]);

  } catch (err) {
    console.error("Error:", err);
    document.getElementById("loading").classList.add("hidden");
    document.getElementById("resultsList").innerHTML = 
      `<p style="color:red">Error: could not reach backend.</p>`;
    document.getElementById("results").classList.remove("hidden");
  }
});

function displayResults(claims) {
  const list = document.getElementById("resultsList");
  list.innerHTML = "";
  claims.forEach(item => {
    console.log("Item:", item);
    console.log("Sources in item:", item.sources);
    
    const card = document.createElement("div");
    card.className = `claim-card ${item.verdict}`;
    
    // Add verdict and explanation
    const claimDiv = document.createElement("div");
    claimDiv.className = "claim-text";
    claimDiv.textContent = item.claim;
    card.appendChild(claimDiv);
    
    const verdictDiv = document.createElement("div");
    verdictDiv.className = "verdict";
    verdictDiv.textContent = verdictLabel(item.verdict);
    card.appendChild(verdictDiv);
    
    // Create explanation with clickable URLs
    const explDiv = document.createElement("div");
    explDiv.className = "explanation";
    
    // Find and linkify URLs in the explanation
    const urlRegex = /(https?:\/\/[^\s\)]+)/g;
    const parts = item.explanation.split(urlRegex);
    
    parts.forEach((part, idx) => {
      if (part.match(urlRegex)) {
        // This is a URL, make it clickable
        const urlLink = document.createElement("a");
        urlLink.href = "javascript:void(0);";
        urlLink.textContent = part;
        urlLink.style.color = "#4f46e5";
        urlLink.style.textDecoration = "underline";
        urlLink.style.cursor = "pointer";
        urlLink.style.wordBreak = "break-all";
        
        urlLink.onclick = (e) => {
          e.preventDefault();
          e.stopPropagation();
          try {
            if (typeof chrome !== 'undefined' && chrome.tabs) {
              chrome.tabs.create({ url: part });
            } else {
              window.open(part, '_blank');
            }
          } catch (err) {
            console.log("Error opening link:", err);
          }
          return false;
        };
        
        urlLink.onmouseover = () => urlLink.style.opacity = "0.8";
        urlLink.onmouseout = () => urlLink.style.opacity = "1";
        
        explDiv.appendChild(urlLink);
      } else {
        // Regular text
        const textNode = document.createTextNode(part);
        explDiv.appendChild(textNode);
      }
    });
    
    card.appendChild(explDiv);
    list.appendChild(card);
  });
  document.getElementById("results").classList.remove("hidden");
}

function verdictLabel(v) {
  if (v === "true") return "✅ Still True";
  if (v === "outdated") return "⚠️ Outdated";
  if (v === "false") return "❌ Contradicted";
  return "🔍 Unknown";
}