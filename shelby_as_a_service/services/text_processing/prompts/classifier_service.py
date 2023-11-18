import os
from collections import Counter
from typing import Literal, Optional

import services.text_processing.prompts.prompt_template_service as prompts
import services.text_processing.text_utils as text_utils


def parse_results(results: list, options: list[str | bool]) -> tuple[str | bool, str]:
    results_count = Counter(results)
    log_string = ""
    for value in options:
        percentage = (results_count[value] / len(results)) * 100
        log_string += f"{value}: {percentage:.2f}%"

    return results_count.most_common(1)[0][0], log_string


# Boolean Classifier
def create_boolean_classifier_logit_bias() -> tuple[dict[str, int], int]:
    return {"15": 100, "16": 100}, 1


def create_boolean_classifier_prompt(
    feature: str,
    user_input: Optional[str] = None,
    prompt_string: Optional[str] = None,
    prompt_template_path: Optional[str] = None,
) -> tuple[str, str]:
    system_prompt = prompts.load_prompt_template(
        prompt_template_path=prompt_template_path, prompt_string=prompt_string
    )

    system_prompt_string = system_prompt + "\nIf true return 1, if false return 0."
    user_input_string = f"feature: {feature}"
    if user_input:
        user_input_string += f"\nuser_input: {user_input}"
    return system_prompt_string, user_input_string


def boolean_classifier_validator(response: str):
    if len(response) > 1 or text_utils.tiktoken_len(text=response) > 1:
        raise ValueError(f"response '{response}' should be a single token.")
    if response != "0" and response != "1":
        raise ValueError(f"response '{response}' should be either 0 or 1.")


def boolean_classifier_response_parser(response: str) -> bool:
    if response == "1":
        return True
    return False


# Single Option Classifier
def create_logit_bias(
    number_of_options: int,
    number_of_decisions: int,
    llm_model_name: str,
    separator: Optional[Literal["\n", ",", " "]] = None,
) -> tuple[dict[str, int], int]:
    if number_of_options == 0 or number_of_decisions == 0:
        raise ValueError(
            f"Both number_of_options '{number_of_options}' and number_of_decisions '{number_of_options}' should be greater than 0."
        )
    logit_bias_weight = 100
    # 0-number_of_options
    logit_bias = {str(k): logit_bias_weight for k in range(15, 15 + number_of_options + 1)}

    if number_of_decisions > 1:
        # separator
        if not separator:
            separator = "\n"
        if len(seperator_token := text_utils.get_tokens(separator, llm_model_name)) > 1:
            raise ValueError(f"separator_token '{seperator_token}' should be a single token.")
        logit_bias[str(seperator_token[0])] = logit_bias_weight

    highest_option_tokens = text_utils.get_tokens(str(number_of_options), llm_model_name)
    if number_of_decisions == 1:
        max_tokens = len(highest_option_tokens)
    else:
        max_tokens = ((len(highest_option_tokens) + 1) * number_of_decisions) - 1

    return logit_bias, max_tokens


def create_logit_bias_prompt(
    features: list[str] | str,
    logit_bias: dict[str, int],
    logit_bias_response_tokens: int,
    prompt_string: Optional[str] = None,
    prompt_template_path: Optional[str] = None,
) -> tuple[str, str]:
    if not prompt_string and not prompt_template_path:
        raise ValueError("prompt_string and prompt_template_path cannot both be None.")
    if prompt_template_path:
        system_prompt = prompts.load_prompt_template(prompt_template_path)
    else:
        system_prompt = prompt_string
    if not isinstance(system_prompt, str):
        raise ValueError("prompt_template should be a string.")
    if not isinstance(features, list):
        features = [features]
