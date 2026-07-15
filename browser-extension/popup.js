const statusEl = document.getElementById("status");
const resultEl = document.getElementById("result");

// Show notification if opened with query params (from context menu)
const urlParams = new URLSearchParams(window.location.search);
if (urlParams.has("text")) {
  document.getElementById("source").value = urlParams.get("text") || "";
}
if (urlParams.has("result")) {
  resultEl.textContent = urlParams.get("result") || "";
}

// Health check
chrome.runtime.sendMessage({ type: "health" }, (resp) => {
  statusEl.textContent = resp?.ok ? "Connected" : "Server offline";
  statusEl.style.color = resp?.ok ? "#4a4" : "#c44";
});

document.getElementById("translateBtn").addEventListener("click", () => {
  const text = document.getElementById("source").value.trim();
  if (!text) return;
  statusEl.textContent = "Translating...";
  statusEl.style.color = "#888";
  chrome.runtime.sendMessage({ type: "translate", text }, (resp) => {
    if (chrome.runtime.lastError) {
      resultEl.textContent = "Error: " + chrome.runtime.lastError.message;
      statusEl.textContent = "Error";
      statusEl.style.color = "#c44";
      return;
    }
    if (resp?.ok) {
      resultEl.textContent = resp.result;
      statusEl.textContent = "Done";
      statusEl.style.color = "#4a4";
    } else {
      resultEl.textContent = "Error: " + (resp?.error || "unknown");
      statusEl.textContent = "Error";
      statusEl.style.color = "#c44";
    }
  });
});

// Translate on Ctrl+Enter in the textarea
document.getElementById("source").addEventListener("keydown", (e) => {
  if (e.ctrlKey && e.key === "Enter") {
    document.getElementById("translateBtn").click();
  }
});
