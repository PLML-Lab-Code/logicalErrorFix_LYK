# How to use:
# python lyk/gpt1-2-parse_and_make_code.py

import json
import os

METHOD = 'parse_response1'
# file names: P[problem_id]_C[Correct_id]_I[Incorrect_id].txt
INPUT_DIR = 'lyk/output/gpt1-lcs'
# file names: [problem_id]C[Correct_id].cpp
CORRECT_CODE_DIR = 'data/cppfiles_valid'
OUTPUT_DIR = 'lyk/output/gpt1-lcs-code'
# LINE_NO_DIR = 'lyk/output/gpt1-line-no'
FAILED_DIR = 'lyk/output/gpt1-lcs-failed'

def parse_response1(possible_json_str):
  # trim input
  possible_json_str = possible_json_str.strip()
  json_obj = None
  try:
    # find first '{'
    possible_json_str = possible_json_str[possible_json_str.index('{'):]
    # find last '}'
    possible_json_str = possible_json_str[:possible_json_str.rindex('}')+1]

    # { "code": "...", "line_no": "[number]", "stmt": "[string]" }
    json_obj = json.loads(possible_json_str)
  except:
    return None
  
  if 'line_no' not in json_obj or 'stmt' not in json_obj:
    return None

  line_no = json_obj['line_no']
  stmt = json_obj['stmt']
  # try to convert line_no to int or raise
  try:
    line_no = int(line_no)
  except:
    return None
  # check stmt is str or raise
  if not isinstance(stmt, str):
    return None

  # return a tuple
  return (line_no, stmt)

def parse_response2(possible_json_str):
  # trim input
  possible_json_str = possible_json_str.strip()
  json_obj = None
  try:
    # find first '{'
    possible_json_str = possible_json_str[possible_json_str.index('{'):]
    # find last '}'
    possible_json_str = possible_json_str[:possible_json_str.rindex('}')+1]

    # {"line_number_with_error": "28", "original_stmt": "for (int i = 3; i <= 3 * n; i += 3) (a[1] += C(i, 1)) %= M;", "fixed_stmt": "for (int i = 3; i <= 3 * n; i += 3) (a[i/3] += C(i, 1)) %= M;"}
    json_obj = json.loads(possible_json_str)
  except:
    return None
  
  if 'line_number_with_error' not in json_obj or 'fixed_stmt' not in json_obj:
    return None

  line_no = json_obj['line_number_with_error']
  stmt = json_obj['fixed_stmt']
  # try to convert line_no to int or raise
  try:
    line_no = int(line_no)
  except:
    return None
  # check stmt is str or raise
  if not isinstance(stmt, str):
    return None
    
  # return a tuple
  return (line_no, stmt)

def main():
  # ensure output dir exists
  if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)
  # if not os.path.exists(LINE_NO_DIR):
  #   os.makedirs(LINE_NO_DIR)
  if not os.path.exists(FAILED_DIR):
    os.makedirs(FAILED_DIR)

  # read dir
  for filename in os.listdir(INPUT_DIR):
    # read file
    with open(os.path.join(INPUT_DIR, filename), 'r') as f:
      # read file content
      content = f.read()
      # parse
      json_obj = globals()[METHOD](content)
      if json_obj is None:
        print('Failed to parse: {}'.format(filename))
        # cp to failed dir
        with open(os.path.join(FAILED_DIR, filename), 'w') as f:
          f.write(str(content))
        continue
      # write to file
      # with open(os.path.join(LINE_NO_DIR, filename), 'w') as f:
      #   f.write(str(json_obj[0]) + '\n')
      
      with open(os.path.join(OUTPUT_DIR, filename), 'w') as f:
        f.write(f'{str(json_obj[0])} {str(json_obj[1])}\n')

if __name__ == '__main__':
  main()