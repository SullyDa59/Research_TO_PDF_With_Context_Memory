# Quick Start Guide

## First Time Setup (5 minutes)

### 1. Set Your OpenAI API Key

```bash
export OPENAI_API_KEY='sk-your-key-here'
```

Get your API key: https://platform.openai.com/api-keys

### 2. Install Dependencies

```bash
pip3 install -r requirements.txt
```

### 3. Test Everything Works

```bash
python3 test_openai_api.py
```

You should see "✅ SUCCESS: OpenAI API is working correctly!"

## Running the App

### Easy Way

```bash
./start.sh
```

Then open: **http://localhost:5001**

### Manual Way

```bash
python3 research_ui_flask.py
```

## Using the App

1. Enter a research topic (e.g., "quantum computing")
2. Review AI-generated search queries
3. Select sources to include
4. Download your research PDF
5. Upload to NotebookLM at https://notebooklm.google.com

## Stopping the App

Press `Ctrl+C` in the terminal

## Common Issues

**Port 5000 already in use?**
- Mac users: Disable AirPlay Receiver in System Preferences
- Or edit `research_ui_flask.py` line 453 to use different port

**API errors?**
- Run `python3 test_openai_api.py` to diagnose
- Check your API key is valid
- Ensure you have credits in your OpenAI account

**Import errors?**
- Run `pip3 install -r requirements.txt` again

## Features

- AI-powered search query generation
- Web scraping from 10+ sources
- Clean PDF formatting
- NotebookLM optimized
- No web search API keys needed (uses DuckDuckGo)

## Cost

Very cheap! ~$0.0001 per research session using GPT-4o-mini

---

**Need help?** Check the full README.md
