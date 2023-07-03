# How to use:
# python lyk/gpt1-4-make-report.py

import argparse
import logging
import os

import matplotlib.pyplot as plt
import numpy as np
from tqdm import tqdm

from utils import Sqlite3Db, Sqlite3TableGpt1_3

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

def main():
  parser = argparse.ArgumentParser()
  parser.add_argument('--db_path', type=str, default='lyk/output/gpt1-3-lcs/gpt1-lcs.db',
    help='데이터베이스 경로')
  parser.add_argument('--table_name', type=str, default='',
    help='데이터베이스 테이블 이름 (비우면 기본값)')
  parser.add_argument('--pair_data_path', type=str, default='data/edit_distance/refined_pair_code_edit_dist_valid.txt',
    help='원본 데이터 쌍 경로')
  parser.add_argument('')
  parser.add_argument('--output_dir', type=str, default='lyk/output/gpt1-4-lcs',
    help='출력 폴더 경로')

  args = parser.parse_args()

  db_path = args.db_path
  table_name = args.table_name
  output_dir = args.output_dir

  # * 폴더 생성
  os.makedirs(output_dir, exist_ok=True)

  # * 보고서 생성: AC, TLE, WA, RE, CE 비율
  gpt1_4_make_report_ratio(
    db_path=db_path,
    table_name=table_name,
    output_dir=output_dir
  )



def gpt1_4_make_report_ratio(
  db_path: str,
  table_name: str,
  output_dir: str
):
  file_name = os.path.basename(db_path)
  # * 데이터베이스 연결
  db = Sqlite3Db(db_path)
  table = Sqlite3TableGpt1_3(db, table_name)

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
  plt.title(f'GPT-1-4({file_name}) all ratio (count: {count})\n')
  plt.text(0, ac, '{:.2f}%\n({})'.format(ac / count * 100, ac), ha='center', va='bottom')
  plt.text(1, tle, '{:.2f}%\n({})'.format(tle / count * 100, tle), ha='center', va='bottom')
  plt.text(2, wa, '{:.2f}%\n({})'.format(wa / count * 100, wa), ha='center', va='bottom')
  plt.text(3, re, '{:.2f}%\n({})'.format(re / count * 100, re), ha='center', va='bottom')
  plt.text(4, ce, '{:.2f}%\n({})'.format(ce / count * 100, ce), ha='center', va='bottom')
  
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
  plt.title(f'GPT-1-4({file_name}) per incorrect_code ratio (count: {count})\n')
  plt.text(0, ac, '{:.2f}%\n({})'.format(ac / count * 100, ac), ha='center', va='bottom')
  plt.text(1, tle, '{:.2f}%\n({})'.format(tle / count * 100, tle), ha='center', va='bottom')
  plt.text(2, wa, '{:.2f}%\n({})'.format(wa / count * 100, wa), ha='center', va='bottom')
  plt.text(3, re, '{:.2f}%\n({})'.format(re / count * 100, re), ha='center', va='bottom')
  plt.text(4, ce, '{:.2f}%\n({})'.format(ce / count * 100, ce), ha='center', va='bottom')

  plt.draw()
  plt.savefig(img_path, dpi=200)



  # * 데이터베이스 닫기
  db.close(commit=False)
  db = None
  table = None



if __name__ == '__main__':
  main()
