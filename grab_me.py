import os

from bcncita import CustomerProfile, DocType, OperationType, Province, try_cita

e = os.environ

if __name__ == "__main__":
    customer = CustomerProfile(
        anticaptcha_api_key=e.get("ANTICAPTCHA_API_KEY"),
        auto_captcha=bool(e.get("ANTICAPTCHA_API_KEY")),
        chrome_driver_path="/usr/bin/chromedriver",
        sms_webhook_token=e.get("SMS_WEBHOOK_TOKEN"),
        province=Province[e.get("PROVINCE", "BARCELONA")],
        operation_code=OperationType[e.get("OPERATION", "TOMA_HUELLAS")],
        doc_type=DocType[e.get("DOC_TYPE", "NIE")],
        doc_value=e["DOC_VALUE"],
        country=e.get("COUNTRY", "RUSIA"),
        name=e["NAME"],
        phone=e["PHONE"],
        email=e["EMAIL"],
        year_of_birth=e.get("YEAR_OF_BIRTH"),
        min_date=e.get("MIN_DATE"),
        max_date=e.get("MAX_DATE"),
    )
    try_cita(context=customer, cycles=int(e.get("CYCLES", 100000)))
