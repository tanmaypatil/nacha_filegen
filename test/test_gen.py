
from dotenv import load_dotenv
from generate_nacha_file import claude_api_with_attachments

# Load environment variables from .env file
load_dotenv()

# Specify file paths
files = ["resources\\NACHA_format.pdf", "resources\\nacha_customer_CT_PPD.txt"]
#files = ["resources\\NACHA_format.pdf"]
# Prompt to 
#prompt = """ Change the credit amount in both payments to 100 . 
#         and update the control record ( record type 9) and 
#         and generate the file in NACHA format.
#         Please keep all other fields in the file unchanged."""

prompt = " can you explain the what is record type 9 in NACHA file" 

# Output file path (optional)
output_file = "nacha_file_response.txt"

def test_gen():
  # Call the API and save response to file
  response = claude_api_with_attachments(files, prompt, output_file=output_file)

  # Process the response
  if hasattr(response, "content") and len(response.content) > 0:
    for content in response.content:
        if content.type == "text":
            print(content.text)
    print(f"\nResponse has been saved to: {output_file}")
    

def test_gen_2():
  prompt = """ Change the credit amount in both payments in the sample NACHA file to 100 . 
         and update the control record ( record type 9) and 
         and generate the file in NACHA format.
         Please keep all other fields in the file unchanged."""
  
  response = claude_api_with_attachments(files, prompt, output_file=output_file)

  # Process the response
  if hasattr(response, "content") and len(response.content) > 0:
    for content in response.content:
        if content.type == "text":
            print(content.text)
    print(f"\nResponse has been saved to: {output_file}")
  
