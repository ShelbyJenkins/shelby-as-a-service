class APIAgent:

    ### APIAgent makes API calls on behalf the user ###
    # Currently under development

    def __init__(self, ceq_agent, log_service, config):

        self.ceq_agent = ceq_agent
        # self.log = log_service
        self.config = config

    # Selects the correct API and endpoint to run action on.
    # Eventually, we should create a merged file that describes all available API.
    def select_API_operationID(self, query):

        API_spec_path = self.API_spec_path
        # Load prompt template to be used with all APIs
        with open(os.path.join('shelby_as_service/prompt_templates/', 'action_topic_constraint.yaml'), 'r', encoding="utf-8") as stream:
            # Load the YAML data and print the result
            prompt_template = yaml.safe_load(stream)
        operationID_file = None
        # Iterates all OpenAPI specs in API_spec_path directory,
        # and asks LLM if the API can satsify the request and if so which document to return
        for entry in os.scandir(API_spec_path):
            if entry.is_dir():
                # Create prompt
                with open(os.path.join(entry.path, 'LLM_OAS_keypoint_guide_file.txt'), 'r', encoding="utf-8") as stream:
                    keypoint = yaml.safe_load(stream)
                    prompt_message  = "query: " + query + " spec: " + keypoint
                    for role in prompt_template:
                        if role['role'] == 'user':
                            role['content'] = prompt_message

                    logit_bias_weight = 100
                    # 0-9
                    logit_bias = {str(k): logit_bias_weight for k in range(15, 15 + 5 + 1)}
                    # \n
                    logit_bias["198"] = logit_bias_weight
                    # x
                    logit_bias["87"] = logit_bias_weight

                    # Creates a dic of tokens that are the only acceptable answers
                    # This forces GPT to choose one.

                    response = openai.ChatCompletion.create(
                        model=self.select_operationID_llm_model,
                        messages=prompt_template,
                        # 5 tokens when doc_number == 999
                        max_tokens=5,
                        logit_bias=logit_bias,
                        stop='x'
                    )
            operation_response = self.ceq_agent.check_response(response)
            if not operation_response:
                return None

            # need to check if there are no numbers in answer
            if 'x' in operation_response or operation_response == '':
                # Continue until you find a good operationID.
                continue
            else:
                digits = operation_response.split('\n')
                number_str = ''.join(digits)
                number = int(number_str)
                directory_path = f"data/minified_openAPI_specs/{entry.name}/operationIDs/"
                for filename in os.listdir(directory_path):
                    if filename.endswith(f"-{number}.json"):
                        with open(os.path.join(directory_path, filename), 'r', encoding="utf-8") as f:
                            operationID_file = json.load(f)
self.log.print_and_log(f"operationID_file found: {os.path.join(directory_path, filename)}.")
                        break
                break
        if operationID_file is None:
self.log.print_and_log("No matching operationID found.")

        return operationID_file

    def create_bodyless_function(self, query, operationID_file):

        with open(os.path.join('shelby_as_service/prompt_templates/', 'action_topic_constraint.yaml'), 'r', encoding="utf-8") as stream:
            # Load the YAML data and print the result
            prompt_template = yaml.safe_load(stream)

        prompt_message  = "user_request: " + query
        prompt_message  += f"\nurl: " + operationID_file['metadata']['server_url'] + " operationid: " + operationID_file['metadata']['operation_id']
        prompt_message  += f"\nspec: " + operationID_file['context']
        for role in prompt_template:
            if role['role'] == 'user':
                role['content'] = prompt_message

        response = openai.ChatCompletion.create(
                        model=self.create_function_llm_model,
                        messages=prompt_template,
                        max_tokens=500,
                    )
        url_response = self.ceq_agent.check_response(response)
        if not url_response:
            return None

        return url_response

    def run_API_agent(self, query):

self.log.print_and_log(f"new action: {query}")
        operationID_file = self.select_API_operationID(query)
        # Here we need to run a doc_agent query if operationID_file is None
        function = self.create_bodyless_function(query, operationID_file)
        # Here we need to run a doc_agent query if url_maybe does not parse as a url

        # Here we need to run a doc_agent query if the function doesn't run correctly

        # Here we send the request to GPT to evaluate the answer

        return response
