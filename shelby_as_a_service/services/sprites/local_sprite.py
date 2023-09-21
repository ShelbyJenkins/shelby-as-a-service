# region
import os
import asyncio
from concurrent.futures import ThreadPoolExecutor
import shutil
import gradio as gr
from services.log_service import Logger
from services.apps.app_management import AppManager
from models.app_base import AppBase
from models.service_models import LocalSpriteModel
from services.ceq_agent import CEQAgent

# endregion

class LocalSprite(AppBase):
    model_ = LocalSpriteModel()
    required_services_ = [CEQAgent]
    # required_services_ = [CEQAgent, IndexService]

    def __init__(self):
        """
        """
        super().__init__()
        self.setup_config(self)
        self.setup_services()

        self.log = Logger(
            self.app_name,
            "LocalSprite",
            "local_sprite.md",
            level="INFO",
        )
        
        self.index_service_ = self.app.index_service
        self.status_textbox_ = self._gradio_logging()
        self.existing_app_names_ = AppManager.check_for_existing_apps()
        self.global_components_ = {}

    async def _create_interface(self):
        """Creates gradio app."""
        try:
            with gr.Blocks() as local_client:
                self.status_textbox_ = gr.Textbox(
                    label="",
                    value="",
                    max_lines=2,
                )
                with gr.Tab(label="Chat"):
                    self._create_ceq_tab()
                with gr.Tab(label="Data Index"):
                    self._create_index_tab()
                with gr.Tab(label="Config"):
                    self._create_config_tab()

                self.log.print_and_log_gradio("LocalSprite launched")
                local_client.queue().launch()

        except Exception as error:
            output_message = f"Error: {error}"
            self.log.print_and_log_gradio(output_message)
        
        return local_client
    
    # Creates interface

    def _create_ceq_tab(self):
        with gr.Blocks() as config_interface:
            with gr.Tab(label="Context Enhanced Querying"):
                with gr.Column(variant="panel"):
                    ceq_chatbot = gr.Textbox(label="Chatbot", lines=20)
                    with gr.Group():
                        with gr.Row():
                            ceq_message_textbox = gr.Textbox(
                                container=False,
                                show_label=False,
                                label="Message",
                                placeholder="Type a message...",
                                scale=7,
                            )

                ceq_message_textbox.submit(
                    fn=self._run_ceq_request,
                    inputs=ceq_message_textbox,
                    outputs=[ceq_message_textbox, ceq_chatbot],
                )

            with gr.Tab(label="Settings"):
                self._create_settings_tab(self.ceq_agent)

        return config_interface

    def _create_index_tab(self):
        with gr.Blocks() as config_interface:
            with gr.Tab(label="Ingest Data"):
                with gr.Tab(label="Web Source"):
                    source_textbox = gr.Textbox(
                        placeholder="url_source or file path",
                        show_label=False,
                        label="Message",
                    )
                    index_ingest_docs = gr.Button(size="sm", value="ingest_docs")
                    self._create_settings_tab(self.index_service_)
                with gr.Tab(label="Local File"):
                    source_textbox = gr.Textbox(
                        placeholder="url_source or file path",
                        show_label=False,
                        label="Message",
                    )
                    index_ingest_docs = gr.Button(size="sm", value="ingest_docs")
                with gr.Tab(label="Log"):
                    index_ingest_docs = gr.Button(size="sm", value="ingest_docs")
            with gr.Tab(label="Manage Index"):
                index_delete_index = gr.Button(size="sm", value="delete_index")
                index_clear_index = gr.Button(size="sm", value="clear_index")
                # Drop down of providers
                index_create_index = gr.Button(size="sm", value="create_index")

            # Will need special function here to load this
            # with gr.Tab(label="Settings"):
            #     self._create_settings_tab(self.index_service_)

            # index_ingest_docs.click(
            #     fn=self.index_service_.ingest_docs,
            #     inputs=None,
            #     outputs=None,
            # )

        return config_interface

    def _create_config_tab(self):
        with gr.Blocks() as config_interface:
            with gr.Tab(label="Local Sprite"):
                self._create_settings_tab(self)

            with gr.Tab(label="Secrets"):
                with gr.Row():
                    gr.Textbox(
                        show_label=False, scale=2, lines=3, value="Instructions here"
                    )
                    with gr.Column(variant="panel"):
                        secrets_file_btn = gr.Button(
                            size="sm", value="Save Secrets to .env File"
                        )
                with gr.Row():
                    
                    secrets_components = self._create_secrets_components()
                    
                    secrets_file_btn.click(
                    fn=self._save_load_new_secrets,
                    inputs=secrets_components,
                    outputs=secrets_components,
                    ).then(
                        fn=self._gradio_logging,
                        inputs=None,
                        outputs=self.status_textbox_,
                    )
                    
            with gr.Tab(label="Management"):
                with gr.Row():
                    gr.Textbox(
                        show_label=False, lines=15, scale=2, value="Instructions here"
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
            #     outputs=config_blocks,
            #     ).then(
            #         fn=self._gradio_logging,
            #         inputs=None,
            #         outputs=self.status_textbox_,
            #         )

            make_app_btn.click(
                fn=self._create_new_app,
                inputs=make_app_textbox,
                outputs=[
                    make_app_textbox,
                    load_apps_dropdown,
                    delete_apps_dropdown,
                ],
            ).then(
                fn=self._gradio_logging,
                inputs=None,
                outputs=self.status_textbox_,
            )

            delete_app_btn.click(
                fn=self._delete_app,
                inputs=[delete_apps_dropdown, delete_app_chk_box],
                outputs=[
                    load_apps_dropdown,
                    delete_apps_dropdown,
                    delete_app_chk_box,
                ],
            ).then(
                fn=self._gradio_logging,
                inputs=None,
                outputs=self.status_textbox_,
            )

        return config_interface

    def _create_secrets_components(self):
        secrets_components = []

        for secret_name, secret in self.secrets.items():
            if secret in [None, ""]:
                placeholder = ""
            else:
                placeholder = "Secret loaded successfully."
            secret_component = gr.Textbox(
                            placeholder=placeholder,
                            label=secret_name,
                            elem_id=secret_name,
                            interactive=True,
                        )
            secrets_components.append(secret_component)
            
        self.global_components_['secrets'] = secrets_components
            
        return secrets_components

    
    # Used multiple times while creating interface

    def _create_settings_tab(self, class_instance):
        with gr.Blocks() as settings_interface:
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

                with gr.Row():
                    self._create_settings_components(
                        class_instance=class_instance,
                        class_name=class_instance.service_name_,
                    )

        config_memory_btn.click(
            fn=self._save_config_to_memory,
            inputs=self.global_components_[class_instance.service_name_],
            outputs=self.status_textbox_,
            )

   
        config_file_btn.click(
            fn=self._save_config_to_file,
            inputs=self.global_components_[class_instance.service_name_],
            outputs=self.status_textbox_,
        )

        return settings_interface

    def _create_settings_components(self, class_instance, class_name):
        settings_components = []
        
        txb = gr.Textbox(
                value=class_name,
                label=class_name,
                elem_id=class_name,
                elem_classes=class_name,
                interactive=False,
                visible=False,
            )
        settings_components.append(txb)
        
        with gr.Blocks(title=class_name) as settings_interface:
            with gr.Group():
                if len(class_instance.required_variables_) > 0:
                    with gr.Tab(
                        label=f"{class_name}_required_settings",
                        elem_id=f"{class_name}_required_settings",
                    ):
                        for var in class_instance.required_variables_:
                            req_var = getattr(class_instance, var)
                            txb = gr.Textbox(
                                value=req_var,
                                label=var,
                                elem_id=var,
                                elem_classes=class_name,
                                interactive=True,
                            )
                            settings_components.append(txb)
                            txb

                with gr.Tab(
                    label=f"{class_name}_optional_settings",
                    elem_id=f"{class_name}_optional_settings",
                ):
                    for var, value in class_instance.__dict__.items():
                        if AppManager.check_for_ignored_objects(
                            var
                        ) and AppManager.check_for_ignored_objects(value):
                            if var not in class_instance.required_variables_:
                                txb = gr.Textbox(
                                    value=value,
                                    label=var,
                                    elem_id=var,
                                    elem_classes=class_name,
                                    interactive=True,
                                )
                                settings_components.append(txb)
                                txb
                                
        self.global_components_[class_name] = settings_components
        
        return settings_interface

    # Interface functions
    
    def _save_config_to_memory(self, *settings_components):
        """Updates settings in memory using input from the gradio config_components.
        Takes  input from config_blocks, and sets the class using elem_classes field.
        Then uses the label field to set the attr with the value from the input.
        """
        class_components = self.global_components_[settings_components[0]]
        
        if settings_components[0] == 'local_sprite':
            class_instance = self
        else:
            class_instance = getattr(self, settings_components[0])
        
        for i, component in enumerate(settings_components):
            setattr(class_instance, class_components[i].elem_id, component)
            
        output_message = "Config settings saved to memory."
        self.log.print_and_log_gradio(output_message)

        return output_message

    def _save_config_to_file(self, *settings_components):
        self._save_config_to_memory(*settings_components)
        
        if settings_components[0] == 'local_sprite':
            class_instance = self
        else:
            class_instance = getattr(self, settings_components[0])
            
        AppManager.update_app_json_from_file(self.app, self.app.app_name, class_instance)
        output_message = "Config settings saved to file."

        self.log.print_and_log_gradio(output_message)

        return output_message

    def _save_load_new_secrets(self, *secrets_components):
       
        output_components = []
        for i, component in enumerate(self.global_components_['secrets']):
            if secrets_components[i] is not None and secrets_components[i] != "":
                self.secrets[component.elem_id] = secrets_components[i]
                output_components.append(component.update(placeholder="Secret loaded successfully.", value=""))
            else:
                output_components.append(component.update(value=""))

        AppManager.create_update_env_file(self.app.app_name, self.secrets)

        output_message = "Secrets saved to .env file and loaded into memory."
        self.log.print_and_log_gradio(output_message)

        return output_components

    # Needs to reload the entire app
    def _load_new_app_from_file(self, load_app_name=None):
        """Loads new app to app object."""

        self.existing_app_names_ = AppManager.check_for_existing_apps()

        if load_app_name is not None:
            if load_app_name not in self.existing_app_names_:
                output_message = f"Can't find a app named: '{load_app_name}'"
                self.log.print_and_log_gradio(output_message)
                return output_message
            if load_app_name == self.app_name:
                output_message = f"app already loaded: '{load_app_name}'"
                self.log.print_and_log_gradio(output_message)
                return output_message
            self.app.app_name = load_app_name

        self.app.setup_app_instance(self.app)
        self.app.setup_services()
        self.app.setup_sprites()
            
        
        output_message = f"app loaded: '{self.app.app_name}'"
        self.log.print_and_log_gradio(output_message)

        return output_message

    def _create_new_app(self, new_app_name):
        new_app_name = new_app_name.strip()

        if len(new_app_name) < 3:
            output_message = "Please enter a longer app name"
            self.log.print_and_log_gradio(output_message)
            
        elif not all(char.isalnum() or char == "_" for char in new_app_name):
            output_message = "Please only use alpha numeric chars and '_' chars."
            self.log.print_and_log_gradio(output_message)
        else:
            if not self.existing_app_names_:
                self.existing_app_names_ = AppManager.check_for_existing_apps()
            if new_app_name in self.existing_app_names_:
                output_message = "That app already exists. Please delete it first"
                self.log.print_and_log_gradio(output_message)
            else:
                AppManager().create_app(new_app_name)
                AppManager().update_app_json_from_file(self.app, new_app_name)
                self.existing_app_names_ = AppManager.check_for_existing_apps()
                output_message = f" app '{new_app_name}' created"
                self.log.print_and_log_gradio(output_message)

        return (
            gr.Textbox.update(
                value=""
            ),
            gr.Dropdown.update(
                value=self.existing_app_names_[0],
                choices=self.existing_app_names_,
            ),
            gr.Dropdown.update(value="Danger!", choices=self.existing_app_names_),
        )

    def _delete_app(self, delete_app_name, delete_app_chk_box):
        if delete_app_name == self.app_name:
            output_message = "Can't delete in use app. Please switch first."
            self.log.print_and_log_gradio(output_message)
        elif delete_app_chk_box is False:
            output_message = "Please check check the box to confirm delete"
            self.log.print_and_log_gradio(output_message)
        else:
            base_dir = "apps"

            app_path = os.path.join(base_dir, delete_app_name)
            if os.path.exists(app_path):
                try:
                    shutil.rmtree(app_path)
                    output_message = f"Successfully deleted app: '{delete_app_name}'"
                    self.log.print_and_log_gradio(output_message)
                except Exception as error:
                    output_message = (
                        f"Error deleting app: '{delete_app_name}'. Error: {str(error)}"
                    )
                    self.log.print_and_log_gradio(output_message)
            else:
                output_message = f"app: '{delete_app_name}' not found."
                self.log.print_and_log_gradio(output_message)

            self.existing_app_names_ = AppManager.check_for_existing_apps()

        return (
            gr.Dropdown.update(choices=self.existing_app_names_),
            gr.Dropdown.update(value="Danger!", choices=self.existing_app_names_),
            gr.Checkbox.update(value=False),
        )

    # App functionality
    
    async def _run_ceq_request(self, request):
        # Required to run multiple requests at a time in async
        with ThreadPoolExecutor() as executor:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                executor, self.ceq_agent.request_thread, request
            )
            return "", response

    def _gradio_logging(self):
        output = self.log.read_logs()
        return output

    def run_sprite(self):
        try:
            asyncio.run(self._create_interface())
        except Exception as error:
            output_message = f"Error: {error}"
            self.log.print_and_log_gradio(output_message)
