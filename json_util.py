import json

# Simple version - pretty print JSON
def json_to_simple_text(json_file_path):
    with open(json_file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
    
    # Convert to pretty-printed JSON text
    return json.dumps(data, indent=2, ensure_ascii=False)

