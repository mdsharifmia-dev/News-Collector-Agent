# News Collector Agent: Autonomous Multi-Tool AI Intelligence Suite

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Model-Agnostic](https://img.shields.io/badge/AI_Engine-Multi--LLM_Agnostic-7928CA?style=for-the-badge&logo=openai&logoColor=white)](https://github.com/mdsharifmia-dev/News-Collector-Agent)
[![Telegram](https://img.shields.io/badge/Interface-Telegram%20Bot-2CA5E0?style=for-the-badge&logo=telegram&logoColor=white)](https://telegram.org)
[![Docker](https://img.shields.io/badge/Deployment-Docker%20Ready-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://docker.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)

**An autonomous 24/7 intelligent news aggregation, synthesis, and personal AI agent on Telegram.**  
*Model-Agnostic Multi-LLM Architecture • Automated Web Scraping • SQLite Memory • Native Tool Execution*

</div>

---

## Core Capabilities & Features

- **Autonomous News Collection (`news_collector.py`):** Real-time scraping and parsing of global tech, business, and breaking news feeds with deduplication.
- **AI Synthesis & Summarization (`news_summarizer.py`):** Distills lengthy articles into concise, bulleted executive briefings in modern Bengali or English.
- **YouTube Video Summarizer (`/yt <url>`):** Extracts video content and provides structured 5-10 line Bengali summaries with key takeaways.
- **Social Media Post Generator (`/post <topic>`):** Crafts publication-ready LinkedIn and Facebook tech posts with hooks, key points, and hashtags.
- **GitHub Trending AI Tracker (`/trending` or `/github`):** Tracks top trending AI and open-source repositories with star velocity and translated descriptions.
- **Multimodal Vision & Voice Intelligence:** Accepts code screenshots and error photos for instant debugging, and processes voice notes (.ogg) directly.
- **Live Internet Search (`search_web`):** Executes real-time web searches using DuckDuckGo to answer ad-hoc user inquiries with source citations.
- **Persistent SQLite Long-Term Memory (`save_note` & `read_notes`):** Stores user preferences, notes, and context in an embedded `memory.db` database.
- **Automated Reminder Scheduler (`set_reminder`):** Background scheduler for time-sensitive task reminders and alerts.
- **Zero-Trust Access Control:** Restricts bot commands and private data access strictly to authenticated Telegram user IDs.

---

## System Architecture

```text
User (Telegram) ──> python-telegram-bot ──> Core AI Agent Engine (Any LLM API)
                                                   │
     ┌──────────────────────┬──────────────────────┼──────────────────────┐
     ▼                      ▼                      ▼                      ▼
[ News Collector ]    [ AI Summarizer ]   [ DuckDuckGo Search ]   [ SQLite Memory DB ]
(Scrapes Feeds)       (Bullet Briefs)     (Live Web Info)         (Notes & Reminders)
```

---

## Project Structure & File Map

```text
News-Collector-Agent/
├── bot.py                  # Main Telegram bot runtime, command handlers & agent loop
├── news_collector.py       # Automated multi-source news scraper & pipeline
├── news_summarizer.py      # LLM-powered news synthesis & briefing engine
├── agent_tools.py          # Native function calling tools (SQLite notes, reminders, search)
├── test_news_pipeline.py   # Test suite for scraper and summarization flows
├── Dockerfile              # Containerized production deployment
├── requirements.txt        # Python package dependencies
└── memory.db               # Embedded SQLite persistent storage
```

---

## Quick Start & Installation

### 1. Clone & Setup Environment
```bash
git clone https://github.com/mdsharifmia-dev/News-Collector-Agent.git
cd News-Collector-Agent

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment Variables
Create a `.env` file in the root directory:
```env
TELEGRAM_BOT_TOKEN="your_telegram_bot_token"
GEMINI_API_KEY="your_api_key_here"  # Or your preferred LLM API key
ALLOWED_USER_ID=your_telegram_numeric_id
```

### 3. Run Locally
```bash
python bot.py
```

### 4. Or Run with Docker
```bash
docker build -t news-collector-agent .
docker run -d --name news-agent --restart always --env-file .env news-collector-agent
```

---

## Engineering & Contact

- **Developer:** [Md Sharif Mia](https://github.com/mdsharifmia-dev)
- **Email:** [mdsharifmia.dev@gmail.com](mailto:mdsharifmia.dev@gmail.com)
- **GitHub:** [github.com/mdsharifmia-dev](https://github.com/mdsharifmia-dev)
