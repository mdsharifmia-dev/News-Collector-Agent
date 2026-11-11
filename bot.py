import os
import re
import html
import asyncio
import logging
import sqlite3
import datetime
from zoneinfo import ZoneInfo
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import google.generativeai as genai

# Import our custom tools & modules
from agent_tools import (
    save_note, read_notes, search_web, set_reminder,
    fetch_github_trending_ai, summarize_youtube_video, generate_social_post,
    systematic_debug, generate_tdd_suite, review_code_security, brainstorm_architecture,
    generate_speckit_spec, generate_speckit_plan, generate_speckit_tasks
)
from news_collector import collect_top_20_ai_news, collect_hackathons_and_competitions, get_current_date_str
from news_summarizer import get_or_create_news_summary

# Load environment variables
load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
ALLOWED_USER_ID = int(str(os.getenv("ALLOWED_USER_ID", "8753623935")).strip().strip('"').strip("'"))

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)

system_instruction = """
তুমি একজন বুদ্ধিমান, কর্মতৎপর ও অত্যন্ত দক্ষ 24/7 পার্সোনাল এআই অ্যাসিস্ট্যান্ট এবং সফটওয়্যার ইঞ্জিনিয়ারিং স্পেশালিস্ট এজেন্ট। তুমি সবসময় প্রাঞ্জল ও সম্মানজনক বাংলায় কথা বলবে।

তোমার সিস্টেম ও ক্ষমতার পূর্ণ বিবরণ:
১. ২৪/৭ ক্লাউড সার্ভিস ও অটোমেশন:
   - তুমি ২৪ ঘণ্টা অনলাইনে সক্রিয় আছো (Render ক্লাউড সার্ভার ও অটোমেশন দ্বারা পরিচালিত)।
   - প্রতিদিন সকাল ৮:০০ টায় (বাংলাদেশ সময় / Asia/Dhaka) তুমি সম্পূর্ণ স্বয়ংক্রিয়ভাবে ইউজারকে "Daily AI News & Hackathons Digest" পাঠাও।
   - ইউজার যেকোনো সময় `/news` লিখে তাৎক্ষণিকভাবে আজকের টপ ২০টি এআই নিউজ এবং বাংলাদেশ ও গ্লোবাল হ্যাকাথনের আপডেট পেতে পারেন।
   - প্রতিটি নিউজের হেডলাইনের সাথে সরাসরি ইন্টারেক্টিভ [ ] বিস্তারিত পড়ুন বাটন রয়েছে, যাতে ক্লিক করলেই তাৎক্ষণিকভাবে ১০-১৫ লাইনের গভীর বাংলা সারসংক্ষেপ ও রিসার্চ পেপারের লিংক প্রসারিত হয়।
   - পুনরায় [X] সংক্ষেপ করুন বাটনে ক্লিক করলে তা সংকুচিত হয়ে পূর্বের অবস্থায় ফিরে আসে।
   - কোনো ব্লারি বা অস্বস্তিকর পপআপ ব্যানার ছাড়াই স্মুথ ইন-লাইন রিডিং এক্সপেরিয়েন্স প্রদান করে।
   - ইউজার সরাসরি `/read_১` বা `/read ১` টাইপ করেও নির্দিষ্ট নিউজের ১০-১৫ লাইনের সামারি এক ক্লিকে পড়তে পারেন।

২. সুপারপাওয়ার্স ইঞ্জিনিয়ারিং স্কিলস (Superpowers Engineering Suite):
   - systematic_debug: সিস্টেমেটিক ডিবাগিং (৪টি ধাপে রুট-কজ বিশ্লেষণ, কোড ফিক্স ও ভেরিফিকেশন)।
   - generate_tdd_suite: টেস্ট-ড্রিভেন ডেভেলপমেন্ট (Red-Green-Refactor সাইকেল মেনে টেস্ট স্যুট ও কোড)।
   - review_code_security: কোড রিভিউ ও সিকিউরিটি অডিট (OWASP ঝুঁকি, পারফরম্যান্স, ক্লিন কোড বিশ্লেষণ)।
   - brainstorm_architecture: ডিপ সিস্টেম আর্কিটেকচার ও ব্রেনস্টর্মিং (টেক স্ট্যাক, ডাটাবেস স্কিমা ও সমাধান)।

৩. স্পেক-কিট ডেভেলপমেন্ট স্কিলস (GitHub Spec-Kit SDD Suite):
   - generate_speckit_spec: ফর্মাল স্পেসিফিকেশন ডকুমেন্ট (spec.md - ইউজার স্টোরি, একসেপ্ট্যান্স ক্রাইটেরিয়া ও রিকয়ারমেন্টস)।
   - generate_speckit_plan: টেকনিক্যাল ইমপ্লিমেন্টেশন প্ল্যান (plan.md - আর্কিটেকচার, ডাটা কন্ট্রাক্টস ও মেথডস)।
   - generate_speckit_tasks: ডিপেনডেন্সি-অর্ডার্ড অ্যাকশনেবল টাস্ক চেকলিস্ট (tasks.md)।

৪. কনটেন্ট, মিডিয়া ও মেমোরি টুলস:
   - summarize_youtube_video: ইউটিউব ভিডিওর ৫-১০ লাইনের বাংলা সারসংক্ষেপ।
   - generate_social_post: লিংকডইন ও ফেসবুকের জন্য প্রফেশনাল টেক পোস্ট ড্রাফট।
   - fetch_github_trending_ai: গিটহাবের শীর্ষ ৫টি ট্রেন্ডিং এআই রিপোজিটরির তথ্য।
   - search_web: রিয়েল-টাইম ওয়েব সার্চ।
   - save_note / read_notes: ইউজারের গুরুত্বপূর্ণ তথ্য সংরক্ষণ ও পড়া।
   - set_reminder: নির্দিষ্ট সময়ের রিমাইন্ডার সেট করা।

৫. সাধারণ আচরণ ও কড়া নিয়মাবলী:
   - কোনো অবস্থাতেই চ্যাটে বা কোডে কোনো ইমোজি ব্যবহার করবে না। সম্পূর্ণ প্রফেশনাল, টেক্সট-অনলি মার্জিত বাংলায় উত্তর দেবে।
   - ইউজার যদি কোনো কোড সমস্যা, প্ল্যানিং বা ডেভেলপমেন্টের কথা বলেন, তবে সংশ্লিষ্ট সুপারপাওয়ার্স বা স্পেক-কিট মেথডোলজি মেনে নিখুঁত উত্তর দেবে।
"""

# Initialize Model with Tools (using ultra-fast and reliable gemini-3.5-flash-lite)
PRIMARY_MODEL_NAME = 'gemini-3.5-flash-lite'
model = genai.GenerativeModel(
    model_name=PRIMARY_MODEL_NAME,
    system_instruction=system_instruction,
    tools=[
        save_note, read_notes, search_web, set_reminder,
        systematic_debug, generate_tdd_suite, review_code_security, brainstorm_architecture,
        generate_speckit_spec, generate_speckit_plan, generate_speckit_tasks
    ]
)

chat_session = model.start_chat(enable_automatic_function_calling=True)

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# Global instances for thread-safe web triggers
APP_INSTANCE = None
APP_LOOP = None

# In-memory selection cache: {user_id: set([news_id_1, news_id_2])}
USER_SELECTIONS = {}

def split_message_text(text: str, max_chunk_size: int = 4000) -> list:
    """
    Splits text of arbitrary length into chunks of at most max_chunk_size characters.
    Prioritizes splitting at paragraphs (\n\n), then lines (\n), then spaces, then character boundaries.
    """
    if not text:
        return []
    if len(text) <= max_chunk_size:
        return [text]
        
    chunks = []
    remaining = text
    
    while len(remaining) > max_chunk_size:
        split_idx = -1
        p_idx = remaining.rfind("\n\n", 0, max_chunk_size)
        if p_idx > max_chunk_size // 2:
            split_idx = p_idx + 2
        else:
            n_idx = remaining.rfind("\n", 0, max_chunk_size)
            if n_idx > max_chunk_size // 3:
                split_idx = n_idx + 1
            else:
                s_idx = remaining.rfind(" ", 0, max_chunk_size)
                if s_idx > max_chunk_size // 4:
                    split_idx = s_idx + 1
                else:
                    split_idx = max_chunk_size
                    
        chunks.append(remaining[:split_idx].strip())
        remaining = remaining[split_idx:].strip()
        
    if remaining:
        chunks.append(remaining)
        
    return [c for c in chunks if c]

def format_audio_duration_bn(seconds: int) -> str:
    """Formats audio duration in seconds to clean Bengali string."""
    bn_digits = str.maketrans('0123456789', '০১২৩৪৫৬৭৮৯')
    if not seconds or seconds < 1:
        return "কয়েক সেকেন্ড"
    mins = seconds // 60
    secs = seconds % 60
    if mins > 0 and secs > 0:
        return f"{str(mins).translate(bn_digits)} মিনিট {str(secs).translate(bn_digits)} সেকেন্ড"
    elif mins > 0:
        return f"{str(mins).translate(bn_digits)} মিনিট"
    else:
        return f"{str(secs).translate(bn_digits)} সেকেন্ড"

async def safe_send_message(bot, chat_id: int, text: str, reply_markup=None, disable_web_page_preview=False, disable_notification=False):
    """
    Safely sends messages of any length by splitting into <=4000 char chunks.
    Ensures Message_too_long is never raised.
    """
    chunks = split_message_text(text, max_chunk_size=4000)
    if not chunks:
        return None
        
    last_msg = None
    for idx, chunk in enumerate(chunks):
        markup = reply_markup if (idx == len(chunks) - 1) else None
        try:
            last_msg = await bot.send_message(
                chat_id=chat_id,
                text=chunk,
                reply_markup=markup,
                parse_mode="HTML",
                disable_web_page_preview=disable_web_page_preview,
                disable_notification=disable_notification
            )
        except Exception as e:
            logger.warning(f"Telegram HTML send failed for chunk {idx+1} ({e}), sending plain text...")
            clean = re.sub(r"<[^>]+>", "", chunk)
            last_msg = await bot.send_message(
                chat_id=chat_id,
                text=clean,
                reply_markup=markup,
                disable_web_page_preview=disable_web_page_preview,
                disable_notification=disable_notification
            )
        if idx < len(chunks) - 1:
            await asyncio.sleep(0.3)
    return last_msg

async def safe_send_or_edit(bot, chat_id: int, status_msg, text: str, reply_markup=None, disable_web_page_preview=False):
    """
    Edits status_msg with chunk 1, then dispatches subsequent chunks as new messages.
    Completely eliminates Message_too_long error across voice, vision, commands and chat.
    """
    chunks = split_message_text(text, max_chunk_size=4000)
    if not chunks:
        return None
        
    first_chunk = chunks[0]
    markup = reply_markup if len(chunks) == 1 else None
    
    try:
        await bot.edit_message_text(
            chat_id=chat_id,
            message_id=status_msg.message_id,
            text=first_chunk,
            reply_markup=markup,
            parse_mode="HTML",
            disable_web_page_preview=disable_web_page_preview
        )
    except Exception as e:
        logger.warning(f"edit_message_text HTML failed ({e}), falling back to plain text or fresh send...")
        clean = re.sub(r"<[^>]+>", "", first_chunk)
        try:
            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=status_msg.message_id,
                text=clean,
                reply_markup=markup,
                disable_web_page_preview=disable_web_page_preview
            )
        except Exception:
            try:
                await status_msg.delete()
            except Exception:
                pass
            await bot.send_message(
                chat_id=chat_id,
                text=clean,
                reply_markup=markup,
                disable_web_page_preview=disable_web_page_preview
            )
            
    for idx in range(1, len(chunks)):
        chunk = chunks[idx]
        cur_markup = reply_markup if (idx == len(chunks) - 1) else None
        await asyncio.sleep(0.3)
        try:
            await bot.send_message(
                chat_id=chat_id,
                text=chunk,
                reply_markup=cur_markup,
                parse_mode="HTML",
                disable_web_page_preview=disable_web_page_preview
            )
        except Exception:
            clean = re.sub(r"<[^>]+>", "", chunk)
            await bot.send_message(
                chat_id=chat_id,
                text=clean,
                reply_markup=cur_markup,
                disable_web_page_preview=disable_web_page_preview
            )

# ==========================================
# TELEGRAM HANDLERS
# ==========================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id != ALLOWED_USER_ID: return
    await update.message.reply_text(
        "হ্যালো! আমি আপনার 24/7 পার্সোনাল এআই অ্যাসিস্ট্যান্ট এবং সফটওয়্যার ইঞ্জিনিয়ারিং সুপার-এজেন্ট।\n\n"
        "আমার প্রধান প্রধান ক্ষমতা ও কমান্ডসমূহ:\n\n"
        "1. সুপারপাওয়ার্স ইঞ্জিনিয়ারিং স্যুট:\n"
        "- /debug <কোড বা এরর> : সিস্টেমেটিক ৪-ধাপের রুট-কজ ডিবাগিং ও সমাধান কোড।\n"
        "- /tdd <রিকোয়ারমেন্ট> : Red-Green-Refactor সাইকেল মেনে ইউনিট টেস্ট স্যুট ও কোড।\n"
        "- /review <কোড> : সিকিউরিটি ভালনারেবিলিটি, পারফরম্যান্স ও ক্লিন কোড অডিট।\n"
        "- /brainstorm <আইডিয়া> : সিস্টেম আর্কিটেকচার, টেক স্ট্যাক ও ডাটাবেস ডিজাইন।\n\n"
        "2. স্পেক-কিট SDD ওয়ার্কফ্লো:\n"
        "- /spec <ফিচার> : ফর্মাল স্পেসিফিকেশন ডকুমেন্ট (spec.md)।\n"
        "- /plan <ফিচার/স্পেক> : টেকনিক্যাল ইমপ্লিমেন্টেশন প্ল্যান ও ডাটা কন্ট্রাক্ট (plan.md)।\n"
        "- /tasks <প্ল্যান/ফিচার> : ডিপেনডেন্সি-অর্ডার্ড অ্যাকশনেবল টাস্ক চেকলিস্ট (tasks.md)।\n\n"
        "3. এআই ইন্টেলিজেন্স ও মিডিয়া:\n"
        "- /news : দৈনিক শীর্ষ ২০ এআই নিউজ ও হ্যাকাথন তালিকা।\n"
        "- /read_1, /read_2 : নির্দিষ্ট নিউজের গভীর বাংলা সামারি।\n"
        "- /trending বা /github : গিটহাব ট্রেন্ডিং এআই ওপেন-সোর্স প্রজেক্ট।\n"
        "- /yt <লিংক> : ৫-১০ লাইনে ইউটিউব ভিডিও সারসংক্ষেপ।\n"
        "- /post <টপিক/আইডি> : রেডি-টু-পাবলিশ লিংকডইন ও ফেসবুক পোস্ট।\n"
        "- ছবি ও ভয়েস নোট : কোড স্ক্রিনশট বা ভয়েস পাঠালে তাৎক্ষণিক প্রসেসিং ও উত্তর।"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id != ALLOWED_USER_ID: return
    
    global chat_session
    user_text = (update.message.text or "").strip()
    if not user_text: return

    # Sentinel Catch-up: Ensure routine daily digest is never forgotten when handling user requests
    asyncio.create_task(check_and_dispatch_daily_digest(context.bot))

    import asyncio
    loop = asyncio.get_running_loop()

    # Auto-detect YouTube URL in text
    yt_pattern = r"(https?://(?:www\.)?(?:youtube\.com/(?:watch\?v=|shorts/)|youtu\.be/)[a-zA-Z0-9_-]{11})"
    yt_match = re.search(yt_pattern, user_text)
    if yt_match:
        yt_url = yt_match.group(1)
        status_msg = await update.message.reply_text("ইউটিউব ভিডিও বিশ্লেষণ ও সামারি তৈরি করছি...")
        res = await loop.run_in_executor(None, summarize_youtube_video, yt_url)
        title = res.get("title", "ভিডিও")
        author = res.get("author", "চ্যানেল")
        summary = res.get("summary", "")
        reply_text = f"ইউটিউব ভিডিও সামারি: {title}\nচ্যানেল: {author}\n━━━━━━━━━━━━━━━━━━━━━━━━━━\n{summary}"
        await safe_send_or_edit(context.bot, chat_id=update.effective_chat.id, status_msg=status_msg, text=reply_text)
        return

    status_msg = await update.message.reply_text("কাজ করছি...")
    max_retries = 3
    
    for attempt in range(max_retries):
        try:
            response = await loop.run_in_executor(None, chat_session.send_message, user_text)
            await safe_send_or_edit(context.bot, chat_id=update.effective_chat.id, status_msg=status_msg, text=response.text)
            break
        except Exception as e:
            logger.warning(f"Gemini API error (attempt {attempt+1}): {e}. Recreating chat session and retrying...")
            try:
                chat_session = model.start_chat(enable_automatic_function_calling=True)
            except Exception:
                pass
            if attempt < max_retries - 1:
                await asyncio.sleep(1.5)
            else:
                logger.error(f"Final Error: {e}")
                try:
                    fallback_resp = await loop.run_in_executor(None, model.generate_content, user_text)
                    await safe_send_or_edit(context.bot, chat_id=update.effective_chat.id, status_msg=status_msg, text=fallback_resp.text)
                except Exception as final_e:
                    logger.error(f"Fallback Error: {final_e}")
                    await safe_send_or_edit(context.bot, chat_id=update.effective_chat.id, status_msg=status_msg, text="[ত্রুটি] গুগলের সার্ভার কানেকশন ড্রপ করেছে। দয়া করে কিছুক্ষণ পর আবার ট্রাই করুন।")

# ==========================================
# ADVANCED SKILL HANDLERS
# ==========================================

async def handle_youtube_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles /yt <url> command to summarize YouTube videos."""
    if update.effective_user.id != ALLOWED_USER_ID: return
    
    args = context.args
    if not args:
        await update.message.reply_text("ব্যবহারের নিয়ম: /yt <ইউটিউব লিংক>\nযেমন: /yt https://www.youtube.com/watch?v=...")
        return
        
    url = args[0].strip()
    status_msg = await update.message.reply_text("ইউটিউব ভিডিও বিশ্লেষণ ও সামারি তৈরি করছি...")
    loop = asyncio.get_running_loop()
    res = await loop.run_in_executor(None, summarize_youtube_video, url)
    title = res.get("title", "ভিডিও")
    author = res.get("author", "চ্যানেল")
    summary = res.get("summary", "")
    reply_text = f"ইউটিউব ভিডিও সামারি: {title}\nচ্যানেল: {author}\n━━━━━━━━━━━━━━━━━━━━━━━━━━\n{summary}"
    await safe_send_or_edit(context.bot, chat_id=update.effective_chat.id, status_msg=status_msg, text=reply_text)

async def handle_post_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles /post <topic_or_id> command to draft LinkedIn & Facebook tech posts."""
    if update.effective_user.id != ALLOWED_USER_ID: return
    
    query = " ".join(context.args).strip() if context.args else ""
    if not query:
        await update.message.reply_text("ব্যবহারের নিয়ম: /post <টপিক বা নিউজ নম্বর>\nযেমন: /post 1 অথবা /post Gemini 3.5 Flash")
        return
        
    status_msg = await update.message.reply_text("লিংকডইন ও ফেসবুক পোস্ট ড্রাফট তৈরি করছি...")
    loop = asyncio.get_running_loop()
    post_content = await loop.run_in_executor(None, generate_social_post, query)
    await safe_send_or_edit(context.bot, chat_id=update.effective_chat.id, status_msg=status_msg, text=post_content)

async def handle_trending_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles /trending or /github to display top AI repositories."""
    if update.effective_user.id != ALLOWED_USER_ID: return
    
    status_msg = await update.message.reply_text("গিটহাবের শীর্ষ ট্রেন্ডিং এআই রিপোজিটরি সংগ্রহ করছি...")
    loop = asyncio.get_running_loop()
    repos = await loop.run_in_executor(None, fetch_github_trending_ai, 5)
    
    if not repos:
        await safe_send_or_edit(context.bot, chat_id=update.effective_chat.id, status_msg=status_msg, text="[ত্রুটি] গিটহাব থেকে ডাটা সংগ্রহ করতে সাময়িক সমস্যা হয়েছে। দয়া করে কিছুক্ষণ পর আবার চেষ্টা করুন।")
        return
        
    bn_digits = str.maketrans('0123456789', '০১২৩৪৫৬৭৮৯')
    lines = [
        "শীর্ষ ৫টি ট্রেন্ডিং এআই ও ওপেন-সোর্স গিটহাব প্রজেক্ট",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    ]
    
    for idx, r in enumerate(repos, 1):
        idx_bn = str(idx).translate(bn_digits)
        stars_formatted = f"{r['stars']:,}".translate(bn_digits)
        lines.append(f"{idx_bn}. {r['repo_name']} (স্টার: {stars_formatted})")
        lines.append(f"   ভাষা: {r['language']}")
        lines.append(f"   বিবরণ: {r['description_bn']}")
        lines.append(f"   লিংক: {r['url']}\n")
        
    reply_text = "\n".join(lines)
    await safe_send_or_edit(context.bot, chat_id=update.effective_chat.id, status_msg=status_msg, text=reply_text, disable_web_page_preview=True)

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles photos and screenshots to diagnose code bugs and analyze images."""
    if update.effective_user.id != ALLOWED_USER_ID: return
    
    # Sentinel Catch-up: Ensure routine daily digest is never forgotten
    asyncio.create_task(check_and_dispatch_daily_digest(context.bot))
    
    status_msg = await update.message.reply_text("ছবি ও স্ক্রিনশট বিশ্লেষণ করছি...")
    loop = asyncio.get_running_loop()
    
    try:
        photo = update.message.photo[-1]
        photo_file = await photo.get_file()
        photo_bytes = bytes(await photo_file.download_as_bytearray())
        
        caption = update.message.caption or (
            "এই ছবিতে বা কোড স্ক্রিনশটে কী দেখানো হয়েছে? কোনো কোড, এরর, বাগ বা ডায়াগ্রাম থাকলে তা বিশ্লেষণ করে পরিষ্কার ও সহজ ভাষায় বাংলায় সমাধান ও ব্যাখ্যা দাও। কোনো ইমোজি ব্যবহার করবে না।"
        )
        
        image_part = {"mime_type": "image/jpeg", "data": photo_bytes}
        response = await loop.run_in_executor(
            None,
            model.generate_content,
            [image_part, caption]
        )
        
        res_text = response.text.strip() if response.text else "ছবি থেকে কোনো ফলাফল পাওয়া যায়নি।"
        await safe_send_or_edit(context.bot, chat_id=update.effective_chat.id, status_msg=status_msg, text=res_text)
    except Exception as e:
        logger.error(f"Photo analysis error: {e}")
        await safe_send_or_edit(context.bot, chat_id=update.effective_chat.id, status_msg=status_msg, text=f"[ত্রুটি] ছবি বিশ্লেষণ করতে সমস্যা হয়েছে: {e}")

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handles voice notes and audio messages of any length (1 min, 5 min, 10+ min).
    Performs speech-to-text recognition, executes voice commands/questions,
    and dispatches multi-part structured responses safely without Message_too_long error.
    """
    if update.effective_user.id != ALLOWED_USER_ID:
        return
        
    voice = update.message.voice or update.message.audio
    if not voice:
        return
        
    # Sentinel Catch-up: Ensure routine daily digest is never forgotten
    asyncio.create_task(check_and_dispatch_daily_digest(context.bot))
        
    duration_sec = getattr(voice, 'duration', 0)
    duration_text = format_audio_duration_bn(duration_sec)
    
    status_msg = await update.message.reply_text(
        f"ভয়েস মেসেজ শুনছি ও বিশ্লেষণ করছি (দৈর্ঘ্য: {duration_text})... অনুগ্রহ করে কিছুক্ষণ অপেক্ষা করুন।"
    )
    
    loop = asyncio.get_running_loop()
    stop_typing = asyncio.Event()
    
    async def keep_typing():
        while not stop_typing.is_set():
            try:
                await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
            except Exception:
                pass
            try:
                await asyncio.wait_for(stop_typing.wait(), timeout=4.5)
            except asyncio.TimeoutError:
                pass

    typing_task = asyncio.create_task(keep_typing())
    
    try:
        # Download voice file with extended timeout for long audio (up to 10-20 minutes)
        voice_file = await voice.get_file(read_timeout=180, write_timeout=180, connect_timeout=60)
        voice_bytes = bytes(await voice_file.download_as_bytearray(read_timeout=180, write_timeout=180, connect_timeout=60))
        
        mime = "audio/ogg"
        if update.message.audio and update.message.audio.mime_type:
            mime = update.message.audio.mime_type
            
        audio_part = {"mime_type": mime, "data": voice_bytes}
        
        voice_prompt = (
            "তুমি একজন অত্যন্ত দক্ষ এআই অ্যাসিস্ট্যান্ট এবং সফটওয়্যার ইঞ্জিনিয়ার। "
            "এই ভয়েস মেসেজটিতে ইউজার কী বলেছেন তা মনোযোগ দিয়ে নিখুঁতভাবে শোনো। "
            "ভয়েস মেসেজটি যেকোনো দৈর্ঘ্যের হতে পারে (১ মিনিট, ৫ মিনিট বা ১০ মিনিট)। "
            "\n\n"
            "তোমার উত্তরটি নিচের দুটি স্পষ্ট অংশে সাজাও:\n\n"
            "১. [ইউজারের কথা / ট্রান্সক্রিপশন]\n"
            "ইউজার অডিওতে যা যা বলেছেন তা হুবহু প্রাঞ্জল বাংলায় লিখে তুলে ধরো। "
            "ইউজার যদি কোনো কোড, এরর বা রিকোয়ারমেন্ট উল্লেখ করে থাকেন, তাও পরিষ্কারভাবে তুলে ধরো।\n\n"
            "২. [উত্তর ও সমাধান / অ্যাকশন]\n"
            "- ইউজার যদি কোনো তথ্য বা প্রশ্নের উত্তর জানতে চান, তবে বিস্তারিত ও প্রফেশনাল বাংলায় সম্পূর্ণ তথ্যবহুল উত্তর দাও।\n"
            "- ইউজার যদি কোনো নির্দেশ বা কমান্ড দেন (যেমন: কোড ডিবাগ করা, TDD টেস্ট লেখা, সিকিউরিটি রিভিউ, আর্কিটেকচার ব্রেনস্টর্মিং, স্পেক তৈরি, নিউজ দেখা ইত্যাদি), তবে সেই নির্দেশনা অনুযায়ী সম্পূর্ণ সমাধান বা কোড প্রস্তুত করে দাও।\n"
            "- ইউজার যদি কোনো প্রজেক্ট বা ফিচারের আইডিয়া ব্যাখ্যা করেন, তবে তা বিশ্লেষণ করে প্রয়োজনীয় প্রযুক্তিগত পরামর্শ ও বাস্তবায়ন ধাপসমূহ উল্লেখ করো।\n\n"
            "কড়া নিয়মাবলী:\n"
            "- কোনো অবস্থাতেই কোনো ইমোজি ব্যবহার করবে না। সম্পূর্ণ প্রফেশনাল, টেক্সট-অনলি মার্জিত বাংলায় উত্তর দেবে।\n"
            "- ইউজারের কথার কোনো অংশ বাদ দেবে না।"
        )
        
        response = await loop.run_in_executor(
            None,
            model.generate_content,
            [audio_part, voice_prompt]
        )
        
        res_text = response.text.strip() if (response and response.text) else "ভয়েস মেসেজ থেকে কোনো উত্তর তৈরি করা যায়নি।"
        
        # Save voice log to SQLite memory for audit and retrieval
        try:
            conn = sqlite3.connect("memory.db")
            c = conn.cursor()
            c.execute("""
                CREATE TABLE IF NOT EXISTS voice_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    duration INTEGER,
                    response TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            c.execute("INSERT INTO voice_logs (user_id, duration, response) VALUES (?, ?, ?)",
                      (update.effective_user.id, duration_sec, res_text))
            conn.commit()
            conn.close()
        except Exception as log_err:
            logger.warning(f"Voice logging error: {log_err}")
        
        final_output = (
            f"[ভয়েস মেসেজ বিশ্লেষণ]\n"
            f"দৈর্ঘ্য: {duration_text}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"{res_text}"
        )
        
        await safe_send_or_edit(
            context.bot,
            chat_id=update.effective_chat.id,
            status_msg=status_msg,
            text=final_output
        )
        
    except Exception as e:
        logger.error(f"Voice analysis error: {e}", exc_info=True)
        error_msg = f"[ত্রুটি] ভয়েস মেসেজ প্রসেস করতে সমস্যা হয়েছে: {e}"
        await safe_send_or_edit(
            context.bot,
            chat_id=update.effective_chat.id,
            status_msg=status_msg,
            text=error_msg
        )
    finally:
        stop_typing.set()
        typing_task.cancel()

# ==========================================
# SUPERPOWERS & SPEC-KIT COMMAND HANDLERS
# ==========================================

async def handle_debug_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles /debug <code_or_error> command for systematic 4-phase debugging."""
    if update.effective_user.id != ALLOWED_USER_ID: return
    query = " ".join(context.args).strip() if context.args else ""
    if not query:
        await update.message.reply_text("ব্যবহারের নিয়ম: /debug <কোড বা এরর মেসেজ>\nযেমন: /debug IndexError: list index out of range in line 45")
        return
    status_msg = await update.message.reply_text("সিস্টেমেটিক ডিবাগিং অ্যানালাইসিস করছি...")
    loop = asyncio.get_running_loop()
    res = await loop.run_in_executor(None, systematic_debug, query)
    await safe_send_message(context.bot, chat_id=update.effective_chat.id, text=res)
    try:
        await status_msg.delete()
    except Exception:
        pass

async def handle_tdd_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles /tdd <requirement> command for Red-Green-Refactor test generation."""
    if update.effective_user.id != ALLOWED_USER_ID: return
    query = " ".join(context.args).strip() if context.args else ""
    if not query:
        await update.message.reply_text("ব্যবহারের নিয়ম: /tdd <ফাংশন বা রিকোয়ারমেন্ট>\nযেমন: /tdd email validation function with domain whitelist")
        return
    status_msg = await update.message.reply_text("TDD টেস্ট স্যুট ও কোড তৈরি করছি...")
    loop = asyncio.get_running_loop()
    res = await loop.run_in_executor(None, generate_tdd_suite, query)
    await safe_send_message(context.bot, chat_id=update.effective_chat.id, text=res)
    try:
        await status_msg.delete()
    except Exception:
        pass

async def handle_review_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles /review <code> command for code review and security audit."""
    if update.effective_user.id != ALLOWED_USER_ID: return
    query = " ".join(context.args).strip() if context.args else ""
    if not query:
        await update.message.reply_text("ব্যবহারের নিয়ম: /review <কোড স্নsnippet>\nযেমন: /review def login(u, p): ...")
        return
    status_msg = await update.message.reply_text("কোড রিভিউ ও সিকিউরিটি অডিট পরিচালনা করছি...")
    loop = asyncio.get_running_loop()
    res = await loop.run_in_executor(None, review_code_security, query)
    await safe_send_message(context.bot, chat_id=update.effective_chat.id, text=res)
    try:
        await status_msg.delete()
    except Exception:
        pass

async def handle_brainstorm_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles /brainstorm <idea> command for deep system architecture."""
    if update.effective_user.id != ALLOWED_USER_ID: return
    query = " ".join(context.args).strip() if context.args else ""
    if not query:
        await update.message.reply_text("ব্যবহারের নিয়ম: /brainstorm <প্রজেক্ট বা ফিচারের আইডিয়া>\nযেমন: /brainstorm AI-driven multi-tenant CRM with WhatsApp")
        return
    status_msg = await update.message.reply_text("সিস্টেম আর্কিটেকচার ও ব্রেনস্টর্মিং রিপোর্ট তৈরি করছি...")
    loop = asyncio.get_running_loop()
    res = await loop.run_in_executor(None, brainstorm_architecture, query)
    await safe_send_message(context.bot, chat_id=update.effective_chat.id, text=res)
    try:
        await status_msg.delete()
    except Exception:
        pass

async def handle_spec_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles /spec <feature_idea> command to generate formal Spec-Kit spec.md."""
    if update.effective_user.id != ALLOWED_USER_ID: return
    query = " ".join(context.args).strip() if context.args else ""
    if not query:
        await update.message.reply_text("ব্যবহারের নিয়ম: /spec <ফিচারের আইডিয়া>\nযেমন: /spec Real-time price tracking and notification engine")
        return
    status_msg = await update.message.reply_text("স্পেক-কিট স্পেসিফিকেশন ডকুমেন্ট (spec.md) তৈরি করছি...")
    loop = asyncio.get_running_loop()
    res = await loop.run_in_executor(None, generate_speckit_spec, query)
    await safe_send_message(context.bot, chat_id=update.effective_chat.id, text=res)
    try:
        await status_msg.delete()
    except Exception:
        pass

async def handle_plan_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles /plan <feature_or_spec> command to generate Spec-Kit plan.md."""
    if update.effective_user.id != ALLOWED_USER_ID: return
    query = " ".join(context.args).strip() if context.args else ""
    if not query:
        await update.message.reply_text("ব্যবহারের নিয়ম: /plan <ফিচার বা স্পেসিফিকেশন>\nযেমন: /plan Multi-threaded worker queue for video processing")
        return
    status_msg = await update.message.reply_text("স্পেক-কিট টেকনিক্যাল প্ল্যান (plan.md) তৈরি করছি...")
    loop = asyncio.get_running_loop()
    res = await loop.run_in_executor(None, generate_speckit_plan, query)
    await safe_send_message(context.bot, chat_id=update.effective_chat.id, text=res)
    try:
        await status_msg.delete()
    except Exception:
        pass

async def handle_tasks_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles /tasks <plan_or_feature> command to generate Spec-Kit tasks.md."""
    if update.effective_user.id != ALLOWED_USER_ID: return
    query = " ".join(context.args).strip() if context.args else ""
    if not query:
        await update.message.reply_text("ব্যবহারের নিয়ম: /tasks <প্ল্যান বা ফিচার>\nযেমন: /tasks User authentication and role-based access control")
        return
    status_msg = await update.message.reply_text("স্পেক-কিট টাস্ক চেকলিস্ট (tasks.md) তৈরি করছি...")
    loop = asyncio.get_running_loop()
    res = await loop.run_in_executor(None, generate_speckit_tasks, query)
    await safe_send_message(context.bot, chat_id=update.effective_chat.id, text=res)
    try:
        await status_msg.delete()
    except Exception:
        pass

# ==========================================
# NEWS DIGEST & INTERACTIVE CHECKBOX UI
# ==========================================

def build_news_keyboard(user_id: int, news_items: list) -> InlineKeyboardMarkup:
    """Builds a compact, clean 5-column checkbox grid for all news items plus a submit button."""
    selected_ids = USER_SELECTIONS.get(user_id, set())
    keyboard = []
    current_row = []
    
    bn_digits = str.maketrans('0123456789', '০১২৩৪৫৬৭৮৯')
    
    for idx, item in enumerate(news_items, start=1):
        nid = item["id"]
        is_selected = nid in selected_ids
        symbol = "[X]" if is_selected else "[ ]"
        bn_idx = str(idx).translate(bn_digits)
        btn_text = f"{symbol} {bn_idx}"
        current_row.append(InlineKeyboardButton(btn_text, callback_data=f"toggle:{nid}:{idx}"))
        
        if len(current_row) == 5:
            keyboard.append(current_row)
            current_row = []
            
    if current_row:
        keyboard.append(current_row)
        
    count = len(selected_ids)
    bn_count = str(count).translate(bn_digits)
    submit_text = f"নির্বাচিত নিউজের বিস্তারিত সামারি পড়ুন ({bn_count}টি সিলেক্টেড)" if count > 0 else "নির্বাচিত নিউজের বিস্তারিত সামারি পড়ুন (০টি সিলেক্টেড)"
    keyboard.append([InlineKeyboardButton(submit_text, callback_data="submit_news")])
    
    return InlineKeyboardMarkup(keyboard)

def is_daily_digest_sent(date_str: str) -> bool:
    """Checks whether the daily digest for date_str has already been dispatched."""
    try:
        conn = sqlite3.connect("memory.db")
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS daily_digest_log (digest_date TEXT PRIMARY KEY, sent_at TIMESTAMP)")
        cursor.execute("SELECT 1 FROM daily_digest_log WHERE digest_date = ?", (date_str,))
        row = cursor.fetchone()
        conn.close()
        return row is not None
    except Exception as e:
        logger.error(f"Error checking daily digest log: {e}")
        return False

def mark_daily_digest_sent(date_str: str) -> None:
    """Marks the daily digest for date_str as successfully dispatched in persistent storage."""
    try:
        conn = sqlite3.connect("memory.db")
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS daily_digest_log (digest_date TEXT PRIMARY KEY, sent_at TIMESTAMP)")
        now = datetime.datetime.now().isoformat()
        cursor.execute("INSERT OR REPLACE INTO daily_digest_log (digest_date, sent_at) VALUES (?, ?)", (date_str, now))
        conn.commit()
        conn.close()
        logger.info(f"Daily digest for {date_str} marked as sent in persistent storage.")
    except Exception as e:
        logger.error(f"Error marking daily digest log: {e}")

DIGEST_LOCK = asyncio.Lock()

async def check_and_dispatch_daily_digest(bot, force: bool = False) -> bool:
    """
    Automatic Routine Manager & Catch-up Dispatcher:
    Guarantees the agent NEVER forgets its regular 08:00 AM daily news and hackathons digest,
    even if the server was asleep, restarted, or busy with other tasks.
    Checks if today's digest has been dispatched; if current time >= 08:00 AM (Asia/Dhaka)
    and not yet sent today, immediately executes and dispatches it.
    """
    async with DIGEST_LOCK:
        try:
            try:
                dhaka_tz = ZoneInfo("Asia/Dhaka")
            except Exception:
                dhaka_tz = datetime.timezone(datetime.timedelta(hours=6))
                
            now_dhaka = datetime.datetime.now(dhaka_tz)
            today_date = now_dhaka.strftime("%Y-%m-%d")
            current_hour = now_dhaka.hour
            
            if not force and is_daily_digest_sent(today_date):
                return False
                
            if force or current_hour >= 8:
                logger.info(f"Routine Sentinel: Dispatching scheduled Daily AI News & Hackathons Digest for {today_date} (Hour: {current_hour})...")
                await send_daily_news_digest(bot, ALLOWED_USER_ID)
                return True
        except Exception as e:
            logger.error(f"Error in check_and_dispatch_daily_digest: {e}", exc_info=True)
            return False
    return False

async def send_daily_news_digest(bot, chat_id: int):
    """
    Dispatches the top 20 AI news in clean, readable Bengali cards with direct per-item
    interactive buttons, followed by the BD & Global Hackathons section.
    """
    logger.info("Starting Daily AI News & Hackathons Digest dispatch...")
    loop = asyncio.get_running_loop()
    
    # 1. Collect Top 20 Global AI News in background thread
    news_items = await loop.run_in_executor(None, collect_top_20_ai_news)
    today_str = get_current_date_str()
    
    # Reset user selection for the new day
    USER_SELECTIONS[chat_id] = set()
    
    if not news_items:
        await bot.send_message(chat_id=chat_id, text="[সতর্কবার্তা] আজকের এআই নিউজগুলো সংগ্রহ করতে সমস্যা হয়েছে। অনুগ্রহ করে কিছুক্ষণ পর আবার চেষ্টা করুন।")
        return

    # Header Message
    header_text = (
        f"<b>আজকের শীর্ষ ২০টি এআই ও ওপেন-সোর্স আপডেট</b>\n"
        f"<i>তারিখ: {today_str}</i>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"প্রতিটি নিউজের শিরোনাম পড়ার পর বিস্তারিত ১০-১৫ লাইনের গভীর বাংলা সারসংক্ষেপ ও রিসার্চ লিংক দেখতে সংশ্লিষ্ট নিউজের নিচের <b>[ [ ] বিস্তারিত পড়ুন ]</b> বক্সে ক্লিক করুন।"
    )
    await safe_send_message(bot, chat_id=chat_id, text=header_text)
    
    # Send each news item as an individual card with its own interactive button
    for idx, item in enumerate(news_items, start=1):
        nid = item["id"]
        t_bn = html.escape(item.get('title_bn') or item['title'])
        s_bn = html.escape(item.get('short_summary_bn') or '')
        
        card_text = f"<b>{idx}. {t_bn}</b>\n<i>{s_bn}</i>"
        card_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("[ ] বিস্তারিত পড়ুন", callback_data=f"expand:{nid}:{idx}")]
        ])
        
        await safe_send_message(
            bot,
            chat_id=chat_id,
            text=card_text,
            reply_markup=card_markup,
            disable_notification=True
        )
        await asyncio.sleep(0.15)
    
    # 2. Collect & Send BD & Global Remote Hackathons/Competitions in background thread
    events = await loop.run_in_executor(None, collect_hackathons_and_competitions)
    
    if events:
        events_text = (
            f"<b>চলমান এআই হ্যাকাথন ও প্রতিযোগিতা (বাংলাদেশ ও গ্লোবাল রিমোট)</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"<i>বাংলাদেশ থেকে ঘরে বসে অনলাইনে অথবা সরাসরি অংশ নেওয়ার শীর্ষ সুযোগসমূহ:</i>\n\n"
        )
        
        for idx, ev in enumerate(events, start=1):
            name_escaped = html.escape(ev['name'])
            org_escaped = html.escape(ev['organizer'])
            loc_escaped = html.escape(ev['location_type'])
            prize_escaped = html.escape(ev['prize_pool'])
            deadline_escaped = html.escape(ev['deadline'])
            
            events_text += (
                f"<b>{idx}. {name_escaped}</b>\n"
                f"   - <b>আয়োজক:</b> {org_escaped}\n"
                f"   - <b>ধরন:</b> {loc_escaped}\n"
                f"   - <b>পুরস্কার:</b> {prize_escaped}\n"
                f"   - <b>ডেডলাইন:</b> {deadline_escaped}\n"
                f"   - <a href=\"{ev['url']}\">অংশগ্রহণ / রেজিস্ট্রেশন লিংক</a>\n\n"
            )
            
        await safe_send_message(bot, chat_id=chat_id, text=events_text, disable_web_page_preview=True, disable_notification=True)
        
    mark_daily_digest_sent(today_str)
    logger.info(f"Daily digest for {today_str} dispatched and recorded successfully.")

async def handle_news_expand(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Expands a specific news card to show its 10-15 line deep summary and source link."""
    query = update.callback_query
    await query.answer()  # Silent acknowledgment: zero alert, zero toast, zero screen blur!
    
    data = query.data
    parts = data.split(":")
    nid = int(parts[1])
    idx = parts[2]
    
    # Provide immediate visual feedback on the button
    try:
        await query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("সারসংক্ষেপ লোড হচ্ছে...", callback_data="noop")]
            ])
        )
    except Exception:
        pass
        
    loop = asyncio.get_running_loop()
    res = await loop.run_in_executor(None, get_or_create_news_summary, nid)
    
    title = html.escape(res.get("title") or res.get("title_bn") or "নিউজ শিরোনাম")
    summary = html.escape(res.get("summary") or "সারসংক্ষেপ পাওয়া যায়নি।")
    url = res.get("url", "")
    
    expanded_text = (
        f"<b>{idx}. {title}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"<b>১০-১৫ লাইনের গভীর বাংলা সারসংক্ষেপ:</b>\n\n"
        f"{summary}"
    )
    
    buttons = []
    if url:
        buttons.append([InlineKeyboardButton("মূল ওয়েবসাইট / রিসার্চ পেপার পড়ুন", url=url)])
    buttons.append([InlineKeyboardButton("[X] সংক্ষেপ করুন", callback_data=f"collapse:{nid}:{idx}")])
    
    try:
        await query.edit_message_text(
            text=expanded_text,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(buttons),
            disable_web_page_preview=True
        )
    except Exception as e:
        if "Message is not modified" not in str(e):
            logger.error(f"Error expanding news card {nid}: {e}")

async def handle_news_collapse(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Collapses an expanded news card back to its headline and 1-2 line summary."""
    query = update.callback_query
    await query.answer()  # Zero toast, zero screen blur
    
    data = query.data
    parts = data.split(":")
    nid = int(parts[1])
    idx = parts[2]
    
    conn = sqlite3.connect("memory.db")
    cursor = conn.cursor()
    cursor.execute("SELECT title, title_bn, short_summary_bn FROM daily_news WHERE id = ?", (nid,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        t_bn = html.escape(row[1] or row[0])
        s_bn = html.escape(row[2] or "")
    else:
        t_bn = "নিউজ শিরোনাম"
        s_bn = ""
        
    collapsed_text = f"<b>{idx}. {t_bn}</b>\n<i>{s_bn}</i>"
    card_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("[ ] বিস্তারিত পড়ুন", callback_data=f"expand:{nid}:{idx}")]
    ])
    
    try:
        await query.edit_message_text(
            text=collapsed_text,
            parse_mode="HTML",
            reply_markup=card_markup
        )
    except Exception as e:
        if "Message is not modified" not in str(e):
            logger.error(f"Error collapsing news card {nid}: {e}")

async def handle_noop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Dummy handler for buttons in loading state."""
    query = update.callback_query
    await query.answer()

async def handle_news_toggle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handles real-time toggling of news checkboxes ([ ] <-> [X]).
    Maintains compatibility for any legacy messages.
    """
    query = update.callback_query
    data = query.data
    
    if not data.startswith("toggle:"):
        return
        
    parts = data.split(":")
    news_id = int(parts[1])
    idx_str = parts[2] if len(parts) > 2 else str(news_id)
    bn_digits = str.maketrans('0123456789', '০১২৩৪৫৬৭৮৯')
    bn_idx = idx_str.translate(bn_digits)
    
    user_id = update.effective_user.id
    if user_id not in USER_SELECTIONS:
        USER_SELECTIONS[user_id] = set()
        
    if news_id in USER_SELECTIONS[user_id]:
        USER_SELECTIONS[user_id].remove(news_id)
    else:
        USER_SELECTIONS[user_id].add(news_id)
        
    # Silent answer: zero toast alert popup to avoid screen blur
    await query.answer()
    
    current_markup = query.message.reply_markup
    if not current_markup:
        return
        
    new_keyboard = []
    selected_set = USER_SELECTIONS[user_id]
    
    for row in current_markup.inline_keyboard:
        new_row = []
        for btn in row:
            if btn.callback_data.startswith("toggle:"):
                btn_parts = btn.callback_data.split(":")
                btn_nid = int(btn_parts[1])
                b_idx = btn_parts[2] if len(btn_parts) > 2 else str(btn_nid)
                b_bn = b_idx.translate(bn_digits)
                
                symbol = "[X]" if btn_nid in selected_set else "[ ]"
                new_row.append(InlineKeyboardButton(f"{symbol} {b_bn}", callback_data=btn.callback_data))
            elif btn.callback_data == "submit_news":
                count = len(selected_set)
                bn_count = str(count).translate(bn_digits)
                submit_text = f"নির্বাচিত নিউজের বিস্তারিত সামারি পড়ুন ({bn_count}টি সিলেক্টেড)" if count > 0 else "নির্বাচিত নিউজের বিস্তারিত সামারি পড়ুন (০টি সিলেক্টেড)"
                new_row.append(InlineKeyboardButton(submit_text, callback_data="submit_news"))
            else:
                new_row.append(btn)
        new_keyboard.append(new_row)
        
    try:
        await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(new_keyboard))
    except Exception as e:
        if "Message is not modified" not in str(e):
            logger.error(f"Error editing reply markup: {e}", exc_info=True)

async def handle_news_submit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the submission of selected news items and dispatches 10-15 line summaries."""
    query = update.callback_query
    user_id = update.effective_user.id
    selected_ids = list(USER_SELECTIONS.get(user_id, set()))
    
    if not selected_ids:
        await query.answer("[সতর্কবার্তা] অনুগ্রহ করে প্রথমে অন্তত ১টি নিউজের বক্সে ক্লিক করুন।", show_alert=True)
        return
        
    await query.answer(f"{len(selected_ids)}টি নিউজের সামারি তৈরি হচ্ছে...")
    
    await context.bot.send_message(
        chat_id=user_id,
        text=f"আপনার নির্বাচিত <b>{len(selected_ids)}টি</b> নিউজের ১০-১৫ লাইনের গভীর বাংলা সামারি তৈরি হচ্ছে, দয়া করে একটু অপেক্ষা করুন...",
        parse_mode="HTML"
    )
    
    loop = asyncio.get_running_loop()
    for idx, nid in enumerate(selected_ids, start=1):
        res = await loop.run_in_executor(None, get_or_create_news_summary, nid)
        title = res.get("title", "নিউজ শিরোনাম")
        summary = res.get("summary", "সামারি পাওয়া যায়নি।")
        url = res.get("url", "")
        
        msg = (
            f"<b>[{idx}/{len(selected_ids)}] {html.escape(title)}</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"{html.escape(summary)}"
        )
        
        reply_markup = None
        if url:
            reply_markup = InlineKeyboardMarkup([
                [InlineKeyboardButton("মূল ওয়েবসাইট / রিসার্চ পেপার পড়ুন", url=url)]
            ])
            
        await safe_send_message(
            context.bot,
            chat_id=user_id,
            text=msg,
            reply_markup=reply_markup
        )
        
    # Clear user selection after dispatch
    USER_SELECTIONS[user_id] = set()

async def handle_read_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles direct reading of a specific news item via /read_<num> or /read <num>."""
    if update.effective_user.id != ALLOWED_USER_ID:
        return
        
    text = (update.message.text or "").strip()
    idx = None
    
    m = re.match(r"^/read_(\d+)$", text)
    if m:
        idx = int(m.group(1))
    elif context.args and len(context.args) > 0 and context.args[0].isdigit():
        idx = int(context.args[0])
    elif re.match(r"^/read\s+(\d+)$", text):
        m2 = re.match(r"^/read\s+(\d+)$", text)
        idx = int(m2.group(1))
        
    if idx is None:
        await update.message.reply_text("কোনো নিউজের বিস্তারিত পড়তে `/read_<নম্বর>` লিখুন, যেমন: `/read_1`")
        return
        
    # Fetch latest 20 items from database
    conn = sqlite3.connect("memory.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, title, title_bn, url 
        FROM daily_news 
        ORDER BY id DESC LIMIT 20
    """)
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        await update.message.reply_text("[তথ্য] ডাটাবেসে কোনো নিউজ পাওয়া যায়নি। প্রথমে `/news` দিন।")
        return
        
    sorted_items = list(reversed(rows))
    if idx < 1 or idx > len(sorted_items):
        await update.message.reply_text(f"[সতর্কবার্তা] {idx} নম্বরের কোনো নিউজ পাওয়া যায়নি। অনুগ্রহ করে ১ থেকে {len(sorted_items)} এর মধ্যে নম্বর দিন।")
        return
        
    item = sorted_items[idx - 1]
    nid = item[0]
    
    bn_digits = str.maketrans('0123456789', '০১২৩৪৫৬৭৮৯')
    bn_idx = str(idx).translate(bn_digits)
    
    status_msg = await update.message.reply_text(f"<b>{bn_idx} নম্বর</b> নিউজের ১০-১৫ লাইনের গভীর বাংলা সামারি তৈরি হচ্ছে...", parse_mode="HTML")
    loop = asyncio.get_running_loop()
    res = await loop.run_in_executor(None, get_or_create_news_summary, nid)
    title = res.get("title", item[2] or item[1])
    summary = res.get("summary", "সামারি পাওয়া যায়নি।")
    url = res.get("url", item[3])
    
    msg = (
        f"<b>[{bn_idx}/{len(sorted_items)}] {html.escape(title)}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"{html.escape(summary)}"
    )
    
    reply_markup = None
    if url:
        reply_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("মূল ওয়েবসাইট / রিসার্চ পেপার পড়ুন", url=url)]
        ])
        
    await safe_send_message(
        context.bot,
        chat_id=update.effective_chat.id,
        text=msg,
        reply_markup=reply_markup
    )
    try:
        await status_msg.delete()
    except Exception:
        pass

async def news_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Manual trigger command `/news` for testing and on-demand digest."""
    if update.effective_user.id != ALLOWED_USER_ID:
        logger.warning(f"Unauthorized access attempt by {update.effective_user.id}")
        return
        
    try:
        status_msg = await update.message.reply_text("আজকের টপ ২০টি এআই নিউজ ও হ্যাকাথন সংগ্রহ করছি... অনুগ্রহ করে কয়েক সেকেন্ড অপেক্ষা করুন।")
        await send_daily_news_digest(context.bot, update.effective_chat.id)
        try:
            await status_msg.delete()
        except Exception:
            pass
    except Exception as e:
        logger.error(f"Error in news_command: {e}", exc_info=True)
        await update.message.reply_text(f"[ত্রুটি] নিউজ লোড করতে সাময়িক সমস্যা হয়েছে: {e}")

# ==========================================
# BACKGROUND SCHEDULERS
# ==========================================

async def check_reminders(context: ContextTypes.DEFAULT_TYPE):
    """Background Job: Checks database for pending reminders and guarantees daily news digest delivery."""
    # 1. Routine Sentinel: Catch-up check for 08:00 AM Daily AI News & Hackathons Digest
    try:
        await check_and_dispatch_daily_digest(context.bot)
    except Exception as e:
        logger.error(f"Daily Digest Sentinel Error: {e}")

    try:
        conn = sqlite3.connect("memory.db")
        cursor = conn.cursor()
        now = datetime.datetime.now()
        
        cursor.execute("SELECT id, message FROM reminders WHERE is_sent=0 AND remind_at <= ?", (now,))
        due_reminders = cursor.fetchall()
        
        for row in due_reminders:
            rem_id, msg = row
            await context.bot.send_message(chat_id=ALLOWED_USER_ID, text=f"**রিমাইন্ডার:**\n{msg}")
            cursor.execute("UPDATE reminders SET is_sent=1 WHERE id=?", (rem_id,))
        
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Reminder System Error: {e}")

async def scheduled_daily_news_job(context: ContextTypes.DEFAULT_TYPE):
    """Daily 08:00 AM BST Job for sending news."""
    try:
        await check_and_dispatch_daily_digest(context.bot, force=True)
    except Exception as e:
        logger.error(f"Daily News Scheduled Job Error: {e}")

# ==========================================
# CLOUD HEALTH SERVER
# ==========================================

import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/trigger-news":
            global APP_INSTANCE, APP_LOOP
            if APP_INSTANCE and APP_LOOP:
                import asyncio
                asyncio.run_coroutine_threadsafe(
                    check_and_dispatch_daily_digest(APP_INSTANCE.bot, force=True),
                    APP_LOOP
                )
                body = b"OK - Daily AI News Digest triggered successfully."
            else:
                body = b"Bot application initializing. Please retry in a few seconds."
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Connection", "close")
            self.end_headers()
            self.wfile.write(body)
            return

        body = b"OK"
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(body)

    def do_HEAD(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", "2")
        self.send_header("Connection", "close")
        self.end_headers()

    def log_message(self, format, *args):
        pass # Suppress noisy healthcheck logs
        
def run_dummy_server():
    port = int(os.getenv("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
    server.serve_forever()

async def post_init_handler(application: Application) -> None:
    """Stores the active event loop and app instance for webhook / trigger endpoints."""
    global APP_INSTANCE, APP_LOOP
    import asyncio
    APP_INSTANCE = application
    APP_LOOP = asyncio.get_running_loop()
    logger.info("Application loop and instance registered for external triggers.")
    
    # Startup Sentinel Catch-up:
    # If the bot starts up or wakes up after 08:00 AM (BST) and today's news wasn't sent, dispatch immediately!
    asyncio.create_task(check_and_dispatch_daily_digest(application.bot))

def main() -> None:
    # 1. Start dummy server for Cloud Health Checks
    threading.Thread(target=run_dummy_server, daemon=True).start()
    
    # 2. Build Telegram Application with post_init
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).post_init(post_init_handler).build()
    
    # 3. Add Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("news", news_command))
    application.add_handler(CommandHandler("read", handle_read_command))
    application.add_handler(CommandHandler("yt", handle_youtube_command))
    application.add_handler(CommandHandler("post", handle_post_command))
    application.add_handler(CommandHandler("trending", handle_trending_command))
    application.add_handler(CommandHandler("github", handle_trending_command))
    
    # Superpowers Handlers
    application.add_handler(CommandHandler("debug", handle_debug_command))
    application.add_handler(CommandHandler("tdd", handle_tdd_command))
    application.add_handler(CommandHandler("review", handle_review_command))
    application.add_handler(CommandHandler("brainstorm", handle_brainstorm_command))
    
    # Spec-Kit Handlers
    application.add_handler(CommandHandler("spec", handle_spec_command))
    application.add_handler(CommandHandler("plan", handle_plan_command))
    application.add_handler(CommandHandler("tasks", handle_tasks_command))
    
    application.add_handler(MessageHandler(filters.Regex(r"^/read_\d+$"), handle_read_command))
    application.add_handler(CallbackQueryHandler(handle_news_expand, pattern=r"^expand:"))
    application.add_handler(CallbackQueryHandler(handle_news_collapse, pattern=r"^collapse:"))
    application.add_handler(CallbackQueryHandler(handle_noop, pattern=r"^noop$"))
    application.add_handler(CallbackQueryHandler(handle_news_toggle, pattern=r"^toggle:"))
    application.add_handler(CallbackQueryHandler(handle_news_submit, pattern=r"^submit_news$"))
    application.add_handler(MessageHandler(filters.PHOTO | filters.Document.IMAGE, handle_photo))
    application.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, handle_voice))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # 4. Job Queue: Reminders every 30 seconds
    application.job_queue.run_repeating(check_reminders, interval=30, first=10)
    
    # 5. Job Queue: Daily 08:00 AM (Asia/Dhaka) News Digest
    try:
        dhaka_tz = ZoneInfo("Asia/Dhaka")
    except Exception:
        dhaka_tz = datetime.timezone(datetime.timedelta(hours=6))
        
    daily_time = datetime.time(hour=8, minute=0, tzinfo=dhaka_tz)
    application.job_queue.run_daily(scheduled_daily_news_job, time=daily_time)
    
    logger.info(f"24/7 Agent is online with Daily AI News scheduled at {daily_time} (Asia/Dhaka)...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
