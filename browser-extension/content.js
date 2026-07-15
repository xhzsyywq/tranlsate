// Content script: detect selected text and offer inline translation toolbar
(function () {
  let toolbar = null;

  function hideToolbar() {
    if (toolbar) { toolbar.remove(); toolbar = null; }
  }

  document.addEventListener("mouseup", (e) => {
    setTimeout(() => {
      const sel = window.getSelection();
      const text = sel?.toString().trim();
      if (!text || text.length < 2) { hideToolbar(); return; }

      const range = sel.getRangeAt(0);
      const rect = range.getBoundingClientRect();
      if (!rect || rect.width < 5) { hideToolbar(); return; }

      if (!toolbar) {
        toolbar = document.createElement("div");
        toolbar.id = "autotranslate-tb";
        toolbar.style.cssText = `
          position: fixed; z-index: 2147483647; background: #4682ff; color: #fff;
          padding: 4px 10px; border-radius: 4px; font: 12px sans-serif;
          cursor: pointer; box-shadow: 0 2px 6px rgba(0,0,0,.3);
          user-select: none; transition: opacity .15s;
        `;
        toolbar.textContent = "T";
        toolbar.title = "Translate with AutoTranslate";
        toolbar.addEventListener("click", async () => {
          const t = window.getSelection()?.toString().trim();
          if (!t) return;
          try {
            const res = await fetch("http://127.0.0.1:18190/translate", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ text: t }),
            });
            const data = await res.json();
            if (data.result) {
              alert("Translation:\n" + data.result);
            } else {
              alert("Error: " + (data.error || "unknown"));
            }
          } catch (err) {
            alert("AutoTranslate server not reachable.\nStart the desktop app first.");
          }
        });
        document.body.appendChild(toolbar);
      }
      const top = rect.top + window.scrollY - toolbar.offsetHeight - 6;
      const left = rect.left + window.scrollX;
      toolbar.style.top = Math.max(4, top) + "px";
      toolbar.style.left = Math.max(4, left) + "px";
    }, 10);
  });

  document.addEventListener("mousedown", (e) => {
    if (!e.target?.closest?.("#autotranslate-tb")) hideToolbar();
  });
})();
