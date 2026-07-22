# Morse Monkeytype

A MonkeyType-style Morse code typing trainer built with Streamlit. English text is displayed and you type the Morse code equivalent.

## Modes

| Mode | Sub-options | Description |
|------|-------------|-------------|
| time | 15s / 30s / 60s / 120s | Random words, type until the timer runs out |
| quote | short / medium / long | Full sentences from the quote bank |

## Key bindings (defaults)

| Key | Action |
|-----|--------|
| `.` | Dot |
| `-` | Dash |
| `Space` | Submit letter |
| `/` | Next word |
| `Backspace` | Undo |
| `Escape` | Clear current letter |
| `Tab` | Restart session |

All bindings are configurable in the sidebar under **Key bindings**.

## Running locally

```bash
pip install streamlit
streamlit run app.py
```

## Adding quotes

Quotes live in `bank.txt` — one sentence per line, blank lines ignored. Edit it directly and restart the app.

You can also upload a custom `.txt` file at runtime via the **Source** expander in the sidebar without touching `bank.txt`.

## Deploying to Streamlit Cloud

1. Push this repo to GitHub (include `app.py`, `bank.txt`, `words.txt`, `requirements.txt`)
2. Go to [share.streamlit.io](https://share.streamlit.io) and connect your repo
3. Set main file to `app.py` and deploy

User stats are stored in browser `localStorage` — they persist across sessions on the same browser and survive app redeployments.

## Regenerating words.txt

`words.txt` is the word pool (generated from wordfreq https://github.com/rspeer/wordfreq) used in time mode (~46k common English words, lengths 2–12). Word selection uses a Gaussian distribution peaked at length 4 so shorter words appear more often, mirroring real Morse training patterns. To regenerate:

```bash
pip install wordfreq
python generate_words.py
```

Commit the updated `words.txt`. The script itself is not committed.
