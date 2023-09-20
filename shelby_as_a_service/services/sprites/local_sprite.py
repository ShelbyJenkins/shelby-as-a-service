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
        """Sprites are initialized through a app.
        setup_config sets services as instance attrs.
        It uses their service_name from model.
        So CEQAgent can be accessed with self.ceq_agent.
        """
        super().__init__()
        self.setup_config()
        self.setup_services()
   
        # self.config_components, self.config_dict, self.secrets_components = self._create_config_components()
        self.index_service = self.app.index_service
        
        self.log = Logger(
            self.app_name,
            "LocalSprite",
            "local_sprite.md",
            level="INFO",
        )

    async def _create_interface(self):
        """Creates gradio app."""
        try:
            with gr.Blocks() as local_client:
                with gr.Tab(label="Chat"):
                    self._create_ceq_tab()
                with gr.Tab(label="Index Management"):
                    self._create_index_tab()
                with gr.Tab(label="Config"):
                    self._create_config_tab()
                with gr.Tab(label="Logs", id="log"):
                    self._create_logging_tab()
        
                self.log.print_and_log_gradio("LocalSprite launched")
                local_client.queue().launch()

        except Exception as error:
            output_message = f"Error: {error}"
            self.log.print_and_log_gradio(output_message)

        return local_client
    
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
            with gr.Tab(label="Manage Index"):
                index_ingest_docs = gr.Button(size='sm', value="ingest_docs")
                index_delete_index = gr.Button(size='sm', value="delete_index")
                index_clear_index = gr.Button(size='sm', value="clear_index")
                index_create_index = gr.Button(size='sm', value="create_index")
                
            # Will need special function here to load this
            # with gr.Tab(label="Settings"):
            #     self._create_settings_tab(self.index_service)
            
            # index_ingest_docs.click(
            #     fn=self.index_service.ingest_docs,
            #     inputs=None,
            #     outputs=None,
            # )
        
        return config_interface
    
    def _create_config_tab(self):
        with gr.Blocks() as config_interface:
            
            with gr.Tab(label="Settings"):
                self._create_settings_tab(self)
                
            with gr.Tab(label="Secrets"):
                with gr.Row():
                    gr.Textbox(show_label=False, scale=2, lines=3, value="Instructions here")
                    with gr.Column(variant='panel'):
                        secrets_file_btn = gr.Button(size='sm', value="Save Secrets to .env File")
                with gr.Row():
                    secrets_components, secrets_blocks = self._create_secrets_tab()
 
            with gr.Tab(label="Management"):
                with gr.Row():
                    gr.Textbox(show_label=False, lines=15, scale=2, value="Instructions here")
                    with gr.Column(variant='panel'):
                        with gr.Group():
                            load_apps_dropdown = gr.Dropdown(
                                value=AppManager.check_for_existing_apps()[0],
                                multiselect=False,
                                choices=AppManager.check_for_existing_apps(),
                                label="Load Existing app",
                            )
                            load_app_btn = gr.Button(size='sm', 
                                value="Load"
                            )
                        with gr.Group():
                            make_app_textbox = gr.Textbox(
                                label="Create new app",
                                placeholder='<your_new_app_name>'
                            )
                            make_app_btn = gr.Button(size='sm', 
                                value="Create"
                            )
                        with gr.Group():
                            with gr.Group():
                                delete_apps_dropdown = gr.Dropdown(
                                    value="Danger!",
                                    multiselect=False,
                                    choices=AppManager.check_for_existing_apps(),
                                    label="Delete Existing app",
                                )
                                delete_app_chk_box = gr.Checkbox(
                                    value=False,
                                    label="Check to confirm",
                                )
                                delete_app_btn = gr.Button(size='sm', 
                                    value="Delete"
                                )
       
            secrets_file_btn.click(
                fn=self._save_load_new_secrets,
                inputs=secrets_blocks,
                outputs=secrets_blocks,
            )
            
            # load_app_btn.click(
            #     fn=self._load_new_app_from_file,
            #     inputs=load_apps_dropdown,
            #     outputs=config_blocks,
            # )
            # make_app_btn.click(
            #     fn=self._create_new_app,
            #     inputs=make_app_textbox,
            #     outputs=[
            #         config_status_textboxt,
            #         make_app_textbox,
            #         load_apps_dropdown,
            #         delete_apps_dropdown,
            #     ],
            # )
            # delete_app_btn.click(
            #     fn=self._delete_app,
            #     inputs=[delete_apps_dropdown, delete_app_chk_box],
            #     outputs=[
            #         config_status_textboxt,
            #         load_apps_dropdown,
            #         delete_apps_dropdown,
            #         delete_app_chk_box,
            #     ],
            # )
                                
        return config_interface
    
    def _create_secrets_tab(self):
        
        secrets_blocks = []
        
        with gr.Blocks() as secrets_components:
            with gr.Row():
                for secret_name, secret in self.secrets.items():
                    if secret in [None, '']:
                        placeholder = ''
                    else:
                        placeholder = 'Secret loaded successfully.'
                    txb = gr.Textbox(
                        placeholder=placeholder, label=secret_name, elem_id=secret_name, interactive=True,
                    )
                    secrets_blocks.append(txb)
                    txb
                    
        return secrets_components, secrets_blocks
    
    def _create_logging_tab(self):
        with gr.Blocks() as config_interface:
            with gr.Row():
                logs_output = gr.Textbox(
                    value="Logs will appear here...",
                    lines=30,
                )
            config_interface.load(
                    fn=self._gradio_logging, inputs=None, outputs=logs_output, every=3
                )
            
        return config_interface
    
    
    def _create_settings_tab(self, class_name):
        
        with gr.Blocks() as config_interface:
            config_status_textboxt = gr.Textbox(
                label="",
                value="A sprite is a wily interface for interacting with AI.",
            )
            with gr.Tab(label="settings"):
                with gr.Row():
                    gr.Textbox(show_label=False, scale=2, lines=5, value="Instructions here")
                    with gr.Column(variant='panel'):
                        config_memory_btn = gr.Button(size='sm', value="Save Config to Memory") 
                        config_revert_btn = gr.Button(size='sm', value="Revert Config from File")
                        config_file_btn = gr.Button(size='sm', value="Save Config to File")
                        
                with gr.Row():
                    settings_components, settings_blocks = self._create_components_from_classes(
                        class_config=class_name,
                        class_name=class_name.service_name_,
                    )
            
            config_memory_btn.click(
                fn=self._save_config_to_memory,
                inputs=settings_blocks,
                outputs=config_status_textboxt,
            )
            config_revert_btn.click(
                fn=self._load_new_app_from_file,
                inputs=None,
                outputs=settings_blocks,
            )
            config_file_btn.click(
                fn=self._save_config_to_file,
                inputs=settings_blocks,
                outputs=config_status_textboxt,
            )
  
                                
        return config_interface
    
    def _create_components_from_classes(self, class_config, class_name):
        settings_blocks = []
        
        with gr.Blocks(title=class_name) as settings_components:
            with gr.Group():
                if len(class_config.required_variables_) > 0:
                    with gr.Tab(
                        label=f"{class_name}_required_settings",
                        elem_id=f"{class_name}_required_settings",
                    ):
                        for var in class_config.required_variables_:
                            req_var = getattr(class_config, var)
                            id = f"{class_name}_{var}"
                            txb = gr.Textbox(
                                value=req_var, label=var, elem_id=id, elem_classes=class_name, interactive=True
                            )
                            settings_blocks.append(txb)
                            txb
                            
                with gr.Tab(
                    label=f"{class_name}_optional_settings",
                    elem_id=f"{class_name}_optional_settings",
                ):
                    for name, value in class_config.__dict__.items():
                        # if (
                        #     not name.startswith("__")
                        #     and not callable(value)
                        #     and not isinstance(value, AppBase)
                        #     and not isinstance(value, type)
                        #     and not isinstance(value, Logger)
                        #     and not name.endswith("_")
                        #     and name != 'app_name'
                        #     and name != 'secrets'
                        # )

                        if AppManager.check_for_ignored_objects(
                            name
                            ) and AppManager.check_for_ignored_objects(value):
                            
                            id = f"{class_name}_{name}"
                            if name not in class_config.required_variables_:
                                txb = gr.Textbox(
                                    value=value,
                                    label=name,
                                    elem_id=id,
                                    elem_classes=class_name,
                                    interactive=True,
                                )
                                settings_blocks.append(txb)
                                txb
                            

        return settings_components, settings_blocks
    
    
    def _save_config_to_memory(self, *config_blocks):
        """Updates settings in memory using input from the gradio config_components.
        Takes  input from config_blocks, and sets the class using elem_classes field.
        Then uses the label field to set the attr with the value from the input.
        """
        counter = 0
        for _, block in self.config_components.blocks.items():
            if block.elem_id is not None and hasattr(block, 'value'):
                instance_name = block.elem_classes[0]
                if instance_name == 'local_sprite':
                    setattr(self, block.label, config_blocks[counter])
                else:
                    class_instance = getattr(self, instance_name)
                    setattr(class_instance, block.label, config_blocks[counter])
                counter += 1
        output_message = "Config settings saved to memory."
        self.log.print_and_log_gradio(output_message)
        
        return output_message
    
    def _save_config_to_file(self, *config_blocks):
        self._save_config_to_memory(*config_blocks)
        AppManager.update_app_json_from_memory(self.app, self.app_name)
        output_message = "Config settings saved to file."
            
        self.log.print_and_log_gradio(output_message)
        
        return output_message
    
    def _save_load_new_secrets(self, *secrets_blocks):    
                    
        counter = 0
        output = []
        for _, block in self.secrets_components.blocks.items():
            if block.elem_id is not None and hasattr(block, 'value'):
                value = secrets_blocks[counter]
                if value is not None and value != '': 
                    self.secrets[block.elem_id] = value
                output.append('')
                counter += 1
                    
        AppManager.create_update_env_file(self.app_name, self.secrets)
        
        output_message = "Secrets saved to .env file and loaded into memory."
        self.log.print_and_log_gradio(output_message)
        
        return output
    
    def _load_new_app_from_file(self, load_app_name = None):
        """Loads new app to app object."""

        self.existing_app_names = AppManager.check_for_existing_apps()

        if load_app_name is not None:
            if load_app_name not in self.existing_app_names:
                output_message = f"Can't find a app named: '{load_app_name}'"
                self.log.print_and_log_gradio(output_message)
                return None
            if load_app_name == self.app_name:
                output_message = f"app already loaded: '{load_app_name}'"
                self.log.print_and_log_gradio(output_message)
                return None
            self.app_name = load_app_name

        
        AppManager.update_app_json_from_model(self.app, self.app_name)
        self.setup_config()
        
        output = []
        for _, block in self.config_components.blocks.items():
            if block.elem_id is not None and hasattr(block, 'value'):
                output.append(block.update(value = self.config_dict.get(block.elem_id, None)))
        
        output_message = f"app loaded: '{self.app_name}'"
        self.log.print_and_log_gradio(output_message)
        
        return output
     
    def _create_new_app(self, new_app_name):
        
        new_app_name = new_app_name.strip()
        
        if len(new_app_name) < 3:
            output_message = "Please enter a longer app name"
            self.log.print_and_log_gradio(output_message)
            return
        elif not all(char.isalnum() or char == "_" for char in new_app_name):
            output_message = "Please only use alpha numeric chars and '_' chars."
            self.log.print_and_log_gradio(output_message)
            return
        if not self.existing_app_names:
            self.existing_app_names = (
                AppManager.check_for_existing_apps()
            )
        if new_app_name in self.existing_app_names:
            output_message = "That app already exists. Please delete it first"
            self.log.print_and_log_gradio(output_message)
            return
        else:
            AppManager().create_app(new_app_name)
            AppManager().update_app_json_from_model(self.app, new_app_name)
            self.existing_app_names = (
                AppManager.check_for_existing_apps()
            )
            output_message = f" app '{new_app_name}' created"
            self.log.print_and_log_gradio(output_message)

        return (
            output_message,
            gr.Textbox.update(value=""),
            gr.Dropdown.update(
                value=self.existing_app_names[0],
                choices=self.existing_app_names,
            ),
            gr.Dropdown.update(value="Danger!", choices=self.existing_app_names),
        )

    def _delete_app(self, delete_app_name, delete_app_chk_box):
        if delete_app_name == self.app_name:
            output_message = "Can't delete in use app. Please switch first."
            self.log.print_and_log_gradio(output_message)
        elif delete_app_chk_box is False:
            output_message = "Please check check the box to confirm delete"
            self.log.print_and_log_gradio(output_message)
        else:
            base_dir = "shelby_as_a_service/apps"

            app_path = os.path.join(base_dir, delete_app_name)
            if os.path.exists(app_path):
                try:
                    shutil.rmtree(app_path)
                    output_message = (
                        f"Successfully deleted app: '{delete_app_name}'"
                    )
                    self.log.print_and_log_gradio(output_message)
                except Exception as error:
                    output_message = f"Error deleting app: '{delete_app_name}'. Error: {str(error)}"
                    self.log.print_and_log_gradio(output_message)
            else:
                output_message = f"app: '{delete_app_name}' not found."
                self.log.print_and_log_gradio(output_message)

            self.existing_app_names = AppManager.check_for_existing_apps()

        return (
            output_message,
            gr.Dropdown.update(
                value=self.existing_app_names[0],
                choices=self.existing_app_names,
            ),
            gr.Dropdown.update(value="Danger!", choices=self.existing_app_names),
            gr.Radio.update(
                value="Don't Delete",
                choices=["Don't Delete", "Check to Confirm Delete"],
            ),
        )

    async def _run_ceq_request(self, request):
        # Required to run multiple requests at a time in async
        with ThreadPoolExecutor() as executor:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                executor, self.ceq_agent.request_thread, request
            )
            return "", response

    def _gradio_logging(self):
        return self.log.read_logs()

    def run_sprite(self):
        try:
            asyncio.run(self._create_interface())
        except Exception as error:
            output_message = f"Error: {error}"
            self.log.print_and_log_gradio(output_message)
