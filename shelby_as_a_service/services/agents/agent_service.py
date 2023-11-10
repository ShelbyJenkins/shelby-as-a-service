    def prep_chat(
        self, query, llm_model_name: Optional[str] = None
    ) -> typing.Tuple[list[dict[str, str]], "ModelConfig", int]:
        llm_model = self.get_model(requested_model_name=llm_model_name)

        prompt = PromptTemplates.create_openai_prompt(
            query=query,
            prompt_template_path=prompt_template_path,
        )

        total_prompt_tokens = text_utils.tiktoken_len_of_openai_prompt(prompt, llm_model)

        if prompt is None or llm_model is None or total_prompt_tokens is None:
            raise ValueError(
                f"Error with input values - prompt: {prompt}, model: {llm_model}, total_prompt_tokens: {total_prompt_tokens}"
            )
        return prompt, llm_model, total_prompt_tokens