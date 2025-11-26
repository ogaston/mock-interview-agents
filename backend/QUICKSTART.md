# Quick Start Guide

Get the Mock Interview Agent backend running in 5 minutes!

## 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

## 2. Configure API Key (or Use Mock Mode)

### Option A: Use Mock Mode (No API Keys Required)

For testing and development, you can use mock mode which doesn't require any API keys:

```bash
# Copy environment template
cp .env.example .env

# Edit .env and enable mock mode
# Windows: notepad .env
# Mac/Linux: nano .env
```

Add to `.env`:
```env
USE_MOCK_LLM=true
USE_MOCK_TTS=true
LLM_PROVIDER=mock
TTS_PROVIDER=mock
```

**Note:** Mock mode uses fake responses and silent audio. Perfect for development and testing!

### Option B: Use Real API Keys

```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your API key
# Windows: notepad .env
# Mac/Linux: nano .env
```

Add your API key:
```env
OPENAI_API_KEY=sk-your-actual-key-here
LLM_PROVIDER=openai
```

## 3. Run the Server

```bash
python -m app.main
```

The API will be running at http://localhost:8000

## 4. Test It Out

Open http://localhost:8000/docs in your browser to see the interactive API documentation.

### Try a Quick Interview

**Start Interview:**
```bash
curl -X POST http://localhost:8000/api/interviews/start \
  -H "Content-Type: application/json" \
  -d '{"role": "Software Engineer", "seniority": "mid"}'
```

Copy the `session_id` from the response.

**Submit an Answer:**
```bash
curl -X POST http://localhost:8000/api/interviews/YOUR_SESSION_ID/answer \
  -H "Content-Type: application/json" \
  -d '{"answer": "I would use a hash map to solve this problem because it provides O(1) lookup time. First, I would iterate through the array and store each element as a key with its index as the value. Then, for each element, I would check if the complement exists in the hash map."}'
```

**Get Feedback (after answering all questions):**
```bash
curl http://localhost:8000/api/interviews/YOUR_SESSION_ID/feedback
```

## Common Issues

**"spaCy model not found"**
```bash
python -m spacy download en_core_web_sm
```

**"Invalid API key"**
- Check that your `.env` file exists in the `backend` directory
- Verify your API key is correct (starts with `sk-` for OpenAI)

**"Port 8000 already in use"**
- Kill the process using port 8000, or
- Change the port in `app/main.py` (line with `port=8000`)

## What's Next?

- Explore the full API at http://localhost:8000/docs
- Read the complete [README.md](README.md) for detailed documentation
- Integrate with your frontend application
- Customize the fuzzy logic rules in `app/services/fuzzy_service.py`

Enjoy your AI-powered interview training! 🚀
