
def validate_nacha_file(file_content):
  status = "valid"
  errors = []
  # read the system prompt from the file
  with open("resources/nacha_validation_prompt.txt", "r", encoding="utf-8") as file:
      system_prompt = file.read()
  print(f"System prompt being used for validation: {system_prompt}")    
  
  return status,errors