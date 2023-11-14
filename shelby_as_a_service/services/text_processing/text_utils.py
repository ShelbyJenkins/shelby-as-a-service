import hashlib
import os
import re
import string
from typing import Optional
from urllib.parse import urlparse

import tiktoken
from langchain.schema import Document


def get_tokens(text: str, encoding_model="text-embedding-ada-002") -> list[int]:
    tokenizer = tiktoken.encoding_for_model(encoding_model)
    return tokenizer.encode(text, disallowed_special=())


def tiktoken_len(text: str, encoding_model="text-embedding-ada-002") -> int:
    tokenizer = tiktoken.encoding_for_model(encoding_model)
    tokens = tokenizer.encode(text, disallowed_special=())
    return len(tokens)


def tiktoken_len_of_document_list(texts: list[str]) -> int:
    token_count = 0
    for text in texts:
        tokens = 0
        tokens += tiktoken_len(text)
        token_count += tokens
    return token_count


def clean_text_content(text: str) -> str:
    text = strip_unwanted_chars(text)
    text = reduce_excess_whitespace(text)
    return text


def strip_unwanted_chars(text):
    """
    Strips all characters from the input text that are not alphanumeric, punctuation, or whitespace.

    Parameters:
        text (str): The input text to be stripped.

    Returns:
        str: The stripped text.
    """
    # Define which chars can be kept; Alpha-numeric chars, punctuation, and whitespaces.
    allowed_chars = string.ascii_letters + string.digits + string.punctuation + string.whitespace

    # Remove unwanted chars using regex.
    stripped_text = re.sub(f"[^{re.escape(allowed_chars)}]", "", text)

    return stripped_text


def reduce_excess_whitespace(text):
    """
    Reduces any sequential occurrences of a specific whitespace character
    (' \t\n\r\v\f') to just one of those specific whitespaces.

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
    # greater than 2 with just one.
    for char, escape_sequence in whitespace_characters.items():
        pattern = f"{escape_sequence}{{2,}}"  # Using an f-string to interpolate the escape_sequence
        text = re.sub(pattern, char, text)

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


def split_text_with_regex(text: str, separator: str, keep_separator: bool) -> list[str]:
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


def extract_document_content(doc: dict | str | Document) -> str:
    # Check if document is a string
    if isinstance(doc, str):
        return doc
    # Check dictionary keys
    elif isinstance(doc, dict):
        for key in ["page_content", "content"]:
            if (document_content := doc.get(key)) is not None:
                return document_content

    elif isinstance(doc, Document):
        for attr in ["page_content", "content"]:
            if (document_content := getattr(doc, attr, None)) is not None:
                return document_content
    else:
        raise ValueError(
            f"Document must be a string, dictionary, or Document. Received {type(doc).__name__}"
        )

    raise ValueError(f"No content found in document {doc}")


def extract_and_clean_title(doc, uri=None) -> str:
    """
    Extracts and cleans the title from a document's metadata or a provided URL.

    Parameters:
        doc (dict or object): The document which may either be a dictionary or an object.
        url (str, optional): A URL from which to extract a title if the document doesn't have one.

    Returns:
        dict: A dictionary with the cleaned title.
    """

    # Use metadata from doc or initialize as empty dictionary
    metadata = doc.metadata if hasattr(doc, "metadata") else doc.get("metadata", {})
    title = metadata.title if hasattr(metadata, "title") else metadata.get("title", {})

    # If title is absent in metadata, attempt to derive it from provided URL or 'loc' in metadata
    if not title:
        use_url = uri or metadata.get("loc", "")
        parsed_url = urlparse(use_url)
        _, tail = os.path.split(parsed_url.path)
        root, _ = os.path.splitext(tail)
        title = root

    title = strip_unwanted_chars(title)
    title = remove_all_white_space_except_space(title)
    title = reduce_excess_whitespace(title)

    return title


def extract_uri(doc: dict | Document) -> str:
    def _extract_uri(doc_or_metadata: dict | Document) -> Optional[str]:
        # Check dictionary keys
        if isinstance(doc_or_metadata, dict):
            for key in ["source", "url", "loc", "uri"]:
                uri = doc_or_metadata.get(key, None)
                return uri

        elif isinstance(doc_or_metadata, Document):
            for attr in ["source", "url", "loc", "uri"]:
                uri = getattr(doc_or_metadata, attr, None)
                return uri

        return None

    if metadata := getattr(doc, "metadata", None):
        if uri := _extract_uri(metadata):
            return uri
    uri = _extract_uri(doc)
    if uri:
        return uri
    else:
        raise ValueError(f"No uri found in document {doc}")


def hash_content(content) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def check_and_handle_name_collision(existing_names: list[str], new_name: str) -> str:
    i = 0
    test_name = new_name
    while test_name in existing_names:
        test_name = f"{new_name}_{i}"
        i += 1
    return test_name
