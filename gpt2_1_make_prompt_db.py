# TODO: This script currently load dataset from restrict path. Change it to db for later use.
# How to Use:
# python lyk/gpt2_1_make_prompt_db.py
'''
python lyk/gpt2_1_make_prompt_db.py \
  --prompt_type gpt \
  --output_db_path lyk/output/gpt2_1_llama.db
'''


import argparse
import json
import os
import re
from typing import Any, Dict, Generator, List, Tuple

from tqdm import tqdm, trange

from utils import gpt1_json_prompt_reader, Sqlite3Db, Sqlite3TablePromptDb, PairDataV1, PDCodeV1



def main():
  parser = argparse.ArgumentParser()
  parser.add_argument('--prompt_type', type=str, default='openai', choices=['openai', 'gpt'],
    help='Prompt type ("openai" for openai chat json, "gpt" for gpt-style text prompt)')
  parser.add_argument('--output_db_path', type=str, default='lyk/output/gpt2_1_NAME.db',
    help='Output database path')
  parser.add_argument('--output_db_table_name', type=str, default='',
    help='Output database table name (empty for default)')
  
  args = parser.parse_args()

  gpt2_1_make_prompt_db(
    prompt_type=args.prompt_type,
    output_db_path=args.output_db_path,
    output_db_table_name=args.output_db_table_name
  )


def ensure_code(code):
  # If code is coverd in front and back with " or ', remove them
  if code[0] == '"' and code[-1] == '"':
    code = code[1:-1]
  if code[0] == "'" and code[-1] == "'":
    code = code[1:-1]
  # Replace " with \"
  code = code.replace('"', '\\"')
  # return PROMPT.format(code)
  return code



def gpt2_1_make_prompt_db(
  prompt_type: str,
  output_db_path: str,
  output_db_table_name: str
):

  # TODO
  # * Pair data load
  pair_data = PairDataV1.from_csv('data/edit_distance/refined_pair_code_edit_dist_valid.txt')

  # * Database load
  output_db = Sqlite3Db(output_db_path)
  output_table = Sqlite3TablePromptDb(output_db, output_db_table_name)

  def process_data(
    pid: int,
    cid: int,
    iid: int,
    correct_code: PDCodeV1,
    incorrect_code: PDCodeV1,
    error_code_stmt: str
  ):
    # Create prompt
    code = ensure_code(incorrect_code.to_code())
    prompt = gpt1_json_prompt_reader('lyk/gpt1/prompt/lshv2fs.json', code)
    # if openai chat json type, convert to json string
    if prompt_type == 'openai':
      prompt = json.dumps(prompt)
    # if gpt text prompt type, convert to string
    elif prompt_type == 'gpt':
      # TODO
      # get the last prompt's content
      prompt = prompt[-1]['content']
    else:
      raise ValueError(f'Unknown prompt type: {prompt_type}')    
    # Write to database
    output_table.safe_insert_many_dict([{
      'pid': pid,
      'cid': cid,
      'iid': iid,
      'prompt': prompt
    }])
      
  pair_data.do_for_each(
    lambda pid, cid, iid, correct_code, incorrect_code, error_code_stmt: process_data(
      pid, cid, iid, correct_code, incorrect_code, error_code_stmt
    )
  )



if __name__ == '__main__':
  main()
