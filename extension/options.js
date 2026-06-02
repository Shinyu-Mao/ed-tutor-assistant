const DEFAULTS = {
  apiKey: "",
  topK: 3,
  style: "friendly",
  maxWords: 150,
};

const $ = id => document.getElementById(id);

// Sync range display
$("topK").addEventListener("input", () => $("topKVal").textContent = $("topK").value);
$("maxWords").addEventListener("input", () => $("maxWordsVal").textContent = $("maxWords").value);

// Load saved settings
chrome.storage.sync.get(DEFAULTS, prefs => {
  $("apiKey").value   = prefs.apiKey;
  $("topK").value     = prefs.topK;
  $("topKVal").textContent    = prefs.topK;
  $("style").value    = prefs.style;
  $("maxWords").value = prefs.maxWords;
  $("maxWordsVal").textContent = prefs.maxWords;
});

// Save
$("save").addEventListener("click", () => {
  const prefs = {
    apiKey:   $("apiKey").value.trim(),
    topK:     parseInt($("topK").value),
    style:    $("style").value,
    maxWords: parseInt($("maxWords").value),
  };
  chrome.storage.sync.set(prefs, () => {
    $("status").textContent = "Saved ✓";
    setTimeout(() => $("status").textContent = "", 2000);
  });
});

// Reset
$("reset").addEventListener("click", () => {
  chrome.storage.sync.set(DEFAULTS, () => {
    $("apiKey").value   = DEFAULTS.apiKey;
    $("topK").value     = DEFAULTS.topK;
    $("topKVal").textContent    = DEFAULTS.topK;
    $("style").value    = DEFAULTS.style;
    $("maxWords").value = DEFAULTS.maxWords;
    $("maxWordsVal").textContent = DEFAULTS.maxWords;
    $("status").textContent = "Reset to defaults ✓";
    setTimeout(() => $("status").textContent = "", 2000);
  });
});
