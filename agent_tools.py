import sqlite3
import datetime
from duckduckgo_search import DDGS

# --- Database Initialization ---
def init_db():
    conn = sqlite3.connect("memory.db")
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS notes (id INTEGER PRIMARY KEY, title TEXT, content TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS reminders (id INTEGER PRIMARY KEY, message TEXT, remind_at TIMESTAMP, is_sent INTEGER DEFAULT 0)''')
    
    # Tables for Daily AI News and Hackathons
    cursor.execute('''CREATE TABLE IF NOT EXISTS daily_news (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        publish_date TEXT NOT NULL,
        category TEXT NOT NULL,
        title TEXT NOT NULL,
        title_bn TEXT,
        short_summary_bn TEXT,
        source_name TEXT NOT NULL,
        url TEXT UNIQUE NOT NULL,
        cached_summary TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    cursor.execute('''CREATE INDEX IF NOT EXISTS idx_daily_news_date ON daily_news(publish_date)''')
    
    # Safe alter table for existing DB
    try:
        cursor.execute("ALTER TABLE daily_news ADD COLUMN title_bn TEXT")
    except Exception:
        pass
    try:
        cursor.execute("ALTER TABLE daily_news ADD COLUMN short_summary_bn TEXT")
    except Exception:
        pass

    cursor.execute('''CREATE TABLE IF NOT EXISTS daily_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_name TEXT NOT NULL,
        organizer TEXT NOT NULL,
        location_type TEXT NOT NULL,
        prize_pool TEXT,
        deadline TEXT,
        url TEXT UNIQUE NOT NULL,
        status TEXT DEFAULT 'ACTIVE',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS user_selection_state (
        user_id INTEGER PRIMARY KEY,
        active_message_id INTEGER NOT NULL,
        selected_news_ids TEXT NOT NULL,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS github_trending (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fetch_date TEXT NOT NULL,
        repo_name TEXT NOT NULL,
        repo_url TEXT UNIQUE NOT NULL,
        stars INTEGER DEFAULT 0,
        description TEXT,
        description_bn TEXT,
        language TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    conn.commit()
    conn.close()

init_db()

# --- MEMORY TOOLS ---
def save_note(title: str, content: str) -> str:
    """Saves a personal note or important information for the user."""
    try:
        conn = sqlite3.connect("memory.db")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO notes (title, content) VALUES (?, ?)", (title, content))
        conn.commit()
        conn.close()
        return f"Note '{title}' saved successfully."
    except Exception as e:
        return f"Failed to save note: {e}"

def read_notes() -> str:
    """Reads and retrieves all saved personal notes of the user."""
    try:
        conn = sqlite3.connect("memory.db")
        cursor = conn.cursor()
        cursor.execute("SELECT title, content FROM notes")
        rows = cursor.fetchall()
        conn.close()
        if not rows: return "No notes found in memory."
        return "Saved Notes:\n" + "\n".join([f"- {r[0]}: {r[1]}" for r in rows])
    except Exception as e:
        return f"Failed to read notes: {e}"

# --- WEB SEARCH TOOL ---
def search_web(query: str) -> str:
    """Searches the internet for real-time information, news, or facts."""
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=3))
        if not results: return "No results found on the web."
        return "Web Search Results:\n" + "\n".join([f"- {r['title']}: {r['body']}" for r in results])
    except Exception as e:
        return f"Error performing web search: {str(e)}"

# --- SCHEDULER TOOL ---
def set_reminder(minutes_from_now: int, message: str) -> str:
    """Sets a timer to remind the user about something after a specific number of minutes."""
    try:
        remind_at = datetime.datetime.now() + datetime.timedelta(minutes=minutes_from_now)
        conn = sqlite3.connect("memory.db")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO reminders (message, remind_at) VALUES (?, ?)", (message, remind_at))
        conn.commit()
        conn.close()
        return f"Success! Reminder set for {minutes_from_now} minutes from now."
    except Exception as e:
        return f"Error setting reminder: {e}"

# --- GITHUB TRENDING AI PROJECTS ---
def fetch_github_trending_ai(limit: int = 5) -> list:
    """
    Fetches the top trending AI & Open Source repositories from GitHub.
    Returns list of dicts with repo_name, url, stars, description, description_bn, language.
    """
    import urllib.request
    import json
    import os
    import google.generativeai as genai
    
    url = f"https://api.github.com/search/repositories?q=topic:ai+stars:%3E1000&sort=stars&order=desc&per_page={limit}"
    req = urllib.request.Request(url, headers={"User-Agent": "1st-Agent-Bot/1.0"})
    
    results = []
    try:
        res = urllib.request.urlopen(req, timeout=10)
        data = json.loads(res.read())
        items = data.get("items", [])[:limit]
        
        prompt_lines = []
        for idx, it in enumerate(items, 1):
            desc = it.get("description") or "No description provided."
            prompt_lines.append(f"{idx}. {desc}")
            
        gemini_key = (os.getenv("GEMINI_API_KEY") or "").strip().strip('"').strip("'")
        translated_map = {}
        if gemini_key:
            try:
                genai.configure(api_key=gemini_key)
                m = genai.GenerativeModel("gemini-3.5-flash-lite")
                tr_prompt = f"""নিচের ইংরেজি টেক্সটগুলোর প্রতিটির জন্য সহজ বাংলায় ১-২ লাইনের ভাবানুবাদ করো।
{chr(10).join(prompt_lines)}

JSON ফরম্যাটে উত্তর দাও:
[
  {{"index": 1, "bn": "বাংলা অনুবাদ"}}
]
শুধুমাত্র ভ্যালিড JSON ছাড়া অন্য কোনো লেখা দেবে না।"""
                resp = m.generate_content(tr_prompt)
                tr_text = resp.text.strip()
                if tr_text.startswith("```"):
                    import re
                    tr_text = re.sub(r"^```[a-zA-Z]*\n?", "", tr_text)
                    tr_text = re.sub(r"\n?```$", "", tr_text).strip()
                tr_json = json.loads(tr_text)
                for entry in tr_json:
                    translated_map[entry.get("index")] = entry.get("bn")
            except Exception:
                pass
                
        for idx, it in enumerate(items, 1):
            name = it.get("full_name", "")
            r_url = it.get("html_url", "")
            stars = it.get("stargazers_count", 0)
            desc = it.get("description") or "No description"
            lang = it.get("language") or "Python"
            desc_bn = translated_map.get(idx, desc)
            results.append({
                "repo_name": name,
                "url": r_url,
                "stars": stars,
                "description": desc,
                "description_bn": desc_bn,
                "language": lang
            })
            
            # Cache in SQLite
            try:
                conn = sqlite3.connect("memory.db")
                cur = conn.cursor()
                now_str = datetime.date.today().strftime("%Y-%m-%d")
                cur.execute("""
                    INSERT INTO github_trending (fetch_date, repo_name, repo_url, stars, description, description_bn, language)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(repo_url) DO UPDATE SET stars=excluded.stars, description_bn=excluded.description_bn
                """, (now_str, name, r_url, stars, desc, desc_bn, lang))
                conn.commit()
                conn.close()
            except Exception:
                pass
                
    except Exception:
        pass
        
    return results

# --- YOUTUBE VIDEO SUMMARIZER ---
def summarize_youtube_video(url: str) -> dict:
    """
    Extracts video details via YouTube oEmbed / Jina AI reader and generates
    a 5-10 line structured Bengali summary.
    """
    import urllib.request
    import json
    import os
    import requests
    import google.generativeai as genai
    
    title = "ইউটিউব ভিডিও"
    author = "ক্রিয়েটর"
    try:
        oembed_url = f"https://www.youtube.com/oembed?url={url}&format=json"
        req = urllib.request.Request(oembed_url, headers={"User-Agent": "Mozilla/5.0"})
        res = urllib.request.urlopen(req, timeout=8)
        meta = json.loads(res.read())
        title = meta.get("title", title)
        author = meta.get("author_name", author)
    except Exception:
        pass
        
    content_text = ""
    try:
        jina_url = f"https://r.jina.ai/{url}"
        resp = requests.get(jina_url, headers={"User-Agent": "1st-Agent-Bot/1.0"}, timeout=12)
        if resp.status_code == 200 and len(resp.text) > 100:
            content_text = resp.text[:7000]
    except Exception:
        pass
        
    if not content_text:
        content_text = f"Title: {title}. Channel: {author}. URL: {url}"
        
    gemini_key = (os.getenv("GEMINI_API_KEY") or "").strip().strip('"').strip("'")
    if not gemini_key:
        return {"title": title, "author": author, "summary": "Gemini API কী পাওয়া যায়নি।", "url": url}
        
    genai.configure(api_key=gemini_key)
    m = genai.GenerativeModel("gemini-3.5-flash-lite")
    prompt = f"""তুমি একজন দক্ষ টেক অ্যানালিস্ট ও ভিডিও কন্টেন্ট সামারাইজার।
নিচের ইউটিউব ভিডিওর তথ্য বিশ্লেষণ করে বাংলায় একটি স্পষ্ট, সুগঠিত ৫ থেকে ১০ লাইনের সামারি তৈরি করো।

ভিডিও শিরোনাম: {title}
চ্যানেল: {author}
লিংক: {url}
কনটেন্ট/তথ্য:
{content_text}

নিয়মাবলী:
১. মোট ৫ থেকে ১০ লাইনের মধ্যে সুনির্দিষ্ট পয়েন্টে উপস্থাপন করো।
২. ভাষা হতে হবে সহজবোধ্য ও স্বাভাবিক বাংলা।
৩. কোনো ইমোজি ব্যবহার করবে না।
৪. নিচের ৩টি পয়েন্টের কাঠামোর মধ্যে সামারি দাও:
- মূল বিষয়বস্তু ও বিষয়সংক্ষেপ: (২-৩ লাইন)
- প্রধান টেকনিক্যাল পয়েন্ট ও শিক্ষণীয় দিক: (৩-৪ লাইন)
- সিদ্ধান্ত ও কাদের দেখা উচিত: (১-২ লাইন)
"""
    try:
        res = m.generate_content(prompt)
        summary = res.text.strip()
    except Exception as e:
        summary = f"ভিডিও সামারি জেনারেট করতে সমস্যা হয়েছে: {e}"
        
    return {
        "title": title,
        "author": author,
        "summary": summary,
        "url": url
    }

# --- SOCIAL MEDIA POST GENERATOR ---
def generate_social_post(topic_or_id: str) -> str:
    """
    Generates a ready-to-publish professional LinkedIn / Facebook post in natural Bengali with hashtags.
    """
    import sqlite3
    import os
    import google.generativeai as genai
    
    context_text = topic_or_id.strip()
    
    if context_text.isdigit():
        nid = int(context_text)
        try:
            conn = sqlite3.connect("memory.db")
            cur = conn.cursor()
            cur.execute("SELECT title, title_bn, short_summary_bn, url FROM daily_news WHERE id=?", (nid,))
            row = cur.fetchone()
            conn.close()
            if row:
                t_bn = row[1] or row[0]
                s_bn = row[2] or ""
                url = row[3]
                context_text = f"শিরোনাম: {t_bn}\nসারসংক্ষেপ: {s_bn}\nসোর্স লিংক: {url}"
        except Exception:
            pass
            
    gemini_key = (os.getenv("GEMINI_API_KEY") or "").strip().strip('"').strip("'")
    if not gemini_key:
        return "Gemini API কী কনফিগার করা নেই।"
        
    genai.configure(api_key=gemini_key)
    m = genai.GenerativeModel("gemini-3.5-flash-lite")
    prompt = f"""তুমি একজন শীর্ষমানের সোশ্যাল মিডিয়া টেক ইনফ্লুয়েন্সার ও কনটেন্ট রাইটার।
নিচের টেক বা এআই টপিকটির ওপর ভিত্তি করে লিংকডইন (LinkedIn) ও ফেসবুকে পোস্ট করার উপযোগী একটি আকর্ষণীয় পোস্ট তৈরি করো।

টপিক/তথ্য:
{context_text}

পোস্ট ফরম্যাট ও নিয়মাবলী:
১. ভাষা: স্বাভাবিক, প্রাঞ্জল ও প্রফেশনাল বাংলা (প্রয়োজনে টেকনিক্যাল টার্ম ইংরেজিতে রাখা যাবে)।
২. প্রথম লাইনে থাকবে একটি শক্তিশালী হুক (Hook) যা মানুষের মনোযোগ আকর্ষণ করবে।
৩. মাঝে ৩ থেকে ৪টি স্পষ্ট বুলেট পয়েন্টে মূল অন্তর্দৃষ্টি বা শিক্ষণীয় বিষয় তুলে ধরবে।
৪. শেষে পাঠকদের মতামত জানতে চেয়ে একটি প্রশ্ন রাখবে (Call to Action)।
৫. একেবারে শেষে প্রাসঙ্গিক ৪-৫টি ট্রেন্ডিং হ্যাশট্যাগ (যেমন #ArtificialIntelligence #TechUpdate #Innovation) দেবে।
৬. কোনো ইমোজি ব্যবহার করবে না। সম্পূর্ণ ক্লিন ও প্রফেশনাল টেক্সট রাখবে।
"""
    try:
        res = m.generate_content(prompt)
        return res.text.strip()
    except Exception as e:
        return f"পোস্ট ড্রাফট তৈরিতে সমস্যা হয়েছে: {e}"

# ========================================================
# SUPERPOWERS ENGINEERING SUITE
# ========================================================

def systematic_debug(code_or_error: str) -> str:
    """
    Executes 4-phase systematic debugging:
    Phase 1: Problem Definition & Error Trace
    Phase 2: Root Cause Analysis with Technical Evidence
    Phase 3: Surgical Minimal Code Fix
    Phase 4: Prevention & Verification Strategy
    """
    import os
    import google.generativeai as genai
    
    gemini_key = (os.getenv("GEMINI_API_KEY") or "").strip().strip('"').strip("'")
    if not gemini_key:
        return "Gemini API কী কনফিগার করা নেই।"
        
    genai.configure(api_key=gemini_key)
    m = genai.GenerativeModel("gemini-3.5-flash-lite")
    prompt = f"""তুমি একজন শীর্ষমানের সিনিয়র সফটওয়্যার আর্কিটেক্ট ও সিস্টেমেটিক ডিবাগিং স্পেশালিস্ট (Superpowers Systematic Debugging Framework)।
নিচের কোড বা এররটি বিশ্লেষণ করে সিস্টেমেটিক ডিবাগিং মেথডোলজি অনুযায়ী ৪টি স্পষ্ট ধাপে বাংলায় সমাধান দাও।

কোড / এরর মেসেজ:
{code_or_error}

নির্দেশনা ও কাঠামোর ধাপসমূহ:
ধাপ ১: সমস্যার ধরন ও এরর ট্রেস (কী ঘটছে এবং কোথায় ফেইল করছে)
ধাপ ২: মূল কারণ বিশ্লেষণ (Root Cause Analysis - টেকনিক্যাল প্রমাণসহ আসল কারণ)
ধাপ ৩: সুনির্দিষ্ট ও নিখুঁত সমাধান কোড (Surgical Code Fix - সমাধান কোড ব্লকসহ)
ধাপ ৪: প্রতিরোধ ও ভেরিফিকেশন কৌশল (ভবিষ্যতে এই বাগ এড়াতে টেস্ট কেস ও সতর্কতা)

কড়া নিয়ম: কোনো অবস্থাতেই কোনো ইমোজি ব্যবহার করবে না। সম্পূর্ণ প্রফেশনাল, টেক্সট-অনলি ও মার্জিত বাংলায় উত্তর দাও।
"""
    try:
        res = m.generate_content(prompt)
        return res.text.strip()
    except Exception as e:
        return f"সিস্টেমেটিক ডিবাগিংয়ে ত্রুটি ঘটেছে: {e}"

def generate_tdd_suite(requirement: str) -> str:
    """
    Generates a strict Test-Driven Development (TDD) workflow:
    Step 1 (Red): Comprehensive failing unit tests
    Step 2 (Green): Minimal passing implementation
    Step 3 (Refactor): Clean, production-grade refactored code
    """
    import os
    import google.generativeai as genai
    
    gemini_key = (os.getenv("GEMINI_API_KEY") or "").strip().strip('"').strip("'")
    if not gemini_key:
        return "Gemini API কী কনফিগার করা নেই।"
        
    genai.configure(api_key=gemini_key)
    m = genai.GenerativeModel("gemini-3.5-flash-lite")
    prompt = f"""তুমি একজন টেস্ট-ড্রিভেন ডেভেলপমেন্ট (TDD) বিশেষজ্ঞ (Superpowers TDD Protocol)।
নিচের রিকোয়ারমেন্টের জন্য কঠোরভাবে Red-Green-Refactor সাইকেল মেনে পূর্ণাঙ্গ কোড ও টেস্ট স্যুট তৈরি করো।

রিকোয়ারমেন্ট / ফাংশন ডেসক্রিপশন:
{requirement}

আউটপুট কাঠামো:
১. ধাপ ১ (Red - ফেইলিং টেস্ট স্যুট):
   - এজ-কেস এবং ভ্যালিডেশন কভার করে পূর্ণাঙ্গ ইউনিট টেস্ট কোড (যেমন: pytest বা unittest)।
২. ধাপ ২ (Green - ন্যূনতম পাসিং কোড):
   - শুধুমাত্র টেস্টগুলো পাস করানোর জন্য ন্যূনতম কার্যকর ইমপ্লিমেন্টেশন।
৩. ধাপ ৩ (Refactor - অপ্টিমাইজড ও ক্লিন কোড):
   - পারফরম্যান্স, ক্লিন কোড প্রিন্সিপাল এবং টাইপ-হিন্টিংসহ রিফ্যাক্টর্ড প্রোডাকশন কোড।

কড়া নিয়ম: কোনো অবস্থাতেই কোনো ইমোজি ব্যবহার করবে না। সম্পূর্ণ প্রফেশনাল, টেক্সট-অনলি ভাষায় উত্তর দেবে।
"""
    try:
        res = m.generate_content(prompt)
        return res.text.strip()
    except Exception as e:
        return f"TDD স্যুট তৈরিতে ত্রুটি ঘটেছে: {e}"

def review_code_security(code: str) -> str:
    """
    Audits code against security risks (OWASP), performance bottlenecks, and code smells.
    """
    import os
    import google.generativeai as genai
    
    gemini_key = (os.getenv("GEMINI_API_KEY") or "").strip().strip('"').strip("'")
    if not gemini_key:
        return "Gemini API কী কনফিগার করা নেই।"
        
    genai.configure(api_key=gemini_key)
    m = genai.GenerativeModel("gemini-3.5-flash-lite")
    prompt = f"""তুমি একজন সিনিয়র প্রিন্সিপাল সফটওয়্যার ইঞ্জিনিয়ার ও সাইবার সিকিউরিটি অডিটর (Superpowers Code Review Protocol)।
নিচের কোডটি নিখুঁতভাবে বিশ্লেষণ করে একটি পূর্ণাঙ্গ কোড রিভিউ ও সিকিউরিটি অডিট রিপোর্ট বাংলায় তৈরি করো।

কোড:
{code}

রিপোর্ট কাঠামো:
১. সিকিউরিটি অডিট (Security Audit):
   - ক্রেডেনশিয়াল লিকেজ, এসকিউএল ইনজেকশন, ইনপুট ভ্যালিডেশন বা ওডব্লিউএএসপি (OWASP) ঝুঁকি আছে কিনা।
২. পারফরম্যান্স ও রিসোর্স অ্যানালাইসিস (Performance & Complexity):
   - টাইম ও স্পেস কমপ্লেক্সিটি, মেমোরি লিক, বা ব্লকিং আই/ও সম্পর্কিত সমস্যা।
3. কোড কোয়ালিটি ও ক্লিন কোড (Clean Code & Refactoring):
   - SOLID ও DRY প্রিন্সিপাল অনুযায়ী ত্রুটি এবং রিফ্যাক্টরিং পরামর্শ।
৪. সংশোধিত নিরাপদ কোড (Recommended Fixed Code):
   - ত্রুটিমুক্ত ও অপ্টিমাইজড কোড ব্লক।

কড়া নিয়ম: কোনো অবস্থাতেই কোনো ইমোজি ব্যবহার করবে না। সম্পূর্ণ প্রফেশনাল টেক্সট-অনলি আউটপুট দেবে।
"""
    try:
        res = m.generate_content(prompt)
        return res.text.strip()
    except Exception as e:
        return f"কোড রিভিউতে ত্রুটি ঘটেছে: {e}"

def brainstorm_architecture(idea: str) -> str:
    """
    Conducts deep architectural and design brainstorming for software projects.
    """
    import os
    import google.generativeai as genai
    
    gemini_key = (os.getenv("GEMINI_API_KEY") or "").strip().strip('"').strip("'")
    if not gemini_key:
        return "Gemini API কী কনফিগার করা নেই।"
        
    genai.configure(api_key=gemini_key)
    m = genai.GenerativeModel("gemini-3.5-flash-lite")
    prompt = f"""তুমি একজন চিফ সিস্টেম আর্কিটেক্ট (Superpowers Brainstorming Protocol)।
নিচের প্রজেক্ট বা ফিচারের আইডিয়াটি গভীরভাবে বিশ্লেষণ করে একটি পরিপূর্ণ আর্কিটেকচারাল ব্রেনস্টর্মিং রিপোর্ট বাংলায় তৈরি করো।

প্রজেক্ট / আইডিয়া:
{idea}

রিপোর্ট কাঠামো:
১. হাই-লেভেল সিস্টেম আর্কিটেকচার (System Architecture & Component Flow)
২. প্রস্তাবিত টেকনোলজি স্ট্যাক ও তার যৌক্তিকতা (Frontend, Backend, Database, Cloud)
৩. ডাটাবেস ডিজাইন ও স্কিমা আইডিয়া (Entities, Relations, Constraints)
৪. সম্ভাব্য চ্যালেঞ্জ ও স্কেলেবিলিটি সমাধান (Bottlenecks, Caching, Fault-tolerance)
৫. পরবর্তী করণীয় ধাপসমূহ (Next Action Steps)

কড়া নিয়ম: কোনো অবস্থাতেই কোনো ইমোজি ব্যবহার করবে না। সম্পূর্ণ প্রফেশনাল টেক্সট-অনলি আউটপুট দেবে।
"""
    try:
        res = m.generate_content(prompt)
        return res.text.strip()
    except Exception as e:
        return f"ব্রেনস্টর্মিংয়ে ত্রুটি ঘটেছে: {e}"

# ========================================================
# SPEC-KIT SPEC-DRIVEN DEVELOPMENT (SDD) SUITE
# ========================================================

def generate_speckit_spec(feature_idea: str) -> str:
    """
    Drafts a formal GitHub Spec-Kit functional specification (spec.md).
    """
    import os
    import google.generativeai as genai
    
    gemini_key = (os.getenv("GEMINI_API_KEY") or "").strip().strip('"').strip("'")
    if not gemini_key:
        return "Gemini API কী কনফিগার করা নেই।"
        
    genai.configure(api_key=gemini_key)
    m = genai.GenerativeModel("gemini-3.5-flash-lite")
    prompt = f"""তুমি একজন অভিজ্ঞ স্পেক-কিট আর্কিটেক্ট (GitHub Spec-Kit SDD Protocol)।
নিচের ফিচারের জন্য একটি ফর্মাল ও পূর্ণাঙ্গ স্পেসিফিকেশন ডকুমেন্ট (spec.md) বাংলায় তৈরি করো।

ফিচার বিবরণ:
{feature_idea}

ডকুমেন্টের প্রয়োজনীয় সেকশনসমূহ:
# Feature Specification: [ফিচারের নাম]
1. Executive Summary & Objective (উদ্দেশ্য ও সারসংক্ষেপ)
2. User Scenarios & Stories (ইউজার স্টোরি এবং Given-When-Then ফরম্যাটে Acceptance Criteria)
3. Functional Requirements (বাধ্যতামূলক ফাংশনাল রিকোয়ারমেন্টস)
4. Non-Functional Constraints (পারফরম্যান্স, সিকিউরিটি ও রিলায়েবিলিটি রুলস)
5. Out of Scope & Edge Cases (কোন বিষয়গুলো এই স্কোপের বাইরে এবং সম্ভাব্য এজ-কেস)

কড়া নিয়ম: কোনো অবস্থাতেই কোনো ইমোজি ব্যবহার করবে না। ফরমাল ও সুনির্দিষ্ট টেক্সট-অনলি বাংলায় আউটপুট দেবে।
"""
    try:
        res = m.generate_content(prompt)
        return res.text.strip()
    except Exception as e:
        return f"স্পেক তৈরিতে ত্রুটি ঘটেছে: {e}"

def generate_speckit_plan(spec_or_idea: str) -> str:
    """
    Drafts a formal GitHub Spec-Kit technical implementation plan (plan.md).
    """
    import os
    import google.generativeai as genai
    
    gemini_key = (os.getenv("GEMINI_API_KEY") or "").strip().strip('"').strip("'")
    if not gemini_key:
        return "Gemini API কী কনফিগার করা নেই।"
        
    genai.configure(api_key=gemini_key)
    m = genai.GenerativeModel("gemini-3.5-flash-lite")
    prompt = f"""তুমি একজন সিনিয়র টেকনিক্যাল লিড (GitHub Spec-Kit Technical Plan Protocol)।
নিচের স্পেসিফিকেশন বা ফিচারের জন্য একটি টেকনিক্যাল প্ল্যান ডকুমেন্ট (plan.md) বাংলায় তৈরি করো।

ইনপুট:
{spec_or_idea}

ডকুমেন্টের প্রয়োজনীয় সেকশনসমূহ:
# Technical Implementation Plan: [ফিচারের নাম]
1. Technical Architecture & Component Flow (আর্কিটেকচার ডায়াগ্রাম ও মডিউল বিভাজন)
2. Data Contracts & Models (YAML বা JSON স্কিমা এবং ডাটাবেস টেবিল স্ট্রাকচার)
3. API & Method Signatures (ফাংশন ও এন্ডপয়েন্ট প্রোটোকল)
4. Security & Error Handling Strategy (ত্রুটি হ্যান্ডলিং এবং সিকিউরিটি হার্নেস)
5. Verification & Test Plan (কীভাবে ভেরিফাই ও টেস্ট করা হবে)

কড়া নিয়ম: কোনো অবস্থাতেই কোনো ইমোজি ব্যবহার করবে না। সম্পূর্ণ প্রফেশনাল টেক্সট-অনলি আউটপুট দেবে।
"""
    try:
        res = m.generate_content(prompt)
        return res.text.strip()
    except Exception as e:
        return f"প্ল্যান তৈরিতে ত্রুটি ঘটেছে: {e}"

def generate_speckit_tasks(plan_or_idea: str) -> str:
    """
    Generates a prioritized, dependency-ordered tasks checklist (tasks.md).
    """
    import os
    import google.generativeai as genai
    
    gemini_key = (os.getenv("GEMINI_API_KEY") or "").strip().strip('"').strip("'")
    if not gemini_key:
        return "Gemini API কী কনফিগার করা নেই।"
        
    genai.configure(api_key=gemini_key)
    m = genai.GenerativeModel("gemini-3.5-flash-lite")
    prompt = f"""তুমি একজন স্পেক-কিট টাস্ক প্ল্যানার (GitHub Spec-Kit Tasks Protocol)।
নিচের প্ল্যান বা ফিচারের জন্য ডিপেনডেন্সি-অর্ডার্ড টাস্ক চেকলিস্ট (tasks.md) বাংলায় তৈরি করো।

প্ল্যান / ফিচার:
{plan_or_idea}

টাস্ক চেকলিস্টের নিয়মাবলী:
১. প্রতিটি কাজকে ফেজ বা ধাপে ভাগ করো (যেমন: ফেজ ১ - পরিবেশ ও স্কিমা সেটআপ, ফেজ ২ - কোর বিজনেস লজিক, ফেজ ৩ - ইন্টিগ্রেশন ও টেস্ট, ফেজ ৪ - ফাইনাল ভেরিফিকেশন)।
২. প্রতিটি টাস্ক পরিষ্কার `[ ]` চেকবক্স ফরম্যাটে হবে (যেমন: `[ ] Task 1.1: ডাটাবেস টেবিল তৈরি করা`)।
৩. প্রতিটি টাস্ক স্বাধীন, টেস্টযোগ্য এবং সুনির্দিষ্ট হতে হবে।

কড়া নিয়ম: কোনো অবস্থাতেই কোনো ইমোজি ব্যবহার করবে না। সম্পূর্ণ প্রফেশনাল টেক্সট-অনলি আউটপুট দেবে।
"""
    try:
        res = m.generate_content(prompt)
        return res.text.strip()
    except Exception as e:
        return f"টাস্ক লিস্ট তৈরিতে ত্রুটি ঘটেছে: {e}"
