/**
 * Background service worker — switches the toolbar icon between
 * purple (active on Ed Discussion) and grey (everywhere else).
 */

function makeIcon(color) {
  const size = 32;
  const canvas = new OffscreenCanvas(size, size);
  const ctx = canvas.getContext("2d");

  // Circle background
  ctx.fillStyle = color;
  ctx.beginPath();
  ctx.arc(size / 2, size / 2, size / 2, 0, Math.PI * 2);
  ctx.fill();

  // Graduation cap emoji substitute — white "T" for Tutor
  ctx.fillStyle = "#ffffff";
  ctx.font = `bold ${size * 0.55}px Arial`;
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  ctx.fillText("T", size / 2, size / 2 + 1);

  return ctx.getImageData(0, 0, size, size);
}

const PURPLE = "#7B2FBE";
const GREY   = "#999999";

function setIcon(tabId, url) {
  const active = url && url.includes("edstem.org");
  chrome.action.setIcon({
    tabId,
    imageData: { 32: makeIcon(active ? PURPLE : GREY) },
  });
  chrome.action.setTitle({
    tabId,
    title: active ? "Ed Tutor Assistant (active)" : "Ed Tutor Assistant",
  });
}

// When switching tabs
chrome.tabs.onActivated.addListener(({ tabId }) => {
  chrome.tabs.get(tabId, tab => setIcon(tabId, tab.url));
});

// When navigating within a tab
chrome.tabs.onUpdated.addListener((tabId, change, tab) => {
  if (change.status === "complete") setIcon(tabId, tab.url);
});
