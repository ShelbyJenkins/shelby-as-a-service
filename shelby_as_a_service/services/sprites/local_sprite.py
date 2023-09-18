# region
import os
import asyncio
from concurrent.futures import ThreadPoolExecutor
import shutil
import gradio as gr
from services.log_service import Logger
from services.deployment_service.deployment_management import DeploymentManager
from models.service_models import ServiceBase
from models.service_models import LocalModel
from services.ceq_agent import CEQAgent
from services.index_service import IndexService

# endregion


class LocalSprite(ServiceBase):
    model_ = LocalModel()
    required_services_ = [CEQAgent, IndexService]

    def __init__(self, deployment_instance):
        """Sprites are initialized through a deployment.
        setup_config sets services as instance attrs.
        It uses their service_name from model.
        So CEQAgent can be accessed with self.ceq_agent.
        """
        super().__init__()
        self.setup_config()
        self.settings_components = self._create_settings_components()
        self.existing_deployment_names = DeploymentManager.check_for_existing_deployments()
        self.deployment_instance = deployment_instance
        self.log = Logger(
            self.deployment_name,
            "LocalSprite",
            "local_sprite.md",
            level="INFO",
        )

    async def create_interface(self):
        """Creates gradio app."""
        try:
            with gr.Blocks() as local_client:
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
                with gr.Tab(label="Apps Settings"):
                    save_deployment_btn = gr.Button(value="Save Config Changes")
                    undo_deployment_btn = gr.Button(value="Undo Config Change")
                    self.settings_components.render()
                    
                with gr.Tab(label="Tara's too tab"):
                    config_status_textboxt = gr.Textbox(
                        label="",
                        value="A sprite is a wily interface for interacting with AI.",
                    )
                    with gr.Tab(label="Deployment/project/app Management"):
                        with gr.Group():
                            with gr.Row():
                                load_deployments_dropdown = gr.Dropdown(
                                    value=self.existing_deployment_names[0],
                                    multiselect=False,
                                    choices=self.existing_deployment_names,
                                    label="Existing Deployments:",
                                )
                            with gr.Row():
                                load_deployment_btn = gr.Button(
                                    value="Load Existing Deployment"
                                )
                        with gr.Group():
                            with gr.Row():
                                make_deployment_textbox = gr.Textbox(
                                    label="Enter new deployment name (new_deployment_name):"
                                )
                            with gr.Row():
                                make_deployment_btn = gr.Button(
                                    value="Make New Deployment"
                                )
                        with gr.Group():
                            with gr.Row():
                                delete_deployments_dropdown = gr.Dropdown(
                                    value="Danger!",
                                    multiselect=False,
                                    choices=self.existing_deployment_names,
                                    label="Existig Deployments:",
                                )
                            with gr.Row():
                                delete_deployment_radio = gr.Radio(
                                    value="Don't Delete",
                                    choices=["Don't Delete", "Check to Confirm Delete"],
                                )
                            with gr.Row():
                                delete_deployment_btn = gr.Button(
                                    value="Delete Existing Deployment"
                                )
                    with gr.Tab(label="Index Management"):
                        index_ingest_docs = gr.Button(value="ingest_docs")
                        index_delete_index = gr.Button(value="delete_index")
                        index_clear_index = gr.Button(value="clear_index")
                        index_create_index = gr.Button(value="create_index")

                with gr.Tab(label="Logs", id="log"):
                    with gr.Row():
                        logs_output = gr.Textbox(
                            value="Logs will appear here...",
                            lines=30,
                        )

                ceq_message_textbox.submit(
                    fn=self._run_ceq_request,
                    inputs=ceq_message_textbox,
                    outputs=[ceq_message_textbox, ceq_chatbot],
                )
                index_ingest_docs.click(
                    fn=self.index_service.ingest_docs,
                    inputs=None,
                    outputs=None,
                )

                load_deployment_blocks = [
                    block for _, block in self.settings_components.blocks.items()
                    if block.elem_id is not None and hasattr(block, 'value')
                ]
                load_deployment_btn.click(
                    fn=self._load_new_deployment,
                    inputs=load_deployments_dropdown,
                    outputs=load_deployment_blocks,
                )
                make_deployment_btn.click(
                    fn=self._create_new_deployment,
                    inputs=make_deployment_textbox,
                    outputs=[
                        config_status_textboxt,
                        make_deployment_textbox,
                        load_deployments_dropdown,
                        delete_deployments_dropdown,
                    ],
                )
                delete_deployment_btn.click(
                    fn=self._delete_deployment,
                    inputs=[delete_deployments_dropdown, delete_deployment_radio],
                    outputs=[
                        config_status_textboxt,
                        load_deployments_dropdown,
                        delete_deployments_dropdown,
                        delete_deployment_radio,
                    ],
                )
                local_client.load(
                    fn=self._gradio_logging, inputs=None, outputs=logs_output, every=3
                )

                self.log.print_and_log_gradio("LocalSprite launched")
                local_client.queue().launch()

        except Exception as error:
            output_message = f"Error: {error}"
            self.log.print_and_log_gradio(output_message)

        return local_client
    

    def _create_settings_components(self):
        """Loads template interface config components and emits structured_config_components."""

        with gr.Blocks() as settings_interface:
            self._create_components_from_classes(
                class_config=self, class_name="local_sprite", secrets=True
            )
            for service in self.required_services_:
                service_name = service.model_.service_name_
                with gr.Tab(
                    label=service_name,
                    open=False,
                    elem_id=f"{service_name}_accordion",
                ):
                    self._create_components_from_classes(
                        class_config=getattr(self, service_name),
                        class_name=service_name,
                    )

        return settings_interface

    def _create_components_from_classes(self, class_config, class_name, secrets=False):
        with gr.Blocks(title=class_name) as settings_component:
            with gr.Group():
                with gr.Tab(
                    label="Required Settings",
                    open=True,
                    elem_id=f"{class_name}_required_settings",
                ):
                    for var in class_config.required_variables_:
                        req_var = getattr(class_config, var)
                        id = f"{class_name}_{var}"
                        gr.Textbox(
                            value=req_var, label=var, elem_id=id, interactive=True
                        )
                    if secrets:
                        with gr.Accordion(
                            label="Required Secrets",
                            open=True,
                            elem_id=f"{class_name}_required_Secrets",
                        ):
                            pass
                with gr.Tab(
                    label="Optional Settings",
                    open=False,
                    elem_id=f"{class_name}_optional_settings",
                ):
                    for name, value in class_config.__dict__.items():
                        if (
                            not name.startswith("__")
                            and not callable(value)
                            and not isinstance(value, ServiceBase)
                            and not isinstance(value, type)
                            and not name.endswith("_")
                            and name != 'deployment_name'
                        ):
                            if name not in class_config.required_variables_:
                                id = f"{class_name}_{name}"
                                gr.Textbox(
                                    value=value,
                                    label=name,
                                    elem_id=id,
                                    interactive=True,
                                )

        return settings_component

    def _load_new_deployment(self, load_deployment_name):
        """Loads new deployment to deployment object."""

        self.existing_deployment_names = DeploymentManager.check_for_existing_deployments()

        if load_deployment_name not in self.existing_deployment_names:
            output_message = f"Can't find a deployment named: '{load_deployment_name}'"
            self.log.print_and_log_gradio(output_message)
            return None
        if load_deployment_name in self.deployment_name:
            output_message = f"Deployment already loaded: '{load_deployment_name}'"
            self.log.print_and_log_gradio(output_message)
            return None

        self.deployment_name = load_deployment_name
        self.setup_config()
        output = self._update_settings()
        
        output_message = f"Deployment loaded: '{load_deployment_name}'"
        self.log.print_and_log_gradio(output_message)
        return output

    def _update_settings(self):
        settings = {}
        settings = self._create_update_dict(
            class_config=self, class_name="local_sprite", secrets=True
        )
        for service in self.required_services_:
            service_name = service.model_.service_name_
    
            settings.update(self._create_update_dict(
                class_config=getattr(self, service_name),
                class_name=service_name,
            ))
        output = []
        for _, block in self.settings_components.blocks.items():
            if block.elem_id is not None and hasattr(block, 'value'):
                output.append(block.update(value = settings.get(block.elem_id, None)))

        return output

    def _create_update_dict(self, class_config, class_name, secrets=False):
        settings = {}
      
        # if secrets:
        #     elem_id = f"{class_name}_required_Secrets",
        #     pass

        for name, value in class_config.__dict__.items():
            if (
                not name.startswith("__")
                and not callable(value)
                and not isinstance(value, ServiceBase)
                and not isinstance(value, type)
                and not name.endswith("_")
                and name != 'deployment_name'
            ):
             
                id = f"{class_name}_{name}"
                settings[id] = value
                    
        return settings
        
    def _create_new_deployment(self, new_deployment_name):
        
        new_deployment_name = new_deployment_name.strip()
        
        if len(new_deployment_name) < 3:
            output_message = "Please enter a longer deployment name"
            self.log.print_and_log_gradio(output_message)
        elif not all(char.isalnum() or char == "_" for char in new_deployment_name):
            output_message = "Please only use alpha numeric chars and '_' chars."
            self.log.print_and_log_gradio(output_message)
        if not self.existing_deployment_names:
            self.existing_deployment_names = (
                DeploymentManager.check_for_existing_deployments()
            )
        if new_deployment_name in self.existing_deployment_names:
            output_message = "That deployment already exists. Please delete it first"
            self.log.print_and_log_gradio(output_message)
            
        else:
            DeploymentManager().create_deployment(new_deployment_name)
            DeploymentManager().update_deployment_json(self.deployment_instance, new_deployment_name)
            self.existing_deployment_names = (
                DeploymentManager.check_for_existing_deployments()
            )
            output_message = f" Deployment '{new_deployment_name}' created"
            self.log.print_and_log_gradio(output_message)

        return (
            output_message,
            gr.Textbox.update(value=""),
            gr.Dropdown.update(
                value=self.existing_deployment_names[0],
                choices=self.existing_deployment_names,
            ),
            gr.Dropdown.update(value="Danger!", choices=self.existing_deployment_names),
        )

    def _delete_deployment(self, delete_deployment_name, delete_deployment_radio):
        if delete_deployment_name == self.deployment_name:
            output_message = "Can't delete in use deployment. Please switch first."
            self.log.print_and_log_gradio(output_message)
        elif delete_deployment_radio != "Check to Confirm Delete":
            output_message = "Please check the radio box to confirm delete"
            self.log.print_and_log_gradio(output_message)
        else:
            base_dir = "shelby_as_a_service/deployments"

            deployment_path = os.path.join(base_dir, delete_deployment_name)
            if os.path.exists(deployment_path):
                try:
                    shutil.rmtree(deployment_path)
                    output_message = (
                        f"Successfully deleted deployment: '{delete_deployment_name}'"
                    )
                    self.log.print_and_log_gradio(output_message)
                except Exception as error:
                    output_message = f"Error deleting deployment: '{delete_deployment_name}'. Error: {str(error)}"
                    self.log.print_and_log_gradio(output_message)
            else:
                output_message = f"Deployment: '{delete_deployment_name}' not found."
                self.log.print_and_log_gradio(output_message)

            self.existing_deployment_names = DeploymentManager.check_for_existing_deployments()

        return (
            output_message,
            gr.Dropdown.update(
                value=self.existing_deployment_names[0],
                choices=self.existing_deployment_names,
            ),
            gr.Dropdown.update(value="Danger!", choices=self.existing_deployment_names),
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
            asyncio.run(self.create_interface())
        except Exception as error:
            output_message = f"Error: {error}"
            self.log.print_and_log_gradio(output_message)
