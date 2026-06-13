document.getElementById("checkBtn").addEventListener("click", async () => {
  const input = document.getElementById("claimInput").value.trim();
  if (!input) return;

  // Show loading, hide results
  document.getElementById("loading").classList.remove("hidden");
  document.getElementById("results").classList.add("hidden");

  // TODO: call your backend here
  console.log("Checking:", input);

  // Fake result for now to test UI
  setTimeout(() => {
    document.getElementById("loading").classList.add("hidden");
    displayResults([
      {
        claim: input,
        verdict: "outdated",
        explanation: "Backend not connected yet — this is a UI test."
      }
    ]);
  }, 1500);
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
  if (v === "true") return "✅ Still True";
  if (v === "outdated") return "⚠️ Outdated";
  if (v === "false") return "❌ Contradicted";
  return "🔍 Unknown";
}
