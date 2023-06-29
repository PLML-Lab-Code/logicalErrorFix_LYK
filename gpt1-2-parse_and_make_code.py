# How to use:
# python lyk/gpt1-2-parse_and_make_code.py

import json
import os

# file names: P[problem_id]_C[Correct_id]_I[Incorrect_id].txt
INPUT_DIR = 'lyk/output/gpt1'
# file names: [problem_id]C[Correct_id].cpp
CORRECT_CODE_DIR = 'data/cppfiles_valid'
OUTPUT_DIR = 'lyk/output/gpt1-code'
LINE_NO_DIR = 'lyk/output/gpt1-line-no'
FAILED_DIR = 'lyk/output/gpt1-failed'

def parse_response(possible_json_str):
  # trim input
  possible_json_str = possible_json_str.strip()
  json_obj = None
  try:
    # { "code": "...", "line_no": "[number]", "stmt": "[string]" }
    json_obj = json.loads(possible_json_str)
  except:
    return None
  
  if 'line_no' not in json_obj or 'stmt' not in json_obj:
    return None

  # return a tuple
  return (json_obj['line_no'], json_obj['stmt'])

def main():
  # ensure output dir exists
  if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)
  if not os.path.exists(LINE_NO_DIR):
    os.makedirs(LINE_NO_DIR)
  if not os.path.exists(FAILED_DIR):
    os.makedirs(FAILED_DIR)

  # read dir
  for filename in os.listdir(INPUT_DIR):
    # read file
    with open(os.path.join(INPUT_DIR, filename), 'r') as f:
      # read file content
      content = f.read()
      # parse
      json_obj = parse_response(content)
      if json_obj is None:
        print('Failed to parse: {}'.format(filename))
        # cp to failed dir
        with open(os.path.join(FAILED_DIR, filename), 'w') as f:
          f.write(content)
        continue
      # write to file
      with open(os.path.join(LINE_NO_DIR, filename), 'w') as f:
        f.write(json_obj[0] + '\n')
      
      with open(os.path.join(OUTPUT_DIR, filename), 'w') as f:
        f.write(json_obj[1] + '\n')

if __name__ == '__main__':
  main()