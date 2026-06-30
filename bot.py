from playwright.sync_api import sync_playwright
from dotenv import load_dotenv
import os
import datetime
import os

print("Current working directory:", os.getcwd())
print("Script directory:", os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

EMAIL = os.getenv("HOYO_EMAIL")
PASSWORD = os.getenv("HOYO_PASSWORD")
LAST_RUN_FILE = "last_run.txt"

GAMES = {
    "HSR": {
        "url": "https://act.hoyolab.com/bbs/event/signin/hkrpg/index.html?act_id=e202303301540311",
        "day_selector": '[class*="prize-list_---no"]',
        "claimable_color": "0, 0, 0",
    },
    "ZZZ": {
        "url": "https://act.hoyolab.com/bbs/event/signin/zzz/e202406031448091.html?act_id=e202406031448091",
        "day_selector": '[class*="prize-list_---cnt"]',
        "claimable_color": "254, 254, 254",
    }
}

STATE_FILE = "state.json"

def already_ran_today():
    today = datetime.date.today().isoformat()

    if os.path.exists(LAST_RUN_FILE):
        with open(LAST_RUN_FILE, "r") as f:
            last_run = f.read().strip()
        return last_run == today

    return False

def mark_run_done():
    today = datetime.date.today().isoformat()
    with open(LAST_RUN_FILE, "w") as f:
        f.write(today)

def close_popups(page):
    """Try to close popup/overlay that might block interaction."""
    try:
        el = page.locator('[class*="dialog-close"]').first

        if el.is_visible(timeout=1000):
            el.click()
            print("Closed popup")
            page.wait_for_timeout(500)
            return True
        
    except Exception:
        pass
    return False


def is_logged_in(page):
    """
    Check login status by inspecting the avatar image src.
    - Not logged in: src is a base64 data URI (default placeholder icon)
    - Logged in: src is a URL from hoyolab CDN (actual user avatar)
    Returns True if logged in.
    """
    try:
        avatar_img = page.locator('.mhy-hoyolab-account-block__avatar-icon')
        if avatar_img.count() > 0 and avatar_img.first.is_visible(timeout=2000):
            src = avatar_img.first.get_attribute("src")
            if src and not src.startswith("data:image"):
                print(f"Logged in (avatar URL detected)")
                return True
            else:
                print("Not logged in (default avatar)")
                return False
    except Exception as e:
        print(f"Login check error: {e}")
    return False


def fill_login_form(page, email, password):
    """
    Attempt to fill login form with iframe.
    Returns True if login was successful.
    """

    # Check if already logged in via avatar image
    if is_logged_in(page):
        return True

    clicked = False
    try:
        el = page.locator(".mhy-hoyolab-account-block__avatar").first
        if el.is_visible(timeout=5000):
            el.click(force=True)
            print(f"Clicked login entry")
            clicked = True
    except Exception:
        pass

    if not clicked:
        print("Could not find login entry button")
        return False

    page.wait_for_timeout(5000)

    # Check for iframe
    iframes = page.frames
    for frame in iframes:
        try:
            username_input = frame.locator('input[name="username"]')
            if username_input.count() > 0:
                print(f"Found login form in iframe: {frame.url}")
                username_input.wait_for(state="visible", timeout=5000)
                username_input.click()
                page.wait_for_timeout(500)
                username_input.type(email, delay=120)

                password_input = frame.locator('input[name="password"]')
                password_input.wait_for(state="visible", timeout=5000)
                password_input.click()
                page.wait_for_timeout(500)
                password_input.type(password, delay=120)

                print("Credentials filled")

                # Find and click submit
                login_button = frame.locator('button[type="submit"]')
                login_button.wait_for(state="visible", timeout=5000)
                login_button.click(force=True)

                print("Login submitted")
                break
        except Exception:
            continue

    # Wait for login to complete
    page.wait_for_timeout(5000)
    page.wait_for_load_state("networkidle", timeout=30000)

    # Verify login via avatar image
    if is_logged_in(page):
        print("Login verified successfully")
        return True

    # If we get here, login might have failed or there's a CAPTCHA
    print("WARNING: Login status uncertain - check for CAPTCHA or phone verification")
    return False

def claim_daily_reward(page, game):
    config = GAMES[game]

    page.wait_for_timeout(3000)

    day_items = page.locator('[class*="prize-list_---item"]')

    print(f"{game}: Found {day_items.count()} day items")

    for i in range(day_items.count()):
        item = day_items.nth(i)

        label = item.locator(config["day_selector"])

        if label.count() == 0:
            continue

        color = label.evaluate(
            "el => window.getComputedStyle(el).color"
        )

        if config["claimable_color"] in color:
            print(f"{game}: Claiming reward...")
            item.click(force=True)
            page.wait_for_timeout(2000)
            return True

    print(f"{game}: Nothing to claim")
    return False

def run_game(page, game):
    config = GAMES[game]

    print(f"\n===== {game} =====")

    page.goto(config["url"], wait_until="domcontentloaded")

    page.wait_for_timeout(5000)

    close_popups(page)

    if fill_login_form(page, EMAIL, PASSWORD):
        claim_daily_reward(page, game)

if already_ran_today():
    print("Already ran today. Exiting...")
    exit()

with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=True
    )

    # Load saved session if available
    if os.path.exists(STATE_FILE):
        print("Loading saved session...")
        try:
            context = browser.new_context(storage_state=STATE_FILE)
        except Exception:
            print("Failed to load state, creating new session...")
            context = browser.new_context()
    else:
        print("Creating new session...")
        context = browser.new_context()

    page = context.new_page()

    # Process all games
    for game in GAMES:
        run_game(page, game)

    # Save login state
    context.storage_state(path=STATE_FILE)

    print("Session saved")
    mark_run_done()
    context.close()
    browser.close()
    
    