from ddgs import DDGS
import ollama
from datetime import datetime

# ==========================================
# CONFIGURATION
# ==========================================

MODEL = "qwen2.5:1.5b"
MAX_RESULTS = 8

LOCAL_SYSTEM_PROMPT = """
You are ReshLLM, a helpful and intelligent AI assistant.

Your responsibilities:

1. Answer Python programming questions accurately.
2. Explain code step by step when needed.
3. Find and correct programming errors.
4. Follow every restriction given by the user.
5. Give efficient solutions and explain time complexity.
6. Answer general knowledge questions clearly.
7. Never invent Python functions or libraries.
8. If you are unsure, admit it.
9. Use simple English and properly formatted code.
"""

# ==========================================
# STEP 1: DATE AND TIME
# ==========================================

DATE_KEYWORDS = [
    "today's date",
    "todays date",
    "current date",
    "what day is it",
    "today's day",
    "current time",
    "what is the time",
    "what time is it"
]


def get_date_response(question):
    """
    Returns a formatted date/time string if the question matches date keywords,
    or None if it does not.
    """
    q = question.lower()
    if any(word in q for word in DATE_KEYWORDS):
        now = datetime.now()
        date_str = now.strftime("%d %B %Y")
        day_str = now.strftime("%A")
        time_str = now.strftime("%I:%M %p")
        return f"**Date:** {date_str}  \n**Day:** {day_str}  \n**Time:** {time_str}"
    return None


def handle_date(question):
    """
    CLI handler for date/time. Prints directly to console and returns True if handled.
    """
    q = question.lower()
    if any(word in q for word in DATE_KEYWORDS):
        now = datetime.now()
        print("\nReshLLM:")
        print("Date:", now.strftime("%d %B %Y"))
        print("Day:", now.strftime("%A"))
        print("Time:", now.strftime("%I:%M %p"))
        return True
    return False


# ==========================================
# STEP 2: DETECT QUESTION TYPE
# ==========================================

WEB_KEYWORDS = [
    "latest",
    "recent",
    "currently",
    "current affairs",
    "today",
    "yesterday",
    "this week",
    "this month",
    "breaking",
    "news",
    "2026",
    "2025",
    "right now",
    "as of now",
    "latest version",
    "recent developments",
    "current price",
    "stock market",
    "who is the current",
    "who won",
    "latest update"
]

NEWS_KEYWORDS = [
    "news",
    "current affairs",
    "breaking news",
    "headlines",
    "major events",
    "top stories",
    "latest developments in india",
    "latest developments around the world"
]


def needs_web_search(question):
    q = question.lower()
    return any(word in q for word in WEB_KEYWORDS)


def is_news_question(question):
    q = question.lower()
    return any(word in q for word in NEWS_KEYWORDS)


# ==========================================
# STEP 3: INTERNET SEARCH
# ==========================================

def search_web(query, search_type="text"):
    """
    Searches the web using DDGS with region support and fallback.
    """
    try:
        ddgs = DDGS()
        results = None

        if search_type == "news":
            try:
                results = ddgs.news(
                    query,
                    region="in-en",
                    safesearch="moderate",
                    timelimit="d",
                    max_results=MAX_RESULTS
                )
            except Exception:
                results = None

            # If today's results are insufficient, search past week
            if not results or len(results) < 3:
                try:
                    results = ddgs.news(
                        query,
                        region="in-en",
                        safesearch="moderate",
                        timelimit="w",
                        max_results=MAX_RESULTS
                    )
                except Exception:
                    # Fallback to general news without region restriction
                    results = ddgs.news(
                        query,
                        safesearch="moderate",
                        max_results=MAX_RESULTS
                    )
        else:
            try:
                results = ddgs.text(
                    query,
                    region="in-en",
                    safesearch="moderate",
                    max_results=MAX_RESULTS
                )
            except Exception:
                # Fallback to text search without region
                results = ddgs.text(
                    query,
                    safesearch="moderate",
                    max_results=MAX_RESULTS
                )

        if not results:
            return []

        search_data = []
        for item in results:
            search_data.append({
                "title": item.get("title", ""),
                "date": item.get("date", ""),
                "source": item.get("source", ""),
                "url": item.get("url", ""),
                "description": item.get(
                    "body",
                    item.get("description", "")
                )
            })

        return search_data

    except Exception as error:
        print("Search error:", error)
        return []


# ==========================================
# STEP 4: PREPARE SEARCH RESULTS
# ==========================================

def prepare_context(results):
    context = ""
    for i, item in enumerate(results, 1):
        context += f"""
RESULT {i}

Title: {item['title']}
Date: {item['date']}
Source: {item['source']}
URL: {item['url']}
Information: {item['description']}

--------------------------------
"""
    return context


def build_web_prompt(question, context):
    current_date = datetime.now().strftime("%d %B %Y")
    prompt = f"""
You are an AI research assistant with access to live search results.

Today's date: {current_date}

USER QUESTION:
{question}

SEARCH RESULTS:
{context}

IMPORTANT RULES:

1. Answer the user's actual question.
2. Use the provided search results as your evidence.
3. Do not invent facts, people, dates, statistics or events.
4. Distinguish between old information and recent information.
5. Prefer recent and relevant sources.
6. Do not treat search result publication dates as event dates.
7. If sources disagree, mention the disagreement.
8. If information is insufficient, clearly say so.
9. Include source names and original URLs.
10. Do not claim that you verified the full article when
    only its search-result description is available.

For news questions:
- Select the most relevant news stories.
- Prioritize major Indian developments.
- Do not include unrelated international business news
  unless it has significant relevance to India.
- Give fewer stories rather than inventing five.

For other questions:
- Answer directly.
- Explain important facts clearly.
- Include sources for factual claims.

Write a clear, well-organized answer.
"""
    return prompt


# ==========================================
# STEP 5: STREAMING GENERATORS (FOR WEB UI)
# ==========================================

def stream_local_ai(question, system_prompt=None, temperature=0.2, num_predict=700):
    """
    Generator yielding streamed text tokens from Ollama for local AI responses.
    """
    sys_prompt = system_prompt or LOCAL_SYSTEM_PROMPT
    response_stream = ollama.chat(
        model=MODEL,
        messages=[
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": question}
        ],
        stream=True,
        options={
            "temperature": temperature,
            "num_predict": num_predict
        }
    )
    for chunk in response_stream:
        content = chunk.get("message", {}).get("content", "")
        if content:
            yield content


def stream_web_ai(question, context, temperature=0.1, num_predict=800):
    """
    Generator yielding streamed text tokens from Ollama with web context.
    """
    prompt = build_web_prompt(question, context)
    response_stream = ollama.chat(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a factual research assistant. "
                    "Never fabricate information."
                )
            },
            {"role": "user", "content": prompt}
        ],
        stream=True,
        options={
            "temperature": temperature,
            "num_predict": num_predict
        }
    )
    for chunk in response_stream:
        content = chunk.get("message", {}).get("content", "")
        if content:
            yield content


def prepare_pipeline(question, search_mode="auto", temperature=0.2, num_predict=700):
    """
    High-level orchestrator for frontend integration.
    Analyzes question and returns a cleanly structured dictionary:
    {
        "type": "date" | "search" | "local" | "error",
        "direct_response": str or None,
        "search_query": str or None,
        "sources": list of dicts,
        "stream": generator yielding tokens or None,
        "error": str or None
    }
    """
    # 1. Deterministic date/time query
    date_resp = get_date_response(question)
    if date_resp:
        return {
            "type": "date",
            "direct_response": date_resp,
            "search_query": None,
            "sources": [],
            "stream": None,
            "error": None
        }

    # 2. Decide search requirement
    should_search = False
    if search_mode == "always":
        should_search = True
    elif search_mode == "offline":
        should_search = False
    else:  # auto
        should_search = needs_web_search(question)

    if should_search:
        news_mode = is_news_question(question)
        if news_mode:
            search_query = (
                "India major news headlines current affairs today "
                + datetime.now().strftime("%d %B %Y")
            )
            search_type = "news"
        else:
            search_query = question
            search_type = "text"

        results = search_web(search_query, search_type)

        if not results:
            # Fallback to local AI with notice
            notice = "_Note: Live web search did not return results. Answering from local knowledge._\n\n"
            def fallback_stream():
                yield notice
                for token in stream_local_ai(question, temperature=temperature, num_predict=num_predict):
                    yield token

            return {
                "type": "local",
                "direct_response": None,
                "search_query": search_query,
                "sources": [],
                "stream": fallback_stream(),
                "error": None
            }

        context = prepare_context(results)
        return {
            "type": "search",
            "direct_response": None,
            "search_query": search_query,
            "sources": results,
            "stream": stream_web_ai(question, context, temperature=0.1, num_predict=max(num_predict, 800)),
            "error": None
        }

    # 3. Local AI query
    return {
        "type": "local",
        "direct_response": None,
        "search_query": None,
        "sources": [],
        "stream": stream_local_ai(question, temperature=temperature, num_predict=num_predict),
        "error": None
    }


# ==========================================
# STEP 6: CLI COMPATIBILITY METHODS
# ==========================================

def ask_local_ai(question):
    print("\nUsing local AI model...")
    try:
        response = ollama.chat(
            model=MODEL,
            messages=[
                {"role": "system", "content": LOCAL_SYSTEM_PROMPT},
                {"role": "user", "content": question}
            ],
            options={
                "temperature": 0.2,
                "num_predict": 700
            }
        )
        print("\nReshLLM:")
        print(response["message"]["content"])
    except Exception as error:
        print("AI generation error:", error)


def ask_web_ai(question):
    news_mode = is_news_question(question)
    if news_mode:
        search_query = (
            "India major news headlines current affairs today "
            + datetime.now().strftime("%d %B %Y")
        )
        search_type = "news"
    else:
        search_query = question
        search_type = "text"

    print("\nSearching the internet...")
    results = search_web(search_query, search_type)

    if not results:
        print("\nNo search results could be retrieved.")
        print("Please check your internet connection or try again.")
        return

    context = prepare_context(results)
    prompt = build_web_prompt(question, context)

    print("\nAnalyzing live search results...")

    try:
        response = ollama.chat(
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a factual research assistant. "
                        "Never fabricate information."
                    )
                },
                {"role": "user", "content": prompt}
            ],
            options={
                "temperature": 0.1,
                "num_predict": 800
            }
        )
        print("\nReshLLM:")
        print(response["message"]["content"])
    except Exception as error:
        print("AI generation error:", error)


def ask_ai(question):
    # First: deterministic date and time
    if handle_date(question):
        return

    # Second: decide whether internet is necessary
    if needs_web_search(question):
        ask_web_ai(question)
    else:
        ask_local_ai(question)


# ==========================================
# STEP 7: MAIN CLI APPLICATION LOOP
# ==========================================

if __name__ == "__main__":
    print("========================================")
    print("                RESHLLM")
    print("========================================")

    print("Model:", MODEL)
    print("Local AI: Enabled")
    print("Live Web Search: Enabled")
    print("Live News Search: Enabled")

    print("----------------------------------------")
    print("Python | Programming | General Knowledge")
    print("Current Affairs | Live Information")
    print("----------------------------------------")

    print("Type 'exit' to close.")

    print("========================================")

    while True:
        try:
            question = input("\nYou: ").strip()

            if question.lower() in ["exit", "quit"]:
                print("\nGoodbye!")
                break

            if not question:
                continue

            ask_ai(question)

        except KeyboardInterrupt:
            print("\n\nAssistant closed.")
            break

        except Exception as error:
            print("\nUnexpected error:", error)
