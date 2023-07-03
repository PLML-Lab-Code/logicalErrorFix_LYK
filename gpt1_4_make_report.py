# How to use:
# python lyk/gpt1_4_make_report.py
'''
python lyk/gpt1_4_make_report.py \
--pair_data_path data/edit_distance/refined_pair_code_edit_dist_valid.txt \
--token_data_path lyk/output/gpt1_1_1_lcs_tiktoken_valid.db \
--stmt_db_path lyk/output/gpt1_2_lcs_refined_valid.db \
--execute_text_db_path lyk/output/gpt1_3_lcs_refined_valid_gpp17.db \
--output_dir lyk/output/gpt1_4_lcs_refined_valid_gpp17
'''
'''
python lyk/gpt1_4_make_report.py \
--pair_data_path data/edit_distance/refined_pair_code_edit_dist_valid.txt \
--token_data_path lyk/output/gpt1_1_1_lsh_tiktoken_valid.db \
--stmt_db_path lyk/output/gpt1_2_lsh_refined_valid.db \
--execute_text_db_path lyk/output/gpt1_3_lsh_refined_valid_gpp17.db \
--output_dir lyk/output/gpt1_4_lsh_refined_valid_gpp17
'''

import argparse
import logging
import os
import traceback

import matplotlib.pyplot as plt
import numpy as np
from tqdm import tqdm

from utils import Sqlite3Db, Sqlite3TableGpt1_2_stmt, Sqlite3TableGpt1_3, PairDataV1, Sqlite3TableGpt1_1_1

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')



def main():
  parser = argparse.ArgumentParser()
  parser.add_argument('--pair_data_path', type=str, default='data/edit_distance/refined_pair_code_edit_dist_valid.txt',
    help='원본 데이터 쌍 경로')
  parser.add_argument('--token_data_path', type=str, default='lyk/output/gpt1_1_1_NAME.db',
    help='생성된 prompt 의 token 데이터베이스 파일 경로')
  parser.add_argument('--token_data_table_name', type=str, default='',
    help='생성된 prompt 의 token 데이터베이스 테이블 이름 (비우면 기본값)')
  parser.add_argument('--stmt_db_path', type=str, default='lyk/output/gpt1-2-NAME.db',
    help='GPT가 생성한 stmt 데이터베이스 파일 경로')
  parser.add_argument('--stmt_db_table_name', type=str, default='',
    help='GPT가 생성한 stmt 데이터베이스 테이블 이름 (비우면 기본값)')
  parser.add_argument('--execute_text_db_path', type=str, default='lyk/output/gpt1-3-NAME.db',
    help='실행 결과 데이터베이스 경로')
  parser.add_argument('--execute_text_db_table_name', type=str, default='',
    help='실행 결과 데이터베이스 테이블 이름 (비우면 기본값)')
  parser.add_argument('--output_dir', type=str, default='lyk/output/gpt1-4-NAME',
    help='출력 폴더 경로')
  
  

  args = parser.parse_args()

  # * 데이터베이스 연결
  pair_data_path = args.pair_data_path
  token_data_path = args.token_data_path
  token_data_table_name = args.token_data_table_name
  stmt_db_path = args.stmt_db_path
  stmt_db_table_name = args.stmt_db_table_name
  execute_text_db_path = args.execute_text_db_path
  execute_text_db_table_name = args.execute_text_db_table_name
  output_dir = args.output_dir

  # * 폴더 생성
  os.makedirs(output_dir, exist_ok=True)

  # # * 보고서 생성: AC, TLE, WA, RE, CE 비율
  # gpt1_4_make_report_ratio(
  #   execute_text_db_path=execute_text_db_path,
  #   execute_text_db_table_name=execute_text_db_table_name,
  #   output_dir=output_dir
  # )

  # # * 보고서 생성: Incorrect_code 의 라인 수 분포 그래프
  # gpt1_4_make_report_line_distribution(
  #   pair_data_path=pair_data_path,
  #   output_dir=output_dir
  # )

  # # * 보고서 생성: line_no 예측 정확도
  # gpt1_4_make_report_line_no_accr(
  #   pair_data_path=pair_data_path,
  #   stmt_db_path=stmt_db_path,
  #   stmt_db_table_name=stmt_db_table_name,
  #   output_dir=output_dir
  # )

  # * 보고서 생성: 토큰 갯수 분포 그래프
  gpt1_4_make_report_calc_tiktoken(
    token_data_path=token_data_path,
    token_data_table_name=token_data_table_name,
    output_dir=output_dir
  )



def gpt1_4_make_report_ratio(
  execute_text_db_path: str,
  execute_text_db_table_name: str,
  output_dir: str
):
  file_name = os.path.basename(execute_text_db_path)
  # * 데이터베이스 연결
  db = Sqlite3Db(execute_text_db_path)
  table = Sqlite3TableGpt1_3(db, execute_text_db_table_name)

  # * 데이터베이스 읽기

  # 총 비율
  ac = 0
  tle = 0
  wa = 0
  re = 0
  ce = 0
  count = table.count()
  cursor = table.cursor_reader_tuple()

  with tqdm(total=count, desc='📖 all ratio') as pbar:
    for rows in cursor:
      for row in rows:
        status = row[4]
        if status == 'AC':
          ac += 1
        elif status == 'TLE':
          tle += 1
        elif status == 'WA':
          wa += 1
        elif status == 'RE':
          re += 1
        elif status == 'CE':
          ce += 1
        else:
          raise Exception('Unknown status: {}'.format(status))
        pbar.update(1)
  
  # * Matplotlib bar chart with percentage
  img_path = os.path.join(output_dir, 'gpt1-4-all.png')
  data = [ac, tle, wa, re, ce]
  x = np.arange(len(data))
  plt.bar(x, data)
  plt.xticks(x, ('AC', 'TLE', 'WA', 'RE', 'CE'))
  plt.ylabel('Count')
  plt.title(f'Script: GPT-1-4({file_name})\nall ratio (count: {count})\n')
  plt.text(0, ac, '{:.2f}%\n({})'.format(ac / count * 100, ac), ha='center', va='bottom')
  plt.text(1, tle, '{:.2f}%\n({})'.format(tle / count * 100, tle), ha='center', va='bottom')
  plt.text(2, wa, '{:.2f}%\n({})'.format(wa / count * 100, wa), ha='center', va='bottom')
  plt.text(3, re, '{:.2f}%\n({})'.format(re / count * 100, re), ha='center', va='bottom')
  plt.text(4, ce, '{:.2f}%\n({})'.format(ce / count * 100, ce), ha='center', va='bottom')
  
  plt.tight_layout()
  plt.draw()
  plt.savefig(img_path, dpi=200)

  # 엄격 모드 (같은 pid, cid, iid에 대해 하나라도 TLE, WA, RE, CE가 있으면 AC가 아님)
  ret_dict = {}
  count = table.count()
  cursor = table.cursor_reader_dict()

  with tqdm(total=count, desc='📖 strict ratio') as pbar:
    for rows in cursor:
      for row in rows:
        status = row["status"]
        key = f'{row["pid"]}-{row["cid"]}-{row["iid"]}'
        if ret_dict.get(key) is None:
          ret_dict[key] = status
        else:
          if status == 'TLE' and ret_dict[key] == 'AC':
            ret_dict[key] = status
          elif status == 'WA' and (ret_dict[key] == 'AC' or ret_dict[key] == 'TLE'):
            ret_dict[key] = status
          elif status == 'RE' and (ret_dict[key] == 'AC' or ret_dict[key] == 'TLE' or ret_dict[key] == 'WA'):
            ret_dict[key] = status
          elif status == 'CE' and (ret_dict[key] == 'AC' or ret_dict[key] == 'TLE' or ret_dict[key] == 'WA' or ret_dict[key] == 'RE'):
            ret_dict[key] = status
        pbar.update(1)
  
  ac = 0
  tle = 0
  wa = 0
  re = 0
  ce = 0
  count = len(ret_dict)
  for key in ret_dict:
    status = ret_dict[key]
    if status == 'AC':
      ac += 1
    elif status == 'TLE':
      tle += 1
    elif status == 'WA':
      wa += 1
    elif status == 'RE':
      re += 1
    elif status == 'CE':
      ce += 1
    else:
      raise Exception('Unknown status: {}'.format(status))
          
  # * Matplotlib bar chart with percentage
  # clean plot
  plt.clf()
  img_path = os.path.join(output_dir, 'gpt1-4-strict.png')
  data = [ac, tle, wa, re, ce]
  x = np.arange(len(data))
  plt.bar(x, data)
  plt.xticks(x, ('AC', 'TLE', 'WA', 'RE', 'CE'))
  plt.ylabel('Count')
  plt.title(f'Script: GPT-1-4({file_name})\nper incorrect_code ratio (count: {count})\n')
  plt.text(0, ac, '{:.2f}%\n({})'.format(ac / count * 100, ac), ha='center', va='bottom')
  plt.text(1, tle, '{:.2f}%\n({})'.format(tle / count * 100, tle), ha='center', va='bottom')
  plt.text(2, wa, '{:.2f}%\n({})'.format(wa / count * 100, wa), ha='center', va='bottom')
  plt.text(3, re, '{:.2f}%\n({})'.format(re / count * 100, re), ha='center', va='bottom')
  plt.text(4, ce, '{:.2f}%\n({})'.format(ce / count * 100, ce), ha='center', va='bottom')

  plt.tight_layout()
  plt.draw()
  plt.savefig(img_path, dpi=200)



  # * 데이터베이스 닫기
  db.close(commit=False)
  db = None
  table = None



def gpt1_4_make_report_line_distribution(
  pair_data_path: str,
  output_dir: str,
):
  try:
    pair_file_name = os.path.basename(pair_data_path)
    # * 자료 읽기
    pair_data = PairDataV1.from_csv(pair_data_path)


    # * 라인 수 분포
    line_lt_10 = 0
    line_lt_20 = 0
    line_lt_30 = 0
    line_lt_40 = 0
    line_lt_50 = 0
    line_lt_60 = 0
    line_lt_70 = 0
    line_lt_80 = 0
    line_lt_90 = 0
    line_lt_100 = 0
    line_ge_100 = 0 
    line_total = 0
    line_count = 0


    def process_element(pid, cid, iid, correct_code, incorrect_code, statement):
      nonlocal line_count, line_total, line_lt_10, line_lt_20, line_lt_30, line_lt_40, line_lt_50, line_lt_60, line_lt_70, line_lt_80, line_lt_90, line_lt_100, line_ge_100

      incorrect_code_line_count = len(incorrect_code)
      line_total += incorrect_code_line_count
      if incorrect_code_line_count < 10:
        line_lt_10 += 1
      elif incorrect_code_line_count < 20:
        line_lt_20 += 1
      elif incorrect_code_line_count < 30:
        line_lt_30 += 1
      elif incorrect_code_line_count < 40:
        line_lt_40 += 1
      elif incorrect_code_line_count < 50:
        line_lt_50 += 1
      elif incorrect_code_line_count < 60:
        line_lt_60 += 1
      elif incorrect_code_line_count < 70:
        line_lt_70 += 1
      elif incorrect_code_line_count < 80:
        line_lt_80 += 1
      elif incorrect_code_line_count < 90:
        line_lt_90 += 1
      elif incorrect_code_line_count < 100:
        line_lt_100 += 1
      else:
        line_ge_100 += 1
      
      line_count += 1
        

    pair_data.do_for_each(process_element)


    # * Matplotlib bar chart with percentage
    plt.clf() # clear
    img_path = os.path.join(output_dir, 'gpt1-4-line_distribution_{}.png'.format(pair_file_name))
    data = [
      line_lt_10,
      line_lt_20,
      line_lt_30,
      line_lt_40,
      line_lt_50,
      line_lt_60,
      line_lt_70,
      line_lt_80,
      line_lt_90,
      line_lt_100,
      line_ge_100,
    ]
    x = np.arange(len(data))
    plt.bar(x, data)
    plt.xticks(x, ('<10', '<20', '<30', '<40', '<50', '<60', '<70', '<80', '<90', '<100', '>=100'))
    plt.ylabel('Count')
    plt.title('Script: GPT-1-4({})\nincorrect_code line distribution (count: {} / avg_line: {:.2f})\n'.format(pair_file_name, line_count, line_total / line_count))
    plt.text(0, line_lt_10, '{:.2f}%\n({})'.format(line_lt_10 / line_total * 100, line_lt_10), ha='center', va='bottom')
    plt.text(1, line_lt_20, '{:.2f}%\n({})'.format(line_lt_20 / line_total * 100, line_lt_20), ha='center', va='bottom')
    plt.text(2, line_lt_30, '{:.2f}%\n({})'.format(line_lt_30 / line_total * 100, line_lt_30), ha='center', va='bottom')
    plt.text(3, line_lt_40, '{:.2f}%\n({})'.format(line_lt_40 / line_total * 100, line_lt_40), ha='center', va='bottom')
    plt.text(4, line_lt_50, '{:.2f}%\n({})'.format(line_lt_50 / line_total * 100, line_lt_50), ha='center', va='bottom')
    plt.text(5, line_lt_60, '{:.2f}%\n({})'.format(line_lt_60 / line_total * 100, line_lt_60), ha='center', va='bottom')
    plt.text(6, line_lt_70, '{:.2f}%\n({})'.format(line_lt_70 / line_total * 100, line_lt_70), ha='center', va='bottom')
    plt.text(7, line_lt_80, '{:.2f}%\n({})'.format(line_lt_80 / line_total * 100, line_lt_80), ha='center', va='bottom')
    plt.text(8, line_lt_90, '{:.2f}%\n({})'.format(line_lt_90 / line_total * 100, line_lt_90), ha='center', va='bottom')
    plt.text(9, line_lt_100, '{:.2f}%\n({})'.format(line_lt_100 / line_total * 100, line_lt_100), ha='center', va='bottom')
    plt.text(10, line_ge_100, '{:.2f}%\n({})'.format(line_ge_100 / line_total * 100, line_ge_100), ha='center', va='bottom')

    plt.tight_layout()
    plt.draw()
    plt.savefig(img_path, dpi=200)
  
  except Exception as e:
    logger.error(f'Failed to make report: {pair_data_path}')
    logger.error(traceback.format_exc())

  

def gpt1_4_make_report_line_no_accr(
  pair_data_path: str,
  stmt_db_path: str,
  stmt_db_table_name: str,
  output_dir: str,
):
  try:
    stmt_file_name = os.path.basename(stmt_db_path)
    pair_file_name = os.path.basename(pair_data_path)
    # * 자료 읽기
    stmt_db = Sqlite3Db(stmt_db_path)
    stmt_db_table = Sqlite3TableGpt1_2_stmt(stmt_db, stmt_db_table_name)

    pair_data = PairDataV1.from_csv(pair_data_path)

    # * line_no 예측 정확도
    line_no_correct = 0
    line_no_incorrect = 0
    line_no_failed = 0
    line_no_total = 0

    def process_element(pid, cid, iid, correct_code, incorrect_code, statement):
      nonlocal line_no_correct, line_no_incorrect, line_no_failed, line_no_total

      line_no_str, _ = statement.split(' ', 1)
      rows = stmt_db_table.query_many_pid_cid_iid(pid, cid, iid)
      if len(rows) == 0:
        line_no_failed += 1
      else:
        predict_line_no = rows[0][0]
        try:
          if predict_line_no == int(line_no_str):
            line_no_correct += 1
            # print(f'---debug\ncorrect: P{pid}C{cid}I{iid}\nline_no: {line_no_str}\n')
          else:
            line_no_incorrect += 1
        except Exception as e:
          logger.error(f'Failed to parse pair_data line_no: {line_no_str} (pid: {pid}, cid: {cid}, iid: {iid})')
          logger.error(traceback.format_exc())
          line_no_failed += 1

    pair_data.do_for_each(process_element)
    line_no_total = line_no_correct + line_no_incorrect + line_no_failed

    txt_path = os.path.join(output_dir, 'gpt1-4-line_no_accuracy.txt')
    with open(txt_path, 'w') as f:
      f.write(f'total: {line_no_total}\n')
      f.write(f'correct: {line_no_correct}\n')
      f.write(f'incorrect: {line_no_incorrect}\n')
      f.write(f'failed: {line_no_failed}\n')
      f.write(f'accuracy: {line_no_correct / line_no_total * 100:.2f}%\n')

  except Exception as e:
    logger.error(f'Failed to make report: {pair_data_path}')
    logger.error(traceback.format_exc())



# 토큰 갯수 분포 그래프
def gpt1_4_make_report_calc_tiktoken(
  token_data_path: str,
  token_data_table_name: str,
  output_dir: str,
):

  # * 데이터베이스 연결
  db = Sqlite3Db(token_data_path)
  table = Sqlite3TableGpt1_1_1(db, token_data_table_name)

  # * 데이터베이스 읽기
  token_lt_400 = 0
  token_lt_800 = 0
  token_lt_1200 = 0
  token_lt_1600 = 0
  token_lt_2000 = 0
  token_ge_2000 = 0
  token_total = 0
  token_n = 0

  count = table.count()
  cursor = table.cursor_reader_dict()

  with tqdm(total=count, desc='📖 token distribution') as pbar:
    for rows in cursor:
      for row in rows:
        token_count = row["token_count"]
        token_total += token_count
        if token_count < 400:
          token_lt_400 += 1
        elif token_count < 800:
          token_lt_800 += 1
        elif token_count < 1200:
          token_lt_1200 += 1
        elif token_count < 1600:
          token_lt_1600 += 1
        elif token_count < 2000:
          token_lt_2000 += 1
        else:
          token_ge_2000 += 1
        pbar.update(1)
        token_n += 1

  # * Matplotlib bar chart with percentage
  plt.clf() # clear
  img_path = os.path.join(output_dir, 'gpt1-4-token_distribution.png')
  data = [
    token_lt_400,
    token_lt_800,
    token_lt_1200,
    token_lt_1600,
    token_lt_2000,
    token_ge_2000,
  ]
  x = np.arange(len(data))
  plt.bar(x, data)
  plt.xticks(x, ('<400', '<800', '<1200', '<1600', '<2000', '>=2000'))
  plt.ylabel('Count')
  plt.title('Script: GPT-1-4\nincorrect_code token distribution (count: {} / avg_token: {:.2f})\n'.format(token_n, token_total / token_n))
  plt.text(0, token_lt_400, '{:.2f}%\n({})'.format(token_lt_400 / token_n * 100, token_lt_400), ha='center', va='bottom')
  plt.text(1, token_lt_800, '{:.2f}%\n({})'.format(token_lt_800 / token_n * 100, token_lt_800), ha='center', va='bottom')
  plt.text(2, token_lt_1200, '{:.2f}%\n({})'.format(token_lt_1200 / token_n * 100, token_lt_1200), ha='center', va='bottom')
  plt.text(3, token_lt_1600, '{:.2f}%\n({})'.format(token_lt_1600 / token_n * 100, token_lt_1600), ha='center', va='bottom')
  plt.text(4, token_lt_2000, '{:.2f}%\n({})'.format(token_lt_2000 / token_n * 100, token_lt_2000), ha='center', va='bottom')
  plt.text(5, token_ge_2000, '{:.2f}%\n({})'.format(token_ge_2000 / token_n * 100, token_ge_2000), ha='center', va='bottom')

  plt.tight_layout()
  plt.draw()
  plt.savefig(img_path, dpi=200)

  # * 데이터베이스 닫기
  db.close(commit=False)
  db = None
  table = None



if __name__ == '__main__':
  main()
