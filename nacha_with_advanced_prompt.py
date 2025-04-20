import anthropic
import os
import json
from datetime import datetime

# Set up Claude client with your API key
client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

def generate_nacha_file(nacha_config):
    """
    Generate a NACHA file using Claude API
    
    nacha_config: A dictionary containing all NACHA file specifications
    """
    
    # Format the configuration as JSON for clear structure in the prompt
    formatted_config = json.dumps(nacha_config, indent=2)
    
    # Create a detailed prompt with complete NACHA specifications
    prompt = f"""
    Generate a valid NACHA payment file according to the following specifications:
    
    {formatted_config}
    
    Important requirements:
    1. Follow the exact NACHA format for each SEC code
    2. Each record must be exactly 94 characters
    3. Handle all required fields for the specified SEC codes (including IAT specific structures)
    4. Calculate correct batch and file control totals
    5. Generate proper trace numbers and entry hash totals
    6. Format all fields according to NACHA rules (left/right justification, zero-filling, etc.)
    7. Include all necessary addenda records for each SEC code
    
    Provide only the raw NACHA file content with each record on a new line, no explanations.
    """
    
    # Call Claude API with system prompt focused on NACHA expertise
    message = client.messages.create(
        model="claude-3-7-sonnet-20250219",
        max_tokens=8000,
        temperature=0,
        system="""You are an expert in ACH payment processing with comprehensive knowledge of NACHA file formats 
        for all SEC codes including PPD, CCD, TEL, WEB, IAT and others. You understand the specific requirements 
        for international transactions, addenda records, batch structuring, and all transaction codes. 
        You generate complete, valid NACHA files exactly according to specifications with proper record formatting, 
        field validation, and accurate control totals.""",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    # Extract the NACHA file from Claude's response
    nacha_content = message.content[0].text
    
    # Clean up any extra text Claude might have included
    nacha_content = clean_nacha_content(nacha_content)
    
    return nacha_content

def clean_nacha_content(content):
    """Clean up Claude's response to extract only the NACHA file content"""
    # Remove any markdown code blocks if present
    if "```" in content:
        parts = content.split("```")
        for part in parts:
            if part.strip() and not part.startswith("nacha") and not part.startswith("NACHA"):
                content = part.strip()
                break
    
    # Ensure each line is exactly 94 characters
    lines = content.strip().split("\n")
    validated_lines = []
    
    for line in lines:
        if line and not line.isspace():
            if len(line) != 94:
                print(f"Warning: Line length {len(line)} != 94 characters")
            validated_lines.append(line)
    
    return "\n".join(validated_lines)

# Example of a complex NACHA configuration
def create_sample_iat_config():
    """Create a sample NACHA configuration for IAT transactions"""
    today = datetime.now().strftime("%y%m%d")
    
    return {
        "file_header": {
            "immediate_destination": "071000505",    # Receiving bank routing number
            "immediate_origin": "1234567890",       # Company ID/Tax ID
            "file_creation_date": today,
            "file_creation_time": datetime.now().strftime("%H%M"),
            "file_id_modifier": "A",
            "immediate_destination_name": "BANK OF AMERICA",
            "immediate_origin_name": "GLOBAL TRADING CO"
        },
        "batches": [
            {
                "batch_header": {
                    "service_class_code": "220",     # Credit only
                    "company_name": "GLOBAL TRADING",
                    "company_discretionary_data": "",
                    "company_identification": "1234567890",
                    "standard_entry_class_code": "IAT",
                    "company_entry_description": "PAYMENTS",
                    "effective_entry_date": (datetime.now().strftime("%y%m%d")),
                    "settlement_date": "",           # Left blank, filled by ACH operator
                    "originator_status_code": "1"
                },
                "entries": [
                    {
                        "transaction_code": "22",    # Checking credit
                        "receiving_dfi_id": "021000021",   # Chase routing number
                        "check_digit": "1",
                        "dfi_account_number": "12345678901234567",
                        "amount": 150000,            # $1,500.00
                        "individual_name": "JOHN MERCHANT LTD",
                        "foreign_receiver_info": {
                            "name": "GLOBAL IMPORT EXPORT GMBH",
                            "address": "123 INTERNATIONAL BLVD",
                            "city": "FRANKFURT",
                            "country_code": "DE",
                            "country_name": "GERMANY"
                        },
                        "originator_info": {
                            "name": "GLOBAL TRADING COMPANY",
                            "address": "456 COMMERCE STREET",
                            "city": "NEW YORK",
                            "state": "NY",
                            "postal_code": "10001",
                            "country_code": "US"
                        },
                        "foreign_correspondent_bank": {
                            "name": "DEUTSCHE BANK",
                            "id_number": "DEUTDE5F",
                            "id_qualifier": "01"    # 01 = SWIFT ID
                        },
                        "currency_info": {
                            "currency_type": "EUR",
                            "exchange_rate": "1.02345"
                        }
                    }
                ]
            },
            {
                "batch_header": {
                    "service_class_code": "225",     # Debit only
                    "company_name": "GLOBAL TRADING",
                    "company_discretionary_data": "",
                    "company_identification": "1234567890",
                    "standard_entry_class_code": "CCD",
                    "company_entry_description": "INVOICES",
                    "effective_entry_date": (datetime.now().strftime("%y%m%d")),
                    "settlement_date": "",
                    "originator_status_code": "1"
                },
                "entries": [
                    {
                        "transaction_code": "27",    # Checking debit
                        "receiving_dfi_id": "121000248",
                        "check_digit": "8",
                        "dfi_account_number": "987654321",
                        "amount": 250000,            # $2,500.00
                        "receiving_company_name": "WIDGETS SUPPLIER INC",
                        "discretionary_data": "",
                        "addenda": [
                            {
                                "payment_related_info": "INV:A12345 PO:B789012"
                            }
                        ]
                    },
                    {
                        "transaction_code": "27",
                        "receiving_dfi_id": "122105155",
                        "check_digit": "5",
                        "dfi_account_number": "135792468",
                        "amount": 125000,            # $1,250.00
                        "receiving_company_name": "PARTS SUPPLIER CO",
                        "discretionary_data": "",
                        "addenda": [
                            {
                                "payment_related_info": "INV:C67890 PO:D123456"
                            }
                        ]
                    }
                ]
            }
        ]
    }

# Example usage
if __name__ == "__main__":
    # For IAT example
    nacha_config = create_sample_iat_config()
    
    # Generate the NACHA file
    nacha_file = generate_nacha_file(nacha_config)
    
    # Save to file
    with open("international_payment.nacha", "w") as f:
        f.write(nacha_file)
    
    print("NACHA file generated successfully.")