# How to use:
# python lyk/gpt1_2_parse_and_make_code.py
'''
python lyk/gpt1_2_parse_and_make_code.py \
--input_dir lyk/output/gpt1_lcs \
--output_db_path lyk/output/gpt1_2_lcs_refined_valid.db \
--method parse_response1
'''
'''
python lyk/gpt1_2_parse_and_make_code.py \
--input_dir lyk/output/gpt1_lsh \
--output_db_path lyk/output/gpt1_2_lsh_refined_valid.db \
--method parse_response2
'''

import argparse
import json
import os
import re
from typing import Any, Dict, Generator, List, Tuple

from utils import Sqlite3Db, Sqlite3TableGpt1_2_stmt, Sqlite3TableGpt1_2_failed



def main():
  parser = argparse.ArgumentParser()
  parser.add_argument('--output_db_path', type=str, default='lyk/output/gpt1-2-NAME.db',
    help='출력 데이터베이스 경로')
  parser.add_argument('--output_db_stmt_table_name', type=str, default='',
    help='파싱 데이터베이스 테이블 이름 (비우면 기본값)')
  parser.add_argument('--output_db_failed_table_name', type=str, default='',
    help='실패 데이터베이스 테이블 이름 (비우면 기본값)')
  parser.add_argument('--input_dir', type=str, default='lyk/output/gpt1-NAME',
    help='입력 폴더 경로')
  parser.add_argument('--method', type=str, default='parse_response2',
    help='응답 파싱에 사용할 함수 이름')

  args = parser.parse_args()

  # db_path parent
  db_path_parent = os.path.dirname(args.output_db_path)
  # ensure output dir exists
  os.makedirs(db_path_parent, exist_ok=True)

  # * 데이터베이스 연결
  db = Sqlite3Db(args.output_db_path)
  table_stmt = Sqlite3TableGpt1_2_stmt(db, args.output_db_stmt_table_name)
  table_failed = Sqlite3TableGpt1_2_failed(db, args.output_db_failed_table_name)
  try:
    # read dir
    for filename in os.listdir(args.input_dir):
      # Parse filename as P[problem_id]C[Correct_id]I[Incorrect_id].txt
      matched = re.match(r'P(\d+)C(\d+)I(\d+).txt', filename)
      if matched is None:
        print('Critical failed to parse: {}'.format(filename))
        exit(1)
      pid, cid, iid = matched.groups()

      # read file
      with open(os.path.join(args.input_dir, filename), 'r') as f:
        # read file content
        content = f.read()
        # parse
        json_obj = globals()[args.method](content)
        if json_obj is None:
          print('Failed to parse: {}'.format(filename))
          table_failed.safe_insert_many_dict([{
            'pid': pid,
            'cid': cid,
            'iid': iid,
            'response': content
          }])
          continue
      
        # insert to db
        table_stmt.safe_insert_many_dict([{
          'pid': pid,
          'cid': cid,
          'iid': iid,
          'line_no': int(json_obj[0]),
          'stmt': str(json_obj[1])
        }])

  except Exception as e:
    db.conn.rollback()
    db.close()
    raise e

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

if __name__ == '__main__':
  main()