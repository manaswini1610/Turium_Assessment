import logging
from typing import Tuple
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger("app.url_service")

REQUEST_TIMEOUT_SECONDS = 10
MIN_USABLE_TEXT_LENGTH = 20
UNWANTED_TAGS = ["script", "style", "nav", "header", "footer", "aside", "form", "noscript", "iframe", "svg"]


class URLFetchError(Exception):
    """Raised when a URL cannot be validated, fetched, or contains no usable text."""


def validate_url_scheme(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise URLFetchError("URL must use the http or https scheme.")
    if not parsed.netloc:
        raise URLFetchError("URL is missing a valid host.")


def fetch_and_extract(url: str) -> Tuple[str, str]:
    """Fetches a webpage and extracts its title and readable text.

    Raises URLFetchError with a user-friendly message if the URL is invalid,
    unreachable, or contains no usable text.
    """
    validate_url_scheme(url)

    try:
        response = requests.get(
            url,
            timeout=REQUEST_TIMEOUT_SECONDS,
            headers={"User-Agent": "AI-Knowledge-Inbox/1.0"},
        )
        response.raise_for_status()
    except requests.exceptions.Timeout as exc:
        logger.error(f"URL fetch timed out: {url}")
        raise URLFetchError(f"Request to {url} timed out after {REQUEST_TIMEOUT_SECONDS} seconds.") from exc
    except requests.exceptions.RequestException as exc:
        logger.error(f"URL fetch failed for {url}: {exc}")
        raise URLFetchError(f"Could not fetch the URL: {url}") from exc

    soup = BeautifulSoup(response.text, "html.parser")

    for tag_name in UNWANTED_TAGS:
        for tag in soup.find_all(tag_name):
            tag.decompose()

    title = url
    if soup.title and soup.title.string and soup.title.string.strip():
        title = soup.title.string.strip()

    raw_text = soup.get_text(separator="\n")
    lines = (line.strip() for line in raw_text.splitlines())
    extracted_text = "\n".join(line for line in lines if line)

    if len(extracted_text) < MIN_USABLE_TEXT_LENGTH:
        logger.error(f"No usable text extracted from URL: {url}")
        raise URLFetchError("No usable text content could be extracted from this URL.")

    logger.info(f"Extracted {len(extracted_text)} character(s) of text from {url}")
    return title, extracted_text
