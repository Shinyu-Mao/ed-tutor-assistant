const statusEl = document.getElementById("status");

document.getElementById("open-settings").addEventListener("click", e => {
  e.preventDefault();
  chrome.runtime.openOptionsPage();
});


fetch("http://localhost:8765/health")
  .then(r => r.json())
  .then(d => {
    statusEl.innerHTML = `<span class="dot green"></span>Backend running · ${d.indexed} records indexed`;
  })
  .catch(() => {
    statusEl.innerHTML = `<span class="dot red"></span>Backend offline — run <code>uvicorn server:app --port 8765</code>`;
  });
