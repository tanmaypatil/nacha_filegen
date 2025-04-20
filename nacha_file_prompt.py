import anthropic
import os

# Set up Claude client with your API key
client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

def generate_nacha_file(payment_details):
    """
    Generate a NACHA file using Claude API
    
    payment_details: A dictionary containing details needed for the NACHA file
    """
    
    # Create a prompt that contains all necessary information
    prompt = f"""
    Please generate a valid NACHA payment file with the following specifications:
    
    Company Name: {payment_details['company_name']}
    Company ID: {payment_details['company_id']}
    Effective Entry Date: {payment_details['effective_date']}
    
    Transactions:
    {format_transactions(payment_details['transactions'])}
    
    The NACHA file should follow exact NACHA format specifications with:
    - File Header Record (Record Type 1)
    - Batch Header Record (Record Type 5)
    - Entry Detail Records (Record Type 6) for each transaction
    - Batch Control Record (Record Type 8)
    - File Control Record (Record Type 9)
    
    Each record must be exactly 94 characters. Please provide only the raw NACHA file content, no explanations.
    """
    
    # Call Claude API
    message = client.messages.create(
        model="claude-3-7-sonnet-20250219",
        max_tokens=4000,
        temperature=0,
        system="You are an expert in ACH payment processing and NACHA file format. Generate valid NACHA files exactly according to specifications.",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    # Extract the NACHA file from Claude's response
    nacha_content = message.content[0].text
    
    # Clean up any extra text Claude might have included
    nacha_content = clean_nacha_content(nacha_content)
    
    return nacha_content

def format_transactions(transactions):
    """Format transaction details for the prompt"""
    formatted = ""
    for idx, tx in enumerate(transactions, 1):
        formatted += f"Transaction {idx}:\n"
        formatted += f"- Receiver Name: {tx['receiver_name']}\n"
        formatted += f"- Receiver Account: {tx['account_number']}\n"
        formatted += f"- Receiver Routing: {tx['routing_number']}\n"
        formatted += f"- Amount: ${tx['amount']:.2f}\n"
        formatted += f"- Transaction Type: {tx['transaction_type']} (Credit/Debit)\n\n"
    return formatted

def clean_nacha_content(content):
    """Clean up Claude's response to extract only the NACHA file content"""
    # Remove any markdown code blocks if present
    if "```" in content:
        content = content.split("```")[1].strip()
        if content.startswith("nacha") or content.startswith("NACHA"):
            content = content.split("\n", 1)[1]
    
    # Ensure each line is exactly 94 characters
    lines = content.strip().split("\n")
    validated_lines = []
    
    for line in lines:
        if line and not line.isspace():
            if len(line) != 94:
                print(f"Warning: Line length {len(line)} != 94 characters")
            validated_lines.append(line)
    
    return "\n".join(validated_lines)

# Example usage
if __name__ == "__main__":
    payment_details = {
        "company_name": "ACME CORP",
        "company_id": "1234567890",
        "effective_date": "240422",  # YYMMDD format
        "transactions": [
            {
                "receiver_name": "JOHN DOE",
                "account_number": "12345678",
                "routing_number": "021000021",
                "amount": 1250.00,
                "transaction_type": "Credit"
            },
            {
                "receiver_name": "JANE SMITH",
                "account_number": "87654321",
                "routing_number": "021000021",
                "amount": 750.00,
                "transaction_type": "Credit"
            }
        ]
    }
    
    nacha_file = generate_nacha_file(payment_details)
    
    # Save to file
    with open("payment.nacha", "w") as f:
        f.write(nacha_file)
    
    print("NACHA file generated successfully.")