import re

def safe_key_string(key: str) -> str:
  # change non-alphanumeric characters to _
  key = re.sub(r'[^a-zA-Z0-9]', '_', key)
  # add _ if key has leading numbers
  if re.match(r'^[0-9]', key):
    key = '_' + key
  return key
