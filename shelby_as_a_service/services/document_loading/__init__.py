from typing import Literal

from services.document_loading.email_fastmail import EmailFastmail
from services.document_loading.web import GenericRecursiveWebScraper, GenericWebScraper

AVAILABLE_PROVIDERS_TYPINGS = Literal[
    GenericWebScraper.class_name,
    GenericRecursiveWebScraper.class_name,
    EmailFastmail.class_name,
]
AVAILABLE_PROVIDERS_NAMES: list[str] = [
    GenericWebScraper.CLASS_NAME,
    GenericRecursiveWebScraper.CLASS_NAME,
    EmailFastmail.CLASS_NAME,
]
AVAILABLE_PROVIDERS = [
    GenericWebScraper,
    GenericRecursiveWebScraper,
    EmailFastmail,
]
AVAILABLE_PROVIDERS_UI_NAMES = [
    GenericWebScraper.CLASS_UI_NAME,
    GenericRecursiveWebScraper.CLASS_UI_NAME,
    EmailFastmail.CLASS_UI_NAME,
]
