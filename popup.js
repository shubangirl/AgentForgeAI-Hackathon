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
    document.getElementById("loading").classList.add("hidden");
    displayResults([data]);

  } catch (err) {
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
    const card = document.createElement("div");
    card.className = `claim-card ${item.verdict}`;
    card.innerHTML = `
      <div class="claim-text">${item.claim}</div>
      <div class="verdict">${verdictLabel(item.verdict)}</div>
      <div class="explanation">${item.explanation}</div>
    `;
    list.appendChild(card);
  });
  document.getElementById("results").classList.remove("hidden");
}

function verdictLabel(v) {
  if (v === "true") return "Still True";
  if (v === "outdated") return "Outdated";
  if (v === "false") return "Content Contradicted!";
  return "Unknown Content";
}