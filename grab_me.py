import logging
import os
import signal
import sys
import time

from bcncita import CustomerProfile, DocType, Office, OperationType, Province, try_cita
from bcncita.notify import notify

e = os.environ


def placeholder(name):
    return e.get(name, "").strip().upper() in ("", "CHANGE_ME")


def csv(name):
    return [v.strip() for v in e.get(name, "").split(",") if v.strip()]


if __name__ == "__main__":
    logging.basicConfig(format="%(asctime)s - %(message)s", level=logging.INFO, stream=sys.stdout)

    if "CHANGE_ME" in e.get("DISCORD_WEBHOOK_URL", "").upper():
        del os.environ["DISCORD_WEBHOOK_URL"]

    # No anti-captcha key: only watch for availability and alert, never book.
    alert_only = placeholder("ANTICAPTCHA_API_KEY")
    if not alert_only and placeholder("SMS_WEBHOOK_TOKEN"):
        # Without it the bot would block on input() waiting for a human.
        sys.exit("SMS_WEBHOOK_TOKEN is required when ANTICAPTCHA_API_KEY is set")

    customer = CustomerProfile(
        alert_only=alert_only,
        anticaptcha_api_key=None if alert_only else e["ANTICAPTCHA_API_KEY"],
        auto_captcha=not alert_only,
        auto_office=True,
        sms_webhook_token=None if alert_only else e["SMS_WEBHOOK_TOKEN"],
        chrome_driver_path="/usr/bin/chromedriver",
        province=Province[e.get("PROVINCE", "BARCELONA")],
        operation_code=OperationType[e.get("OPERATION", "TOMA_HUELLAS")],
        doc_type=DocType[e.get("DOC_TYPE", "NIE")],
        doc_value=e["DOC_VALUE"],
        country=e.get("COUNTRY", "RUSIA"),
        name=e["NAME"],
        phone=e["PHONE"],
        email=e["EMAIL"],
        year_of_birth=e.get("YEAR_OF_BIRTH"),
        offices=[Office[o] for o in csv("OFFICES")],  # e.g. BARCELONA_MALLORCA,BARCELONA
        except_offices=[Office[o].value for o in csv("EXCEPT_OFFICES")],
        min_date=e.get("MIN_DATE"),
        max_date=e.get("MAX_DATE"),
        min_time=e.get("MIN_TIME"),
        max_time=e.get("MAX_TIME"),
        heartbeat_cycles=int(e.get("HEARTBEAT_CYCLES", 100)),
    )
    session_cycles = int(e.get("SESSION_CYCLES", 200))  # attempts per browser before a fresh one
    retry_delay = int(e.get("RETRY_DELAY", 30))  # seconds between browser sessions

    if not e.get("DISCORD_WEBHOOK_URL"):
        logging.warning("DISCORD_WEBHOOK_URL is not set: no Discord notifications")
    if alert_only:
        logging.warning("ANTICAPTCHA_API_KEY not set: ALERT-ONLY mode, nothing will be booked")
    notify(
        f"cita-bot started in {'ALERT-ONLY' if alert_only else 'AUTOBOOK'} mode: "
        f"{customer.province.name} / {customer.operation_code.name}, "
        f"offices={[o.name for o in customer.offices] or 'any'}, "
        f"dates {customer.min_date or '*'}..{customer.max_date or '*'}"
    )

    session = 0
    while True:  # runs until the container is stopped
        session += 1
        logging.info(f"Starting browser session {session} ({session_cycles} attempts)")
        try:
            booked = try_cita(context=customer, cycles=session_cycles)
        except Exception as ex:
            logging.exception("Browser session crashed")
            notify(f"Browser session crashed: {ex}"[:300])
            booked = False

        if booked:
            # Idle instead of exiting: Dokploy restarts exited containers and we'd rebook.
            logging.info("Booked. Idling until the container is stopped.")
            while True:
                signal.pause()

        logging.info(f"Session {session} over, next one in {retry_delay}s")
        time.sleep(retry_delay)
