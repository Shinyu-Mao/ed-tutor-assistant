# Ed Tutor Assistant

A Chrome extension + local Python backend that helps tutors respond to student questions on [Ed Discussion](https://edstem.org). When a tutor opens a question thread, the extension reads the title and body, searches a knowledge base of past Q&A records using semantic similarity, and uses the Claude API to draft a suggested reply.

---

## How It Works

```
Ed Discussion page
  └── content.js reads question title + body
        └── POST /suggest → FastAPI backend
              ├── search.py   — embeds query, finds top-k similar past threads (cosine similarity)
              └── generate.py — builds RAG prompt → Claude API → draft reply
                    └── suggested answer + matched threads → sidebar UI
                          └── tutor edits and inserts into reply box
```

The knowledge base is loaded and embedded once at server startup and held in memory. No database required.

---

## Project Structure

```
ed-tutor-assistant/
├── backend/
│   ├── server.py          # FastAPI app — POST /suggest, GET /health
│   ├── search.py          # Sentence-transformer embeddings + cosine similarity search
│   ├── generate.py        # RAG prompt builder + Claude API call
│   ├── requirements.txt
│   └── .env.example       # Config template
├── extension/
│   ├── manifest.json      # Chrome Manifest V3
│   ├── content.js         # Sidebar UI, DOM reading, backend calls
│   ├── background.js      # Icon colour switching (purple on Ed, grey elsewhere)
│   ├── sidebar.css        # Sidebar + modal styles
│   ├── popup.html/js      # Toolbar popup — shows backend health + indexed count
├── data/
│   └── qa.json            # Anonymised Q&A knowledge base (not committed — add your own)
└── setup.sh               # One-shot dependency installer
```

---

## Setup

### 1. Backend

```bash
cd ed-tutor-assistant
bash setup.sh                    # installs Python deps, creates backend/.env
```

Edit `backend/.env`:

```
ANTHROPIC_API_KEY=your_key_here
DATA_PATH=../data/qa.json
TOP_K=3
```

Place your anonymised Q&A JSON at `data/qa.json` (see Data Format below), then start the server:

```bash
cd backend
uvicorn server:app --reload --port 8765
```

Verify it's running:

```bash
curl http://localhost:8765/health
# {"status": "ok", "indexed": 52}
```

### 2. Chrome Extension

1. Go to `chrome://extensions`
2. Enable **Developer mode** (top right)
3. Click **Load unpacked** → select the `extension/` folder
4. The toolbar icon appears — purple on Ed Discussion, grey elsewhere

---

## Data Format

`data/qa.json` must be a JSON array. Each object with at least one answer will be indexed:

```json
[
  {
    "number": 37,
    "title": "No Stemming/Stop is better in assignment?",
    "category": "Project",
    "subcategory": "P1",
    "text": "Hi, I have realised that when I using stemming...",
    "answers": [
      { "text": "Hi, as this may be due to different reasons..." }
    ]
  }
]
```

Fields used: `number`, `title`, `text` (question body), `answers[].text`, `category`, `subcategory`. All other fields are ignored.

---

## Using the Extension

1. Open any question thread on Ed Discussion (`/discussion/*`)
2. The **Tutor Assistant** sidebar appears on the right
3. Click **Suggest Answer** — the extension sends the question to the backend
4. Review the suggested reply in the editable text area
5. Click a matched thread card to view its full question and answers in a modal
6. Edit the reply as needed, then click **Insert into Reply Box**

---

## API

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Returns status and number of indexed records |
| `POST` | `/suggest` | Returns suggested answer + matched threads |

`POST /suggest` body:
```json
{ "title": "...", "body": "..." }
```

Response:
```json
{
  "suggested_answer": "Hi, ...",
  "matched_threads": [
    {
      "number": 37,
      "title": "No Stemming/Stop is better?",
      "question": "...",
      "answers": ["..."],
      "score": 0.91
    }
  ]
}
```

---

## TODO

### In progress
- [ ] Verify reply box insertion across different Ed Discussion thread types (question, post, announcement)

### Near-term
- [ ] **Category-aware search** — detect current thread's category/subcategory from the page and filter matched records accordingly
- [ ] **Persistent vector index** — serialise embeddings to disk so startup is instant on subsequent runs
- [ ] **Fix reply box injection** — replace deprecated `document.execCommand` with Clipboard API

### Nice to have
- [ ] **Multi-semester support** — load per-course JSON based on course ID in the Ed URL
- [ ] **Backend authentication** — API key header for shared/deployed use
- [ ] **DOM resilience** — fallback selectors + sidebar warning when question text cannot be read confidently
- [ ] **Settings popup** — let tutors configure `TOP_K`, backend URL, and model from the extension UI
- [ ] **Mark as helpful** — thumbs up/down on suggestions to log quality for future fine-tuning

---

## Notes for Future Development

### Category-aware search
Currently the knowledge base is searched globally across all categories and subcategories. A natural next step is to detect the category of the current thread from the Ed Discussion page (e.g. read a breadcrumb or URL segment like `/P1`, `/Lectures`), pass it as a filter field in `POST /suggest`, and restrict the embedding search to records with a matching `category`/`subcategory`. This would improve match precision when the same question wording appears in different project parts.

### Persistent vector index
Embeddings are recomputed from scratch on every server start. For larger knowledge bases, serialise the numpy embedding matrix and record list to disk (e.g. with `numpy.save` + `pickle`) and reload on startup instead of re-encoding.

### Multi-semester knowledge base
The current setup assumes a single `qa.json`. Supporting multiple course offerings would require either a merged file or a per-course index, with the extension passing a course ID (readable from the Ed Discussion URL) so the backend can select the right index.

### Reply box injection reliability
`document.execCommand("insertText")` is deprecated and may break in future Chrome versions. Replace with the [Clipboard API](https://developer.mozilla.org/en-US/docs/Web/API/Clipboard_API) (`navigator.clipboard.writeText`) and prompt the tutor to paste, or investigate Ed Discussion's internal React event system for a more robust injection approach.

### Ed Discussion DOM stability
The content script relies on CSS class names (`disthrb-title`, `disthrb-body`) and a `data-testid` attribute (`content`) that could change with Ed updates. Consider adding a fallback that reads the page `<title>` and visible paragraph text when the primary selectors fail, and surface a warning in the sidebar when the question could not be read confidently.

### Authentication for the backend
The backend currently accepts requests from any origin. If deployed for shared tutor use (rather than locally), add an API key header check to `server.py` and store the key in the extension's `chrome.storage.sync`.
