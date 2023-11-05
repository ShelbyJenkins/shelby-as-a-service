import logging
from typing import Optional

import spacy

from . import text_utils


class DFSTextSplitter:
    """Splits text that attempts to split by paragraph, newlines, sentences, spaces, and finally chars.
    Splits with regex for all but sentences and words.
    It then tries to construct chunks with the splits that fall within the token limits.
    Tiktoken is used as a tokenizer.
    After splitting, creating the chunks is used with a DFS algo utilizing memoization and a heuristic prefilter.
    """

    max_length: int
    goal_length_max_threshold: int
    goal_length_min_threshold: int
    chunk_overlap_max_threshold: int
    chunk_overlap_min_threshold: int
    chunk_overlap: int
    average_range_min: int

    def __init__(
        self,
        goal_length: int,
        overlap_percent: int,
    ) -> None:
        self.log = logging.getLogger(self.__class__.__name__)
        self.split_with_regex = text_utils.split_text_with_regex
        self.spacy = spacy.load("en_core_web_sm")

        self.memo: dict = {}
        self.original_goal_length = goal_length
        self.goal_length = goal_length
        self.overlap_percent = overlap_percent
        if not overlap_percent or overlap_percent < 10:
            self.overlap_percent = 10

        self._separators = ["\n\n", "\n", "spacy_sentences", "spacy_words", " ", ""]
        self.threshold_modifier = 0.1
        self.min_length = 0.7
        self._keep_separator: bool = True

    def _set_thresholds(self, goal_length=None):
        if goal_length is None:
            self.goal_length = self.goal_length - int(0.02 * self.goal_length)
        else:
            self.goal_length = goal_length

        self.max_length = int(self.goal_length * 1.25)

        self.goal_length_max_threshold = self.goal_length + int(
            self.threshold_modifier * self.goal_length
        )
        self.goal_length_min_threshold = self.goal_length - int(
            self.threshold_modifier * self.goal_length
        )

        self.chunk_overlap = int(self.goal_length * (self.overlap_percent / 100))

        self.chunk_overlap_max_threshold = self.chunk_overlap + int(
            self.threshold_modifier * self.chunk_overlap
        )
        self.chunk_overlap_min_threshold = self.chunk_overlap - int(
            self.threshold_modifier * self.chunk_overlap
        )
        # self.log.info(f"New goal_length: {self.goal_length}")

    def _set_heuristics(self, text, splits):
        """Sets some values that we use as a pre-filter to speed up the process."""
        self.average_range_min = 0
        for split in splits:
            if text_utils.tiktoken_len(split) > self.max_length:
                return False
        total_tokens = text_utils.tiktoken_len(text)

        estimated_chunks = int(total_tokens / self.goal_length)
        if estimated_chunks == 1:
            estimated_chunks = 2
        estimated_splits_per_chunk = int(len(splits) / estimated_chunks)

        # Test required chunks exceed splits
        if len(splits) < estimated_splits_per_chunk:
            return False

        self.average_range_min = int((estimated_splits_per_chunk / 2))
        return True

    def _split_text(self, text: str, separator: str) -> Optional[list[str]]:
        """Splits text by various methods."""

        match separator:
            case "\n\n":
                splits = self.split_with_regex(text, separator, self._keep_separator)
            case "\n":
                splits = self.split_with_regex(text, separator, self._keep_separator)
            case "spacy_sentences":
                doc = self.spacy(text)
                splits = [sent.text for sent in doc.sents]
            case "spacy_words":
                doc = self.spacy(text)
                splits = [token.text for token in doc]
            case " ":
                splits = self.split_with_regex(text, separator, self._keep_separator)
            case "":
                splits = self.split_with_regex(text, separator, self._keep_separator)
            case _:
                return None
        if splits is None:
            return None
        if len(splits) < 2:
            return None
        return splits

    def _find_valid_chunk_combinations(self, splits):
        """Initializes the chunk combo finding process."""

        chunks_as_splits = self._recursive_chunk_tester(0, splits)

        if chunks_as_splits is None:
            return None
        if len(chunks_as_splits) < 2:
            return None

        # self.log.info(f"chunks_as_splits: {chunks_as_splits}")
        return chunks_as_splits

    def _recursive_chunk_tester(self, start, splits):
        """Manages the testing of chunk combos.
        Stops when it successfuly finds a path to the final split.
        """

        valid_ends = self._find_valid_endsplits_for_chunk(start, splits)
        if valid_ends is None:
            return None

        for i, end_split in enumerate(valid_ends):
            # Successful exit condition
            if end_split + 1 == len(splits):
                return [end_split]
            # This keeps things from melting
            if end_split == start:
                valid_ends.pop(i)

        for end_split in valid_ends:
            # Recursive call with the next start
            next_chunk = self._recursive_chunk_tester(end_split, splits)

            # If a valid combination was found in the recursive call
            if next_chunk is not None:
                return [end_split] + next_chunk

        # If no valid chunking found for the current start, return None
        return None

    def _find_valid_endsplits_for_chunk(self, start, splits):
        """Returns endsplits that are within the threshold of goal_length.
        Uses memoization to save from having to recompute.
        Starts calculation at + self.average_range_min as a pre-filter.
        """
        if start in self.memo:
            # self.log.info(f"Returning memoized result for start at index {start}")
            return self.memo[start]

        valid_ends = []

        current_length = text_utils.tiktoken_len(
            "".join(splits[start : start + 1 + self.average_range_min])
        )
        for j in range(start + 1 + self.average_range_min, len(splits)):
            # Final tokenization will be of combined chunks - not individual chars!
            current_length = text_utils.tiktoken_len("".join(splits[start:j]))
            if current_length >= self.goal_length_min_threshold - self.chunk_overlap_max_threshold:
                if current_length <= self.max_length - self.chunk_overlap_max_threshold:
                    valid_ends.append(j)
                else:
                    break
        # self.log.info(f"Start: {start} has valid_ends: {valid_ends}")
        self.memo[start] = valid_ends

        return valid_ends

    def _create_chunks(self, chunk_end_splits, splits):
        """Creates the text chunks including overlap"""
        # Initialize an empty list to store chunks
        chunks = []

        # Starting point for the first chunk

        if chunk_end_splits[0] != 0:
            chunk_end_splits.insert(0, 0)  # whoo whoo
        # Iterate over chunk_end_splits
        for i, end_split in enumerate(chunk_end_splits):
            forward_overlap_text = ""
            backwards_overlap_text = ""
            if end_split == 0:
                forward_overlap_text = self._create_forward_overlap(
                    chunk_end_splits[i + 1],
                    chunk_end_splits[i + 2],
                    self.chunk_overlap_min_threshold,
                    self.chunk_overlap_max_threshold,
                    splits,
                )
            elif chunk_end_splits[i + 1] + 1 == len(splits):
                backwards_overlap_text = self._create_backwards_overlap(
                    end_split,
                    chunk_end_splits[i - 1],
                    self.chunk_overlap_min_threshold,
                    self.chunk_overlap_max_threshold,
                    splits,
                )
                break
            else:
                forward_overlap_text = self._create_forward_overlap(
                    chunk_end_splits[i + 1],
                    chunk_end_splits[i + 2],
                    int(self.chunk_overlap_min_threshold / 2),
                    int(self.chunk_overlap_max_threshold / 2),
                    splits,
                )
                backwards_overlap_text = self._create_backwards_overlap(
                    end_split,
                    chunk_end_splits[i - 1],
                    int(self.chunk_overlap_min_threshold / 2),
                    int(self.chunk_overlap_max_threshold / 2),
                    splits,
                )

            if forward_overlap_text is None or backwards_overlap_text is None:
                return None

            # Append the sublist to chunks
            chunk_splits = splits[end_split : chunk_end_splits[i + 1] + 1]
            text_chunk = "".join(chunk_splits)
            if len(text_chunk) < 1:
                return None
            text_chunk = "".join([backwards_overlap_text, text_chunk, forward_overlap_text])

            text_chunk = text_utils.reduce_excess_whitespace(text_chunk)
            token_count = text_utils.tiktoken_len(text_chunk)
            if token_count > self.max_length:
                # self.log.info(f"chunk token count too big!: {text_utils.tiktoken_len(text_chunk)}")
                return None
            # self.log.info(f"chunk token count: {text_utils.tiktoken_len(text_chunk)}")
            # self.log.info(f"backwards_overlap_text token count: {text_utils.tiktoken_len(backwards_overlap_text)}")
            # self.log.info(f"forward_overlap_text token count: {text_utils.tiktoken_len(forward_overlap_text)}")

            chunks.append(text_chunk)

        return chunks

    def _create_forward_overlap(self, end_split, next_end, overlap_min, overlap_max, splits):
        """Creates forward chunks."""
        overlap_text = "".join(splits[end_split + 1 : next_end])
        for separator in self._separators:
            # self.log.info(f"Trying overlap separator: {repr(separator)}")
            overlap_splits = self._split_text(overlap_text, separator)
            if overlap_splits is None:
                continue
            current_length = 0
            saved_splits = []
            for split in overlap_splits:
                saved_splits.append(split)
                current_length = text_utils.tiktoken_len("".join(saved_splits))
                if current_length > overlap_max:
                    break
                if current_length >= overlap_min:
                    overlap = "".join(saved_splits)
                    return overlap
        return None

    def _create_backwards_overlap(
        self, start_split, previous_end, overlap_min, overlap_max, splits
    ):
        """Creates backwards chunks."""
        overlap_text = "".join(splits[previous_end:start_split])
        for separator in self._separators:
            # self.log.info(f"Trying overlap separator: {repr(separator)}")
            overlap_splits = self._split_text(overlap_text, separator)
            if overlap_splits is None:
                continue
            current_length = 0
            saved_splits = []
            for j in range(len(overlap_splits) - 1, -1, -1):
                saved_splits.insert(0, overlap_splits[j])
                current_length = text_utils.tiktoken_len("".join(saved_splits))
                if current_length > overlap_max:
                    break
                if current_length >= overlap_min:
                    overlap = "".join(saved_splits)
                    return overlap
        return None

    def split_text(self, text: str) -> Optional[list[str]]:
        """Interface for class."""
        self._set_thresholds(self.original_goal_length)
        # Skip if too small
        if text_utils.tiktoken_len(text) < self.max_length:
            self.log.info(
                f"Doc length: {text_utils.tiktoken_len(text)} already within max_length: {self.max_length}"
            )
            return [text]
        for separator in self._separators:
            self.log.info(f"Trying separator: {repr(separator)}")
            self._set_thresholds(self.original_goal_length)
            while (self.goal_length / self.original_goal_length) > self.min_length:
                self.memo = {}

                chunk_end_splits = None
                text_chunks = None
                splits = self._split_text(text, separator)
                if splits is not None:
                    if self._set_heuristics(text, splits):
                        chunk_end_splits = self._find_valid_chunk_combinations(splits)
                if chunk_end_splits is not None:
                    text_chunks = self._create_chunks(chunk_end_splits, splits)
                    if text_chunks is not None:
                        return text_chunks
                self._set_thresholds()
        return None
