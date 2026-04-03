from playwright.sync_api import sync_playwright
import logging

# 🔥 LLM IMPORTS
from groq import Groq
import os
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))


logging.basicConfig(
    filename="playwright.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


# ---------------------------------------------
# Selector Map (fallback only)
# ---------------------------------------------

selector_map = {
    "username field": 'input[name="username"]',
    "password field": 'input[name="password"]',
    "login button": 'button[type="submit"]',
}

# ---------------------------------------------
# URL Handler
# ---------------------------------------------

def get_url(target):

    if not target:
        raise Exception("Empty target")

    target = target.lower().strip()

    if target.startswith("http"):
        return target

    target = target.replace("website", "").strip()
    domain = target.replace(" ", "")

    return f"https://www.{domain}.com"

# ---------------------------------------------
# INPUT SCORING
# ---------------------------------------------

def score_input(element, target):

    score = 0

    try:
        name = (element.get_attribute("name") or "").lower()
        placeholder = (element.get_attribute("placeholder") or "").lower()
        type_attr = (element.get_attribute("type") or "").lower()
        element_id = (element.get_attribute("id") or "").lower()
    except:
        return 0

    # 🔥 CLEAN TARGET
    target = target.lower()

# 🔥 REMOVE COMMON UI WORDS
    target = target.replace("field", "")
    target = target.replace("input", "")
    target = target.replace("textbox", "")
    target = target.replace("bar", "")   # ✅ ADD THIS
    target = target.replace("box", "")   # ✅ ADD THIS

    target = target.strip()

    # 🔥 EXACT MATCH
    if target == name or target == element_id:
        score += 5

    # 🔥 PARTIAL MATCH
    if target in name or target in element_id:
        score += 3
    # 🔥 HIGH PRIORITY: common fields
    if target in ["search", "email", "username"]:
        if target in name or target in element_id:
            score += 2

    if target == placeholder:
        score += 5
    elif target in placeholder:
        score += 3

    # 🔥 PASSWORD BOOST
    if "password" in target and type_attr == "password":
        score += 4

    # 🔥 GENERAL INPUT BOOST
    if type_attr in ["text", "email"]:
        score += 1

    return score

# ---------------------------------------------
# SMART INPUT WITH SCORING
# ---------------------------------------------

def smart_find_input(page, target):

    inputs = page.locator("input")
    count = inputs.count()

    best_element = None
    best_score = -1

    for i in range(count):
        el = inputs.nth(i)

        s = score_input(el, target)

        if s > best_score:
            best_score = s
            best_element = el

    # 🔥 Add threshold (IMPORTANT)
    if best_score >= 3:
        return best_element

    # 🔥 fallback for search
    if "search" in target:
        return page.locator("input[type='text']")

    print(f"Best score for '{target}': {best_score}")
    return None
# ---------------------------------------------
# BUTTON SCORING
# ---------------------------------------------

def normalize(text):
    return text.replace(" ", "").lower()

def score_button(element, target):

    score = 0

    try:
        text = normalize(element.inner_text() or "")
    except:
        text = ""

    target = normalize(target.replace("button", ""))

    if target == text:
        score += 5

    if target in text:
        score += 3

    return score
# ---------------------------------------------
# SMART BUTTON WITH SCORING
# ---------------------------------------------

def smart_find_button(page, target):

    def normalize(text):
        return text.replace(" ", "").lower()

    target = normalize(target.replace("button", ""))

    buttons = page.locator("button, input[type='submit']")
    count = buttons.count()

    best_element = None
    best_score = -1

    for i in range(count):
        btn = buttons.nth(i)

        try:
            text = normalize(btn.inner_text() or btn.text_content() or "")
        except:
            text = ""

        score = 0

        if target == text:
            score += 5

        if target in text:
            score += 3

        if score > best_score:
            best_score = score
            best_element = btn

    # 🔥 IMPORTANT: only return if GOOD match
    if best_score >= 3:
        return best_element

    return None
# ---------------------------------------------
# 🔥 LLM SELECTOR (LAST FALLBACK)
# ---------------------------------------------
# ---------------------------------------------
# 🔥 CLEAN LLM SELECTOR OUTPUT
# ---------------------------------------------
def clean_selector(selector: str):
    if not selector:
        return selector

    # take only first line
    selector = selector.strip().split("\n")[0]

    # remove explanation text after space
    selector = selector.split(" ")[0] if " " in selector else selector

    return selector.strip()
def llm_find_selector(page, target, action):

    try:
        html = page.content()

        prompt = f"""
You are an expert in web automation.

Find the best CSS selector for this action:

Action: {action}
Target: {target}

HTML:
{html[:5000]}

Rules:
- Return ONLY a valid CSS selector
- Prefer id, name, placeholder, or unique attributes
- If input → return input selector
- If button → return button selector

Output ONLY selector string.
"""

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            temperature=0,
            messages=[
                {"role": "system", "content": "Return only selector."},
                {"role": "user", "content": prompt}
            ]
        )

        selector = response.choices[0].message.content.strip()
        selector = clean_selector(selector)

        print(f"\n🔥 LLM USED → selector: {selector}\n")
        logging.info(f"LLM selector: {selector}")

        return selector

    except Exception as e:
        logging.error(f"LLM selector failed: {str(e)}")
        return None

# ---------------------------------------------
# MAIN SELECTOR ENGINE
# ---------------------------------------------
# ---------------------------------------------
# 🔥 SPECIAL TARGET HANDLER (FIRST / LIST ITEMS)
# ---------------------------------------------
def handle_special_targets(page, target):

    target = target.lower()

    # 🎯 YouTube first video
    if "first video" in target:
        return page.locator("ytd-video-renderer").first.locator("a#thumbnail")

    # 🎯 generic first result
    if "first result" in target:
        return page.locator("a").first

    return None
def get_selector(page, target, action):

    target = target.strip().lower()

    # 1️⃣ INPUT
    if action in ["type", "enter"]:
        el = smart_find_input(page, target)
        if el:
            return el

    # 2️⃣ BUTTON
    if action in ["click", "assert", "verify"]:
        el = smart_find_button(page, target)
        if el:
            return el
    # 3️⃣ MAPPING
    selector = selector_map.get(target)
    if selector:
        return page.locator(selector)
    
    # 3.5️⃣ 🔥 SPECIAL TARGETS (NEW)
    special = handle_special_targets(page, target)
    if special:
        return special
    # 3.7️⃣ 🔥 YOUTUBE SEARCH FIX (ADD HERE)
    if "search" in target:
        try:
            return page.locator("input#search")
        except:
            pass
    
    # 4️⃣ 🔥 LLM FALLBACK
    llm_selector = llm_find_selector(page, target, action)
    if llm_selector:
        try:
            return page.locator(llm_selector)
        except:
            pass

    # 5️⃣ FINAL FALLBACK
    raise Exception(f"Element not found by any strategy: {target}")

# ---------------------------------------------
# EXECUTION ENGINE
# ---------------------------------------------

def execute_steps(page, steps):

    for step in steps:

        action = step.get("action")
        target = step.get("target")
        value = step.get("value")

        logging.info(f"Executing: {action} | {target} | {value}")

        try:

            if action == "open":

                url = get_url(target)
                page.goto(url, wait_until="domcontentloaded", timeout=60000)
                page.wait_for_load_state("networkidle")

            elif action in ["type", "enter"]:

                selector = get_selector(page, target, action)

                selector.wait_for(state="visible", timeout=10000)
                selector.click()
                page.wait_for_timeout(300)

                selector.fill(value or "")

            elif action == "click":

                selector = get_selector(page, target, action)

                selector.wait_for(state="visible", timeout=10000)
                selector.click()

            elif action == "submit":

                page.keyboard.press("Enter")

            elif action == "wait":

                page.wait_for_timeout(2000)

            elif action == "scroll":

                page.mouse.wheel(0, 1000)

            elif action == "verify":

                selector = get_selector(page, target, action)

                # 🔥 HARD CHECK
                if selector.count() == 0:
                    raise Exception(f"Verify Failed: Element not found: {target}")

                selector.wait_for(state="visible", timeout=5000)

                if value and value.lower() == "visible":
                    logging.info(f"Verify passed: {target} is visible")

                elif value:
                    actual_text = selector.inner_text()

                    if value.lower() not in actual_text.lower():
                        raise Exception(
                            f"Verify Failed: '{value}' not found in '{actual_text}'"
                        )

                else:
                    logging.info(f"Verify passed: {target} exists")
            elif action == "assert":

                selector = get_selector(page, target, action)
                if selector.count() == 0:
                    raise Exception(f"Assertion Failed: Element not found: {target}")

                # Always wait for element
                selector.wait_for(state="visible", timeout=10000)

                # 🔥 CASE 1: visibility check
                if value and value.lower() == "visible":
                    logging.info(f"Assertion passed: {target} is visible")

                # 🔥 CASE 2: text check
                elif value:
                    actual_text = selector.inner_text()

                    if value.lower() not in actual_text.lower():
                        raise Exception(
                            f"Assertion Failed: Expected '{value}' in '{actual_text}'"
                        )

                # 🔥 CASE 3: no value → just existence
                else:
                    logging.info(f"Assertion passed: {target} exists")

            elif action == "assert_url":

                current_url = page.url

                if value not in current_url:
                    raise Exception(
                        f"URL Assertion Failed: Expected '{value}' in '{current_url}'"
                    )


            else:

                logging.warning(f"Unsupported action: {action}")

        except Exception as e:

            logging.error(f"Step failed: {action} → {str(e)}")
            raise

# ---------------------------------------------
# MAIN EXECUTOR
# ---------------------------------------------

def run_playwright_test(parsed_output):

    try:

        with sync_playwright() as p:

            browser = p.chromium.launch(headless=False)
            page = browser.new_page()

            intent = parsed_output.get("intent")

            if intent == "simple":
                execute_steps(page, parsed_output.get("steps", []))

            elif intent == "loop":
                loop_data = parsed_output.get("loop", {})
                for _ in range(loop_data.get("count", 1)):
                    execute_steps(page, loop_data.get("steps", []))

            elif intent == "conditional":
                cond_data = parsed_output.get("conditional", {})
                execute_steps(page, cond_data.get("steps", []))

            page.wait_for_timeout(8000)
            browser.close()

            return {
                "status": "success",
                "message": "Test executed successfully"
            }

    except Exception as e:

        return {
            "status": "failed",
            "error": str(e)
        }