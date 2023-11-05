class BalancedRecursiveCharacterTextSplitter:
    """Implementation of splitting text that looks at characters.
    Recursively tries to split by different characters to find one that works.
    Originally from Langchain's RecursiveCharacterTextSplitter.
    However this version retries if the chunk sizes does not meet the input requirements.
    This splitter is slow and not recommended for use.
    """

    def __init__(
        self,
        goal_length,
        max_length,
        chunk_overlap,
        info,
    ) -> None:
        self.info = info
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

    def _split_text(self, text: str, separators: list[str], goal_length=None) -> list[list[str]]:
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

        # self.info(f"Trying separator: {repr(separator)} with goal_length: {goal_length}")

        # Use the current separator to split the text
        if separator == "spacy_sentences":
            doc = self.spacy_sentences(text)
            splits = [sent.text for sent in doc.sents]
        else:
            splits = TextProcessing.split_text_with_regex(text, separator, self._keep_separator)
        final_combos = self.distribute_splits(splits, goal_length)

        # If any split was larger than the max size
        # final_combos will be returned empty from distribute_splits
        if final_combos:
            for combo in final_combos:
                # If a combo of splits is too small,
                # we adjust the goal_length and retry separator
                combo_token_count = self.tiktoken_len("".join(combo))
                if combo_token_count < self.goal_length * 0.75 and len(final_combos) > 1:
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

    def distribute_splits(self, splits: list, goal_length: int) -> list[list[str]]:
        # Build initial combos
        combos: list[list[str]] = []
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

    def split_text(self, text: str) -> list[str]:
        final_combos = self._split_text(text, self._separators, self.goal_length)
        return ["".join(combo) for combo in final_combos]
