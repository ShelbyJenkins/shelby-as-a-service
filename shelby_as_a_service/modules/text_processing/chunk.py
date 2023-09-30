class DFSTextSplitter:
    """Splits text that attempts to split by paragraph, newlines, sentences, spaces, and finally chars.
    Splits with regex for all but sentences and words.
    It then tries to construct chunks with the splits that fall within the token limits.
    Tiktoken is used as a tokenizer.
    After splitting, creating the chunks is used with a DFS algo utilizing memoization and a heuristic prefilter.
    """

    def __init__(
        self,
        goal_length,
        overlap_percent,
        print_and_log,
    ) -> None:
        self.print_and_log = print_and_log

        self.split_with_regex = TextProcessing.split_text_with_regex
        self.spacy = spacy.load("en_core_web_sm")
        self.tiktoken_len = TextProcessing.tiktoken_len

        self.memo = {}
        self.original_goal_length = goal_length
        self.goal_length = goal_length
        self.overlap_percent = overlap_percent
        if not overlap_percent or overlap_percent < 10:
            self.overlap_percent = 10
        self.max_length = None
        self.goal_length_max_threshold = None
        self.goal_length_min_threshold = None
        self.chunk_overlap = None
        self.chunk_overlap_max_threshold = None
        self.chunk_overlap_min_threshold = None
        self.average_range_min = None

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
        # self.print_and_log(f"New goal_length: {self.goal_length}")

    def _set_heuristics(self, text, splits):
        """Sets some values that we use as a pre-filter to speed up the process."""
        self.average_range_min = 0
        for split in splits:
            if self.tiktoken_len(split) > self.max_length:
                return False
        total_tokens = self.tiktoken_len(text)

        estimated_chunks = int(total_tokens / self.goal_length)
        if estimated_chunks == 1:
            estimated_chunks = 2
        estimated_splits_per_chunk = int(len(splits) / estimated_chunks)

        # Test required chunks exceed splits
        if len(splits) < estimated_splits_per_chunk:
            return False

        self.average_range_min = int((estimated_splits_per_chunk / 2))
        return True

    def _split_text(self, text, separator) -> List[List[str]]:
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

        # self.print_and_log(f"chunks_as_splits: {chunks_as_splits}")
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
            # self.print_and_log(f"Returning memoized result for start at index {start}")
            return self.memo[start]

        valid_ends = []

        current_length = self.tiktoken_len(
            "".join(splits[start : start + 1 + self.average_range_min])
        )
        for j in range(start + 1 + self.average_range_min, len(splits)):
            # Final tokenization will be of combined chunks - not individual chars!
            current_length = self.tiktoken_len("".join(splits[start:j]))
            if (
                current_length
                >= self.goal_length_min_threshold - self.chunk_overlap_max_threshold
            ):
                if current_length <= self.max_length - self.chunk_overlap_max_threshold:
                    valid_ends.append(j)
                else:
                    break
        # self.print_and_log(f"Start: {start} has valid_ends: {valid_ends}")
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
            text_chunk = "".join(
                [backwards_overlap_text, text_chunk, forward_overlap_text]
            )

            text_chunk = TextProcessing.remove_starting_whitespace_and_double_newlines(
                text_chunk
            )
            token_count = self.tiktoken_len(text_chunk)
            if token_count > self.max_length:
                # self.print_and_log(f"chunk token count too big!: {self.tiktoken_len(text_chunk)}")
                return None
            # self.print_and_log(f"chunk token count: {self.tiktoken_len(text_chunk)}")
            # self.print_and_log(f"backwards_overlap_text token count: {self.tiktoken_len(backwards_overlap_text)}")
            # self.print_and_log(f"forward_overlap_text token count: {self.tiktoken_len(forward_overlap_text)}")

            chunks.append(text_chunk)

        return chunks

    def _create_forward_overlap(
        self, end_split, next_end, overlap_min, overlap_max, splits
    ):
        """Creates forward chunks."""
        overlap_text = "".join(splits[end_split + 1 : next_end])
        for separator in self._separators:
            # self.print_and_log(f"Trying overlap separator: {repr(separator)}")
            overlap_splits = self._split_text(overlap_text, separator)
            if overlap_splits is None:
                continue
            current_length = 0
            saved_splits = []
            for split in overlap_splits:
                saved_splits.append(split)
                current_length = self.tiktoken_len("".join(saved_splits))
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
            # self.print_and_log(f"Trying overlap separator: {repr(separator)}")
            overlap_splits = self._split_text(overlap_text, separator)
            if overlap_splits is None:
                continue
            current_length = 0
            saved_splits = []
            for j in range(len(overlap_splits) - 1, -1, -1):
                saved_splits.insert(0, overlap_splits[j])
                current_length = self.tiktoken_len("".join(saved_splits))
                if current_length > overlap_max:
                    break
                if current_length >= overlap_min:
                    overlap = "".join(saved_splits)
                    return overlap
        return None

    def split_text(self, text) -> List[str]:
        """Interface for class."""
        self._set_thresholds(self.original_goal_length)
        # Skip if too small
        if self.tiktoken_len(text) < self.max_length:
            self.print_and_log(
                f"Doc length: {self.tiktoken_len(text)} already within max_length: {self.max_length}"
            )
            return text
        for separator in self._separators:
            self.print_and_log(f"Trying separator: {repr(separator)}")
            self._set_thresholds(self.original_goal_length)
            while (self.goal_length / self.original_goal_length) > self.min_length:
                self.memo = {}
                splits = []
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


class BalancedRecursiveCharacterTextSplitter:
    """Implementation of splitting text that looks at characters.
    Recursively tries to split by different characters to find one that works.
    Originally from Langchain's RecursiveCharacterTextSplitter.
    However this version retries if the chunk sizes does not meet the input requirements.
    """

    def __init__(
        self,
        goal_length,
        max_length,
        chunk_overlap,
        print_and_log,
    ) -> None:
        self.print_and_log = print_and_log
        self._separators = ["\n\n", "\n", "spacy_sentences", " ", ""]
        self.spacy_sentences = spacy.load("en_core_web_sm")
        self._keep_separator: bool = False
        self.goal_length = goal_length
        self.max_length = max_length or (self.goal_length * 1.25)
        self.tiktoken_len = TextProcessing.tiktoken_len
        # Chunk size logic
        if chunk_overlap is not None:
            # There must be at least some chunk overlap for this to function
            if chunk_overlap < 100:
                self._chunk_overlap = 100
            else:
                self._chunk_overlap = chunk_overlap
        else:
            self._chunk_overlap = self._chunk_overlap

    def _split_text(
        self, text: str, separators: List[str], goal_length=None
    ) -> List[List[str]]:
        """Split incoming text and return chunks."""

        # Have to define here initially so it can be redefined for each recursion
        if goal_length is None:
            goal_length = self.goal_length
        # Get appropriate separator to use
        separator = separators[-1]
        new_separators = []
        for i, _s in enumerate(separators):
            if _s == "":
                separator = _s
                break
            if _s == "spacy_sentences":
                separator = "spacy_sentences"
                new_separators = separators[i + 1 :]
                break
            elif re.search(_s, text):
                separator = _s
                new_separators = separators[i + 1 :]
                break

        # self.print_and_log(f"Trying separator: {repr(separator)} with goal_length: {goal_length}")

        # Use the current separator to split the text
        if separator == "spacy_sentences":
            doc = self.spacy_sentences(text)
            splits = [sent.text for sent in doc.sents]
        else:
            splits = TextProcessing.split_text_with_regex(
                text, separator, self._keep_separator
            )
        final_combos = self.distribute_splits(splits, goal_length)

        # If any split was larger than the max size
        # final_combos will be returned empty from distribute_splits
        if final_combos:
            for combo in final_combos:
                # If a combo of splits is too small,
                # we adjust the goal_length and retry separator
                combo_token_count = self.tiktoken_len("".join(combo))
                if (
                    combo_token_count < self.goal_length * 0.75
                    and len(final_combos) > 1
                ):
                    new_goal_length = int(
                        goal_length + (combo_token_count / (len(final_combos) - 1))
                    )
                    final_combos = self._split_text(text, separators, new_goal_length)
                # If a combo of splits is too large, we retry with new separator
                elif combo_token_count > self.max_length and new_separators:
                    final_combos = self._split_text(text, new_separators, goal_length)
        else:
            # In the case distribute_splits returned None continue to next separator
            final_combos = self._split_text(text, new_separators, goal_length)

        # All combos satisfy requirements
        return final_combos

    def distribute_splits(self, splits: list, goal_length: int) -> List[List[str]]:
        # Build initial combos
        combos: List[List[str]] = []
        current_combo = []
        combo_token_count = 0
        for split in splits:
            split_token_count = self.tiktoken_len(split)
            # If too big skip to next separator
            if split_token_count > self.max_length:
                combos = []
                return combos
            if goal_length > (combo_token_count + split_token_count):
                current_combo.append(split)
                combo_token_count = self.tiktoken_len("".join(current_combo))
            # Combo larger than goal_length
            else:
                current_combo.append(split)
                combos.append(current_combo)
                # Create a new combo and add the current split so there is overlap
                if split_token_count < self._chunk_overlap:
                    current_combo = []
                    current_combo.append(split)
                    combo_token_count = self.tiktoken_len("".join(current_combo))
                # If the overlap chunk is larger than overlap size
                # continue to next separator
                else:
                    combos = []
                    return combos
        # Add the last combo if it has more than just the overlap chunk
        if len(current_combo) > 1:
            combos.append(current_combo)
        return combos

    def split_text(self, text: str) -> List[str]:
        final_combos = self._split_text(text, self._separators, self.goal_length)
        return ["".join(combo) for combo in final_combos]
