import logging
import os
import time

import requests

THROTTLE = 300  # seconds before the same non-urgent message is posted again
_last_sent: dict = {}


def notify(text, driver=None, urgent=False):
    """Log `text` and post it to DISCORD_WEBHOOK_URL, with a screenshot if `driver` is given.

    `urgent` pings DISCORD_MENTION (e.g. "<@123456789>") and bypasses the repeat throttle.
    """
    logging.info(f"[notify] {text}")
    url = os.environ.get("DISCORD_WEBHOOK_URL")
    if not url:
        return

    now = time.monotonic()
    if not urgent:
        if now - _last_sent.get(text, -THROTTLE) < THROTTLE:
            return
        _last_sent[text] = now

    mention = os.environ.get("DISCORD_MENTION")
    if urgent and mention:
        text = f"{mention} {text}"

    files = None
    if driver is not None:
        try:
            files = {"file": ("screenshot.png", driver.get_screenshot_as_png(), "image/png")}
        except Exception as e:
            logging.error(f"Screenshot for notification failed: {e}")

    try:
        requests.post(
            url,
            data={"content": text[:1900], "username": "cita-bot"},
            files=files,
            timeout=15,
        ).raise_for_status()
    except requests.RequestException as e:
        logging.error(f"Discord notification failed: {e}")
