import os
import base64
import mimetypes
import argparse
from datetime import datetime
from dotenv import load_dotenv
from anthropic import Anthropic

system_prompt = """
you are a helpful assistant . 
You will be provided with two files. 
The first is a NACHA file format documentation.
You will study the structure of the NACHA file and how each field is used in the file and how to format each field and the whole file.
The second file is a sample NACHA payment file.
Your task is to re-generate NACHA second file ( sample NACHA file) as per the instructions provided in the prompt.
I just need the NACHA file content, no explanations or additional text.
"""

def get_file_mimetype(file_path):
    """Determine the MIME type of a file"""
    mime_type, _ = mimetypes.guess_type(file_path)
    if mime_type is None:
        # Default to octet-stream if we can't determine the type
        return 'application/octet-stream'
    return mime_type

def encode_ifrequired(file_path):
    """Read a file and encode its contents in base64 for pdf files"""
    
    mime_type = get_file_mimetype(file_path)
    
    with open(file_path, 'rb') as file:
        file_data = file.read()
    
    
    file_base64 = base64.b64encode(file_data).decode('utf-8')
    
    print(f"Encoded {file_path} with MIME type {mime_type} and size {len(file_base64)} bytes")
    
    return {
        "type": mime_type, 
        "data": file_base64
    }

def claude_api_with_attachments(files, prompt, model="claude-sonnet-4-20250514", max_tokens=2000, output_file=None):
    """
    Send a request to Claude API with file attachments using the Anthropic Python SDK
    
    Args:
        files (list): List of file paths to attach
        prompt (str): The prompt to send to Claude
        model (str): The Claude model to use
        max_tokens (int): Maximum tokens to generate
        output_file (str, optional): Path to save the response to. If None, no file is created.
        
    Returns:
        dict: The API response
    """
    # Load API key from environment variables
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable is not set")
    
    # Initialize Anthropic client
    client = Anthropic(api_key=api_key)
    
    # Prepare message content
    message_content = [
        {
            "type": "text",
            "text": prompt
        }
    ]
    
    # Add file attachments
    for file_path in files:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        file_data = encode_ifrequired(file_path)
        
        message_object = {
            "type": "image" if file_data["type"].startswith("image/") else "document",
            "source": {
                "type": "base64" if file_data["type"] == "application/pdf" else "text",
                "data": file_data["data"],
                "media_type": file_data["type"],
            }
        }
         
        
        message_content.append(message_object)
       
    
    # Make the API call using the SDK
    message = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=system_prompt,
        messages=[
            {
                "role": "user",
                "content": message_content
            }
        ]
    )
    
    # Save response to output file if specified
    final_response = ""
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            for content in message.content:
                if content.type == "text":
                    f.write(content.text)
                    final_response = content.text
                
    
    return final_response

if __name__ == "__main__":
    # Load environment variables from .env file
    load_dotenv()
    
    parser = argparse.ArgumentParser(description="Query Claude API with file attachments")
    parser.add_argument("--file1", required=True, help="Path to first file attachment")
    parser.add_argument("--file2", required=True, help="Path to second file attachment")
    parser.add_argument("--prompt", required=True, help="Prompt for Claude")
    parser.add_argument("--model", default="claude-3-7-sonnet-20250219", help="Claude model to use")
    parser.add_argument("--max-tokens", type=int, default=2000, help="Maximum tokens to generate")
    parser.add_argument("--output", help="Path to save the response to. If not specified, a timestamped file will be created.")
    
    args = parser.parse_args()
    
    # Generate default output filename if not provided
    output_file = args.output
    if not output_file:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"claude_response_{timestamp}.txt"
    
    # Call the API
    try:
        response = claude_api_with_attachments(
            [args.file1, args.file2],
            args.prompt,
            args.model,
            args.max_tokens,
            output_file
        )
        
        # Print the response and notify about the saved file
        if hasattr(response, "content") and len(response.content) > 0:
            for content in response.content:
                if content.type == "text":
                    print(content.text)
            print(f"\n\nResponse has been saved to: {output_file}")
        else:
            print("Error or no response:", response)
            
    except Exception as e:
        print(f"Error: {e}")