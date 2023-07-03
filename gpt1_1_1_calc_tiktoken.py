# How to use:
# python lyk/gpt1_1_1_calc_tiktoken.py
'''
python lyk/gpt1_1_1_calc_tiktoken.py \
--pair_data_path data/edit_distance/refined_pair_code_edit_dist_valid.txt \
--prompt_name lcs \
--output_db_path lyk/output/gpt1_1_1_lcs_tiktoken_valid.db
'''
'''
python lyk/gpt1_1_1_calc_tiktoken.py \
--pair_data_path data/edit_distance/refined_pair_code_edit_dist_valid.txt \
--prompt_name lsh \
--output_db_path lyk/output/gpt1_1_1_lsh_tiktoken_valid.db
'''

import argparse
import os
import tiktoken

from utils import Sqlite3Db, Sqlite3TableGpt1_1_1, gpt1_build_prompt, PairDataV1, PDCodeV1



def main():
  parser = argparse.ArgumentParser()
  parser.add_argument('--pair_data_path', type=str, default='data/edit_distance/refined_pair_code_edit_dist_valid.txt',
    help='페어 데이터 경로')
  parser.add_argument('--prompt_name', type=str, default='lcs',
    help='프롬프트 이름 (ex. lcs, lsh)')
  parser.add_argument('--output_db_path', type=str, default='lyk/output/gpt1_1_1-NAME.db',
    help='출력 데이터베이스 경로')
  parser.add_argument('--output_db_table_name', type=str, default='',
    help='데이터베이스 테이블 이름 (비우면 기본값)')

  args = parser.parse_args()

  gpt1_1_1_calc(
    pair_data_path=args.pair_data_path,
    prompt_name=args.prompt_name,
    output_db_path=args.output_db_path,
    output_db_table_name=args.output_db_table_name,
  )



def gpt1_1_1_calc(
  pair_data_path: str,
  prompt_name: str,
  output_db_path: str,
  output_db_table_name: str,
):
  # db_path parent
  db_path_parent = os.path.dirname(output_db_path)
  # ensure output dir exists
  os.makedirs(db_path_parent, exist_ok=True)

  # lyk/gpt1/prompt/ 에서 {name}.txt 프롬프트 불러와서 .format
  # {name}.txt 파일이 없으면 에러
  path = 'lyk/gpt1/prompt/{}.txt'.format(prompt_name)

  # 데이터베이스 연결
  output_db = Sqlite3Db(db_file=output_db_path)
  output_table = Sqlite3TableGpt1_1_1(sqlite3db=output_db, table_name=output_db_table_name)
  try:
    # 페어 데이터 읽기
    pair_data = PairDataV1.from_csv(pair_data_path)
    # 페어 데이터 순회
    def process_element(
      pid: int,
      cid: int,
      iid: int,
      correct_code: PDCodeV1,
      incorrect_code: PDCodeV1,
      statement: str,
    ):
      # incorrect_code 프롬프트 빌드
      prompt = gpt1_build_prompt(path, str(incorrect_code))
      # * OpenAI의 tiktoken 라이브러리를 사용해 요청에 사용될 토큰 양 계산
      # https://github.com/openai/openai-cookbook/blob/main/examples/How_to_count_tokens_with_tiktoken.ipynb
      enc = tiktoken.get_encoding('cl100k_base') # gpt-4, gpt-3.5-turbo, text-embedding-ada-002
      token = enc.encode(prompt)
      token_count = len(token)
      # 토큰 양 데이터베이스에 저장
      output_table.safe_insert_many_tuple([(pid, cid, iid, token_count)])
    
    # For each
    pair_data.do_for_each(process_element)
  finally:
    output_db.close()
    output_db = None
    output_table = None



if __name__ == '__main__':
  main()
