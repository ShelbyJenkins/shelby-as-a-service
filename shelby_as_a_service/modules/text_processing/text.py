import re
import string
from urllib.parse import urlparse
import shutil
import os
import json
from typing import List
import tiktoken
import spacy


def tiktoken_len(document, encoding_model="text-embedding-ada-002"):
    tokenizer = tiktoken.encoding_for_model(encoding_model)
    tokens = tokenizer.encode(document, disallowed_special=())
    return len(tokens)


def strip_unwanted_chars(text):
    """
    Strips all characters from the input text that are not alphanumeric, punctuation, or whitespace.

    Parameters:
        text (str): The input text to be stripped.

    Returns:
        str: The stripped text.
    """
    # Define which chars can be kept; Alpha-numeric chars, punctuation, and whitespaces.
    allowed_chars = (
        string.ascii_letters + string.digits + string.punctuation + string.whitespace
    )

    # Remove unwanted chars using regex.
    stripped_text = re.sub(f"[^{re.escape(allowed_chars)}]", "", text)

    return stripped_text


def reduce_excess_whitespace(text):
    """
    Reduces any sequential occurrences of a specific whitespace character
    (' \t\n\r\v\f') to just two of those specific whitespaces.

    Parameters:
        text (str): The input text to be processed.

    Returns:
        str: The text with reduced whitespace.
    """
    # Map each whitespace character to its escape sequence (if needed)
    whitespace_characters = {
        " ": r" ",
        "\t": r"\t",
        "\n": r"\n",
        "\r": r"\r",
        "\v": r"\v",
        "\f": r"\f",
    }

    # Replace any sequential occurrences of each whitespace character
    # greater than 2 with just two.
    for char, escape_sequence in whitespace_characters.items():
        pattern = escape_sequence + "{3,}"
        replacement = char * 2
        text = re.sub(pattern, replacement, text)

    # Remove leading and trailing whitespaces.
    text = text.strip()

    return text


def remove_all_white_space_except_space(text):
    # Remove all whitespace characters (like \n, \r, \t, \f, \v) except space (' ')
    text = re.sub(r"[\n\r\t\f\v]+", "", text)
    # Remove any extra spaces
    text = re.sub(r" +", " ", text)
    # Remove leading and trailing spaces
    text = text.strip()
    return text


def remove_starting_whitespace_and_double_newlines(text):
    # Remove all starting whitespace characters (like \n, \r, \t, \f, \v, and ' ')
    text = re.sub(r"^[\n\r\t\f\v ]+", "", text)
    # Remove starting consecutive newline characters (\n\n)
    text = re.sub(r"^\n\n+", "", text)
    return text


def split_text_with_regex(text: str, separator: str, keep_separator: bool) -> List[str]:
    # Now that we have the separator, split the text
    if separator:
        if keep_separator:
            # The parentheses in the pattern keep the delimiters in the result.
            _splits = re.split(f"({separator})", text)
            splits = [_splits[i] + _splits[i + 1] for i in range(1, len(_splits), 2)]
            if len(_splits) % 2 == 0:
                splits += _splits[-1:]
            splits = [_splits[0]] + splits
        else:
            splits = re.split(separator, text)
    else:
        splits = list(text)
    return [s for s in splits if s != ""]


def extract_and_clean_title(document, url=None):
    """
    Extracts and cleans the title from a document's metadata or a provided URL.

    Parameters:
        doc (dict or object): The document which may either be a dictionary or an object.
        url (str, optional): A URL from which to extract a title if the document doesn't have one.

    Returns:
        dict: A dictionary with the cleaned title.
    """

    # Use metadata from doc or initialize as empty dictionary
    metadata = (
        document.metadata
        if hasattr(document, "metadata")
        else document.get("metadata", {})
    )
    title = metadata.title if hasattr(metadata, "title") else metadata.get("title", {})

    # If title is absent in metadata, attempt to derive it from provided URL or 'loc' in metadata
    if not title:
        use_url = url or metadata.get("loc", "")
        parsed_url = urlparse(use_url)
        _, tail = os.path.split(parsed_url.path)
        root, _ = os.path.splitext(tail)
        title = root

    title = strip_unwanted_chars(title)
    title = remove_all_white_space_except_space(title)
    title = reduce_excess_whitespace(title)

    return title
