import gradio as gr
from sprites.local.local_app_theme import AtYourServiceTheme

gradio_components = {}


def create_interface(self):
    """Creates gradio app."""

    with gr.Blocks(theme=AtYourServiceTheme()) as local_client:
        # with gr.Blocks() as local_client:

        create_chat_ui(self)
        # create_event_handlers(self)
        # with gr.Tab(label="Data Index"):
        #     with gr.Tab(label="Index Config"):
        #         self._create_index_config()

        #     with gr.Tab(label="Web Source"):
        #         source_textbox = gr.Textbox(
        #             placeholder="url_source or file path",
        #             show_label=False,
        #             label="Message",
        #         )
        #         index_ingest_docs = gr.Button(size="sm", value="ingest_docs")
        #         index_components = self._create_settings_tab(self.index)
        #     with gr.Tab(label="Local File"):
        #         source_textbox = gr.Textbox(
        #             placeholder="url_source or file path",
        #             show_label=False,
        #             label="Message",
        #         )
        #         index_ingest_docs = gr.Button(size="sm", value="ingest_docs")
        #     with gr.Tab(label="Log"):
        #         index_ingest_docs = gr.Button(size="sm", value="ingest_docs")

        # with gr.Tab(label="Config"):
        # with gr.Tab(label="Local Sprite"):
        #     config_components = self._create_settings_tab(self)

        # with gr.Tab(label="Secrets"):
        #     with gr.Row():
        #         gr.Textbox(
        #             show_label=False,
        #             scale=2,
        #             lines=3,
        #             value="Instructions here",
        #         )
        #         with gr.Column(variant="panel"):
        #             secrets_file_btn = gr.Button(
        #                 size="sm", value="Save Secrets to .env File"
        #             )
        #     with gr.Row():
        #         secrets_components = self._create_secrets_components()

        #         secrets_file_btn.click(
        #             fn=self._save_load_new_secrets,
        #             inputs=secrets_components,
        #             outputs=secrets_components,
        #         )

        # with gr.Tab(label="Management"):
        #     with gr.Row():
        #         gr.Textbox(
        #             show_label=False,
        #             lines=15,
        #             scale=2,
        #             value="Instructions here",
        #         )
        #         with gr.Column(variant="panel"):
        #             with gr.Group():
        #                 load_apps_dropdown = gr.Dropdown(
        #                     value=self.existing_app_names_[0],
        #                     multiselect=False,
        #                     choices=self.existing_app_names_,
        #                     label="Load Existing app",
        #                 )
        #                 load_app_btn = gr.Button(size="sm", value="Load")
        #             with gr.Group():
        #                 make_app_textbox = gr.Textbox(
        #                     label="Create new app",
        #                     placeholder="<your_new_app_name>",
        #                 )
        #                 make_app_btn = gr.Button(size="sm", value="Create")
        #             with gr.Group():
        #                 with gr.Group():
        #                     delete_apps_dropdown = gr.Dropdown(
        #                         value="Danger!",
        #                         multiselect=False,
        #                         choices=self.existing_app_names_,
        #                         label="Delete Existing app",
        #                     )
        #                     delete_app_chk_box = gr.Checkbox(
        #                         value=False,
        #                         label="Check to confirm",
        #                     )
        #                     delete_app_btn = gr.Button(
        #                         size="sm", value="Delete"
        #                     )

        #             load_app_btn.click(
        #                 fn=self._load_new_app_from_file,
        #                 inputs=load_apps_dropdown,
        #                 outputs=None,
        #             ).success(
        #                 fn=self._update_ui_settings_components,
        #                 inputs=ceq_components,
        #                 outputs=ceq_components,
        #             ).success(
        #                 fn=self._update_ui_settings_components,
        #                 inputs=index_components,
        #                 outputs=index_components,
        #             ).success(
        #                 fn=self._update_ui_settings_components,
        #                 inputs=config_components,
        #                 outputs=config_components,
        #             )

        #             make_app_btn.click(
        #                 fn=self._create_new_app,
        #                 inputs=make_app_textbox,
        #                 outputs=[
        #                     make_app_textbox,
        #                     load_apps_dropdown,
        #                     delete_apps_dropdown,
        #                 ],
        #             )

        #             delete_app_btn.click(
        #                 fn=self._delete_app,
        #                 inputs=[delete_apps_dropdown, delete_app_chk_box],
        #                 outputs=[
        #                     load_apps_dropdown,
        #                     delete_apps_dropdown,
        #                     delete_app_chk_box,
        #                 ],
        #             )

        local_client.queue()
        local_client.launch()


def create_chat_ui(self):
    gradio_components["chat_ui"] = {}
    with gr.Tab(label="Chat"):
        with gr.Tab(label="Vanilla Chat"):
            with gr.Column(variant="panel"):
                gradio_components["chat_ui"]["vanilla_chatbot"] = gr.ChatInterface(
                    self.vanilla_agent.create_streaming_chat
                ).queue()
        #         with gr.Group():
        #             with gr.Row():
        #                 gradio_components['chat_ui']['vanilla_message_textbox'] = gr.Textbox(
        #                     container=False,
        #                     show_label=False,
        #                     label="Message",
        #                     placeholder="Type a message...",
        #                     scale=7,
        #                 )

        # with gr.Tab(label="Context Enhanced Querying"):
        #     with gr.Column(variant="panel"):
        #         ceq_chatbot = gr.Textbox(label="Chatbot", lines=20)
        #         with gr.Group():
        #             with gr.Row():
        #                 ceq_message_textbox = gr.Textbox(
        #                     container=False,
        #                     show_label=False,
        #                     label="Message",
        #                     placeholder="Type a message...",
        #                     scale=7,
        #                 )


# def create_event_handlers(self):

#     gradio_components["chat_ui"]['vanilla_message_textbox'].submit(
#         fn=self.vanilla_agent.run_query,
#         inputs=gradio_components['chat_ui']['vanilla_message_textbox'],
#         outputs=gradio_components['chat_ui']['vanilla_chatbot'],
#     )
