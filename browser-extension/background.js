const API = "http://127.0.0.1:18190";

chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: "autotranslate-page",
    title: "Translate full page",
    contexts: ["page"],
  });
  chrome.contextMenus.create({
    id: "autotranslate-selection",
    title: "Translate with AutoTranslate",
    contexts: ["selection"],
  });
});

async function apiCall(path, body) {
  const res = await fetch(API + path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await res.json();
  if (data.error) throw new Error(data.error);
  return data;
}

function openPopup(text, result) {
  const w = 420, h = 320;
  const left = Math.round(screen.width / 2 - w / 2);
  const top = Math.round(screen.height / 2 - h / 2);
  const url = chrome.runtime.getURL("popup.html") +
    `?text=${encodeURIComponent(text)}&result=${encodeURIComponent(result)}`;
  chrome.windows.create({
    url, type: "popup", width: w, height: h, left, top
  });
}

chrome.contextMenus.onClicked.addListener(async (info, tab) => {
  if (info.menuItemId === "autotranslate-selection" && info.selectionText) {
    try {
      const data = await apiCall("/translate", { text: info.selectionText });
      openPopup(info.selectionText, data.result);
    } catch (e) {
      openPopup(info.selectionText, "Error: " + e.message);
    }
  }
  if (info.menuItemId === "autotranslate-page") {
    try {
      const [result] = await chrome.scripting.executeScript({
        target: { tabId: tab.id },
        func: () => document.body.innerText.substring(0, 5000),
      });
      const text = result?.result || "";
      const data = await apiCall("/translate", { text });
      openPopup("Page content", data.result);
    } catch (e) {
      openPopup("Error", e.message);
    }
  }
});

// Allow popup.js to call these APIs
chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.type === "translate") {
    apiCall("/translate", { text: msg.text })
      .then(d => sendResponse({ ok: true, result: d.result }))
      .catch(e => sendResponse({ ok: false, error: e.message }));
    return true;
  }
  if (msg.type === "health") {
    fetch(API + "/health")
      .then(r => r.json())
      .then(d => sendResponse({ ok: true, status: d.status }))
      .catch(() => sendResponse({ ok: false }));
    return true;
  }
});
