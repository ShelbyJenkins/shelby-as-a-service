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


def strip_excess_whitespace(text):
    # Defines which chars can be kept; Alpha-numeric chars, punctionation, and whitespaces.
    # Remove bad chars
    text = re.sub(f"[^{re.escape(string.printable)}]", "", text)
    # Reduces any sequential occurrences of a specific whitespace (' \t\n\r\v\f') to just two of those specific whitespaces
    # Create a dictionary to map each whitespace character to its escape sequence (if needed)
    whitespace_characters = {
        " ": r" ",
        "\t": r"\t",
        "\n": r"\n",
        "\r": r"\r",
        "\v": r"\v",
        "\f": r"\f",
    }
    # Replace any sequential occurrences of each whitespace characters greater than 3 with just two
    for char, escape_sequence in whitespace_characters.items():
        pattern = escape_sequence + "{3,}"
        replacement = char * 2
        text = re.sub(pattern, replacement, text)

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
