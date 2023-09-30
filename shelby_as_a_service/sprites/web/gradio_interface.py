import gradio as gr
from sprites.web.gradio_themes import AtYourServiceTheme
from services.llm_service import LLMService, OpenAILLM
import modules.utils.config_manager as ConfigManager

ui_comp = {}


def create_interface(self):
    """Creates gradio app."""

    with gr.Blocks(theme=AtYourServiceTheme()) as local_client:
        with gr.Tab("Vanillm Chat", elem_id="default-tab"):
            with gr.Tab("Chat", elem_id="default-tab"):
                create_chat_ui("vanillm")

        with gr.Tab("Web Chat", elem_id="default-tab"):
            with gr.Tab("Chat", elem_id="default-tab"):
                create_chat_ui("simple")

        with gr.Tab("Data Chat", elem_id="default-tab"):
            with gr.Tab("Context Enhanced Querying", elem_id="default-tab"):
                create_chat_ui("ceq_agent")
            with gr.Tab("Add Data", elem_id="default-tab"):
                create_index_config(self)
                with gr.Tab("email", elem_id="default-tab"):
                    pass
                with gr.Tab("local", elem_id="default-tab"):
                    pass
                with gr.Tab("web", elem_id="default-tab"):
                    pass

        with gr.Tab("Build Bots and Websites", elem_id="default-tab"):
            create_chat_ui("ceq_agent")

        with gr.Tab("Config", elem_id="default-tab"):
            create_chat_ui("ceq_agent")

        # create_index_ui(self)
        # create_web_settings_ui(self)
        local_client.queue()
        local_client.launch()


def create_chat_ui(agent_type):
    ui_comp[agent_type] = {}

    with gr.Row():
        with gr.Column(scale=4):
            with gr.Row():
                ui_comp[agent_type]["output_textbox"] = gr.Textbox(
                    lines=27,
                    label="output_textbox",
                    show_label=False,
                    interactive=False,
                    elem_id="output_textbox",
                )

            with gr.Row():
                ui_comp[agent_type]["input_textbox"] = gr.Textbox(
                    label="input_textbox",
                    show_label=False,
                    placeholder="Send a message",
                    elem_id="input_textbox",
                )

            with gr.Row():
                ui_comp[agent_type]["generate_button"] = gr.Button(
                    "generate", variant="primary"
                )

        with gr.Column():
            ui_comp[agent_type]["llm_provider"] = gr.Dropdown(
                choices=LLMService.ui_provider_names,
                value=LLMService.ui_provider_names[0],
                label="LLM Provider",
            )

            ui_comp[agent_type]["llm_Model"] = gr.Dropdown(
                choices=OpenAILLM.ui_model_names,
                value=OpenAILLM.ui_model_names[0],
                label="LLM Model",
            )

    # create_chat_event_handlers(agent_type)


# def run_chat(input, llm_provider, llm_model):
#     if ceq_radio:
#         yield from self.ceq_agent.run_context_enriched_query(
#             input, stream=True, provider_name=llm_provider, model_name=llm_model
#         )
#     else:
#         yield from self.vanilla_agent.create_streaming_chat(
#             input, provider_name=llm_provider, model_name=llm_model
#         )


# def create_chat_event_handlers(agent_type):

#     ui_comp[agent_type]["input_textbox"].submit(
#         fn=run_chat,
#         inputs=[
#             ui_comp[agent_type]["input_textbox"],
#             ui_comp[agent_type]["llm_provider"],
#             ui_comp[agent_type]["llm_Model"],
#         ],
#         outputs=ui_comp[agent_type]["output_textbox"],
#     )
#     ui_comp[agent_type]["generate_button"].click(
#         fn=run_chat,
#         inputs=[
#             ui_comp[agent_type]["input_textbox"],
#             ui_comp[agent_type]["llm_provider"],
#             ui_comp[agent_type]["llm_Model"],
#         ],
#         outputs=ui_comp[agent_type]["output_textbox"],
#     )


def create_index_config(self):
    settings_components = []

    index_instance = self.index
    index_name = index_instance.index_name
    data_domain_instance = index_instance.index_data_domains[0]
    data_domain_name = data_domain_instance.data_domain_name
    data_domain_names = [
        domain.data_domain_name for domain in index_instance.index_data_domains
    ]
    source_instance = data_domain_instance.data_domain_sources[0]
    data_source_name = source_instance.data_source_name
    data_source_names = [
        source.data_source_name for source in data_domain_instance.data_domain_sources
    ]

    txb = gr.Textbox(
        value="index",
        label="index",
        elem_id="index",
        elem_classes="index",
        interactive=False,
        visible=False,
    )

    with gr.Blocks():
        with gr.Row():
            gr.Textbox(show_label=False, scale=2, lines=3, value="Instructions here")
            with gr.Column(variant="panel"):
                config_memory_btn = gr.Button(size="sm", value="Save Config to Memory")
                config_file_btn = gr.Button(size="sm", value="Save Config to File")

        with gr.Group():
            with gr.Tab(label=f"Selected Index: {index_name}"):
                index_name_dropdown = gr.Dropdown(
                    value=index_name,
                    choices=index_name,
                    label="Index Name",
                    elem_id="index_name",
                    elem_classes="index",
                    multiselect=False,
                    interactive=True,
                )
                with gr.Tab(label=f"Selcted Data Domain: {data_domain_name}"):
                    txb = gr.Dropdown(
                        value=data_domain_name,
                        choices=data_domain_names,
                        label="Data Domain Name",
                        elem_id="data_domain_name",
                        elem_classes="index",
                        multiselect=False,
                        interactive=True,
                    )

                    with gr.Tab(label=f"Selected Data Source: {data_source_name}"):
                        txb = gr.Dropdown(
                            value=data_source_name,
                            choices=data_source_names,
                            label="Data Source Name",
                            elem_id="data_source_name",
                            elem_classes="index",
                            multiselect=False,
                            interactive=True,
                        )

                    with gr.Tab(label="Rename Selected Data Source"):
                        make_app_textbox = gr.Textbox(
                            placeholder="<your_new_data_source_name>",
                            container=True,
                        )
                        with gr.Row():
                            delete_app_chk_box = gr.Checkbox(
                                value=False,
                                label="Check to confirm",
                                container=True,
                            )
                            make_app_btn = gr.Button(
                                size="sm", value="Rename", container=True
                            )
                    with gr.Tab(label="Clear Selected Data Source"):
                        with gr.Row():
                            delete_app_chk_box = gr.Checkbox(
                                value=False,
                                label="Check to confirm",
                                container=True,
                            )
                            delete_app_btn = gr.Button(
                                size="sm", value="Clear", container=True
                            )
                    with gr.Tab(label="Delete Selected Data Source"):
                        with gr.Row():
                            delete_app_chk_box = gr.Checkbox(
                                value=False,
                                label="Check to confirm",
                                container=True,
                            )
                            delete_app_btn = gr.Button(
                                size="sm", value="Delete", container=True
                            )
                    with gr.Tab(label="Create New Data Source"):
                        make_app_textbox = gr.Textbox(
                            placeholder="<your_new_data_source_name>",
                            container=True,
                        )
                        with gr.Row():
                            delete_app_chk_box = gr.Checkbox(
                                value=False,
                                label="Check to confirm",
                                container=True,
                            )
                            make_app_btn = gr.Button(
                                size="sm", value="Create", container=True
                            )

                with gr.Tab(label="Rename Selected Data Domain"):
                    make_app_textbox = gr.Textbox(
                        placeholder="<your_new_data_domain_name>",
                        container=True,
                    )
                    with gr.Row():
                        delete_app_chk_box = gr.Checkbox(
                            value=False,
                            label="Check to confirm",
                            container=True,
                        )
                        make_app_btn = gr.Button(
                            size="sm", value="Rename", container=True
                        )
                with gr.Tab(label="Clear Selected Data Domain"):
                    with gr.Row():
                        Clear_app_chk_box = gr.Checkbox(
                            value=False,
                            label="Check to confirm",
                            container=True,
                        )
                        Clear_app_btn = gr.Button(
                            size="sm", value="Clear", container=True
                        )
                with gr.Tab(label="Delete Selected Data Domain"):
                    with gr.Row():
                        delete_app_chk_box = gr.Checkbox(
                            value=False,
                            label="Check to confirm",
                            container=True,
                        )
                        delete_app_btn = gr.Button(
                            size="sm", value="Delete", container=True
                        )
                with gr.Tab(label="Create New Data Domain"):
                    make_app_textbox = gr.Textbox(
                        placeholder="<your_new_data_domain_name>",
                        container=True,
                    )
                    with gr.Row():
                        delete_app_chk_box = gr.Checkbox(
                            value=False,
                            label="Check to confirm",
                            container=True,
                        )
                        make_app_btn = gr.Button(
                            size="sm", value="Create", container=True
                        )

            with gr.Tab(label="Rename Selected Index"):
                make_app_textbox = gr.Textbox(
                    placeholder="<your_new_index_name>",
                    container=True,
                )
                with gr.Row():
                    delete_app_chk_box = gr.Checkbox(
                        value=False,
                        label="Check to confirm",
                        container=True,
                    )
                    make_app_btn = gr.Button(size="sm", value="Rename", container=True)
            with gr.Tab(label="Clear Selected Index"):
                with gr.Row():
                    Clear_app_chk_box = gr.Checkbox(
                        value=False,
                        label="Check to confirm",
                        container=True,
                    )
                    Clear_app_btn = gr.Button(size="sm", value="Clear", container=True)
            with gr.Tab(label="Delete Selected Index"):
                with gr.Row():
                    delete_app_chk_box = gr.Checkbox(
                        value=False,
                        label="Check to confirm",
                        container=True,
                    )
                    delete_app_btn = gr.Button(
                        size="sm", value="Delete", container=True
                    )

        # index_name_dropdown.change()


def create_index_ui(self):
    with gr.Tab(label="Data Index"):
        with gr.Tab(label="Index Config"):
            create_index_config(self)

        with gr.Tab(label="Web Source"):
            source_textbox = gr.Textbox(
                placeholder="url_source or file path",
                show_label=False,
                label="Message",
            )
            index_ingest_docs = gr.Button(size="sm", value="ingest_docs")
            # index_components = create_settings_components(self, self.index)
        with gr.Tab(label="Local File"):
            source_textbox = gr.Textbox(
                placeholder="url_source or file path",
                show_label=False,
                label="Message",
            )
            index_ingest_docs = gr.Button(size="sm", value="ingest_docs")
        with gr.Tab(label="Log"):
            index_ingest_docs = gr.Button(size="sm", value="ingest_docs")


def create_secrets_components(self):
    secrets_components = []

    # for secret_name, secret in self.app.secrets.items():
    #     if secret in [None, ""]:
    #         placeholder = ""
    #     else:
    #         placeholder = "Secret loaded successfully."
    #     secret_component = gr.Textbox(
    #         placeholder=placeholder,
    #         label=secret_name,
    #         elem_id=secret_name,
    #         interactive=True,
    #     )
    #     secrets_components.append(secret_component)
    # self.global_components_["secrets"] = secrets_components

    return secrets_components


def create_web_settings_ui(self):
    with gr.Tab(label="Config"):
        #     config_components = create_settings_components(self)

        with gr.Tab(label="Secrets"):
            with gr.Row():
                gr.Textbox(
                    show_label=False,
                    scale=2,
                    lines=3,
                    value="Instructions here",
                )
                with gr.Column(variant="panel"):
                    secrets_file_btn = gr.Button(
                        size="sm", value="Save Secrets to .env File"
                    )
            with gr.Row():
                secrets_components = create_secrets_components(self)

                # secrets_file_btn.click(
                #     fn=self._save_load_new_secrets,
                #     inputs=secrets_components,
                #     outputs=secrets_components,
                # )

        with gr.Tab(label="Management"):
            with gr.Row():
                gr.Textbox(
                    show_label=False,
                    lines=15,
                    scale=2,
                    value="Instructions here",
                )
                with gr.Column(variant="panel"):
                    with gr.Group():
                        load_apps_dropdown = gr.Dropdown(
                            value=self.existing_app_names_[0],
                            multiselect=False,
                            choices=self.existing_app_names_,
                            label="Load Existing app",
                        )
                        load_app_btn = gr.Button(size="sm", value="Load")
                    with gr.Group():
                        make_app_textbox = gr.Textbox(
                            label="Create new app",
                            placeholder="<your_new_app_name>",
                        )
                        make_app_btn = gr.Button(size="sm", value="Create")
                    with gr.Group():
                        with gr.Group():
                            delete_apps_dropdown = gr.Dropdown(
                                value="Danger!",
                                multiselect=False,
                                choices=self.existing_app_names_,
                                label="Delete Existing app",
                            )
                            delete_app_chk_box = gr.Checkbox(
                                value=False,
                                label="Check to confirm",
                            )
                            delete_app_btn = gr.Button(size="sm", value="Delete")

                    # load_app_btn.click(
                    #     fn=self._load_new_app_from_file,
                    #     inputs=load_apps_dropdown,
                    #     outputs=None,
                    # ).success(
                    #     fn=self._update_ui_settings_components,
                    #     inputs=ceq_components,
                    #     outputs=ceq_components,
                    # ).success(
                    #     fn=self._update_ui_settings_components,
                    #     inputs=index_components,
                    #     outputs=index_components,
                    # ).success(
                    #     fn=self._update_ui_settings_components,
                    #     inputs=config_components,
                    #     outputs=config_components,
                    # )

                    # make_app_btn.click(
                    #     fn=self._create_new_app,
                    #     inputs=make_app_textbox,
                    #     outputs=[
                    #         make_app_textbox,
                    #         load_apps_dropdown,
                    #         delete_apps_dropdown,
                    #     ],
                    # )

                    # delete_app_btn.click(
                    #     fn=self._delete_app,
                    #     inputs=[delete_apps_dropdown, delete_app_chk_box],
                    #     outputs=[
                    #         load_apps_dropdown,
                    #         delete_apps_dropdown,
                    #         delete_app_chk_box,
                    #     ],
                    # )

            # reate_settings_tab(self, class_instance):
            # class_name = class_instance.service_name_

            with gr.Blocks():
                with gr.Row():
                    gr.Textbox(
                        show_label=False, scale=2, lines=3, value="Instructions here"
                    )
                    with gr.Column(variant="panel"):
                        config_memory_btn = gr.Button(
                            size="sm", value="Save Config to Memory"
                        )
                        config_file_btn = gr.Button(
                            size="sm", value="Save Config to File"
                        )

                # with gr.Row():
                #     with gr.Group():
                # settings_components = self._create_settings_components(
                #     class_instance
                # )

        #     config_memory_btn.click(
        #         fn=self._save_config_to_memory,
        #         inputs=self.global_components_["settings_components"][class_name],
        #         outputs=None,
        #     )

        #     config_file_btn.click(
        #         fn=self._save_config_to_file,
        #         inputs=self.global_components_["settings_components"][class_name],
        #         outputs=None,
        #     )

        # return settings_components


# def create_settings_components(self, class_instance):
#     class_name = class_instance.service_name
#     settings_components = []

#     txb = gr.Textbox(
#         value=class_name,
#         label=class_name,
#         elem_id=class_name,
#         elem_classes=class_name,
#         interactive=False,
#         visible=False,
#     )
#     settings_components.append(txb)
#     if len(class_instance.required_variables_) > 0:
#         with gr.Tab(
#             label=f"{class_name}_required_settings",
#             elem_id=f"{class_name}_required_settings",
#         ):
#             for var in class_instance.required_variables_:
#                 req_var = getattr(class_instance, var)
#                 txb = gr.Textbox(
#                     value=req_var,
#                     label=var,
#                     elem_id=var,
#                     elem_classes=class_name,
#                     interactive=True,
#                 )
#                 settings_components.append(txb)
#                 txb

#     with gr.Tab(
#         label=f"{class_name}_optional_settings",
#         elem_id=f"{class_name}_optional_settings",
#     ):
#         for var, value in class_instance.__dict__.items():
#             if ConfigManager.check_for_ignored_objects(
#                 var
#             ) and ConfigManager.check_for_ignored_objects(value):
#                 if var not in class_instance.required_variables_:
#                     txb = gr.Textbox(
#                         value=value,
#                         label=var,
#                         elem_id=var,
#                         elem_classes=class_name,
#                         interactive=True,
#                     )
#                     settings_components.append(txb)
#                     txb

#     if "settings_components" not in self.global_components_:
#         self.global_components_["settings_components"] = {}
#     self.global_components_["settings_components"][class_name] = settings_components

#     return settings_components
