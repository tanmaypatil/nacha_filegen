import gradio as gr
from dotenv import load_dotenv
from generate_nacha_file import claude_api_with_attachments

# Load environment variables from .env file
load_dotenv()

# Specify file paths
files = ["resources\\NACHA_format.pdf", "resources\\nacha_customer_CT_PPD.txt"]
prompt = """ Change the credit amount in both payments to 100 . 
        and update the control record ( record type 9) and 
        and generate the file in NACHA format.
        Please keep all other fields in the file unchanged."""

# Output file path (optional)
output_file = "nacha_file_response.txt"


def generate_file(prompt):
    # This function would typically call a backend service to generate the Nacha file
    # For demonstration purposes, we will just return the prompt as output
    message = claude_api_with_attachments(files, prompt, output_file=output_file)
    return message
  

with gr.Blocks() as demo:
    gr.Markdown("## Generate Nacha file ")
    with gr.Row():
        with gr.Column():
          prompt = gr.TextArea(label="Prompt", placeholder="Enter your prompt here...", lines=10)
    with gr.Row():
      with gr.Column():
            output = gr.TextArea(label="Output",placeholder="Output will be displayed here...", lines=10)
    with gr.Row():
        with gr.Column():
            submit_btn = gr.Button("Submit")
        
    submit_btn.click(fn=generate_file, inputs=prompt, outputs=output)
    
    
demo.launch()
    