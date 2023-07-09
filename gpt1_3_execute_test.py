# How to use:
# python lyk/gpt1_3_execute_test.py
'''
python lyk/gpt1_3_execute_test.py \
  --dataset valid \
  --pair_data_path data/edit_distance/refined_pair_code_edit_dist_valid.txt \
  --workspace lyk/output/tmp/gpt1_3/gpt1_3_lcs_refined_valid \
  --stmt_db_path lyk/output/gpt1_2_lcs_refined_valid.db \
  --output_db_path lyk/output/gpt1_3_lcs_refined_valid_gpp17.db \
  --processes 12 \
  --timeout 2
'''
'''
python lyk/gpt1_3_execute_test.py \
  --dataset valid \
  --pair_data_path data/edit_distance/refined_pair_code_edit_dist_valid.txt \
  --workspace lyk/output/tmp/gpt1_3/gpt1_3_lsh_refined_valid \
  --stmt_db_path lyk/output/gpt1_2_lsh_refined_valid.db \
  --output_db_path lyk/output/gpt1_3_lsh_refined_valid_gpp17.db \
  --processes 12 \
  --timeout 2
'''
'''
python lyk/gpt1_3_execute_test.py \
  --dataset valid \
  --pair_data_path data/edit_distance/refined_pair_code_edit_dist_valid.txt \
  --workspace lyk/output/tmp/gpt1_3/gpt1_3_lshv3_refined_valid \
  --stmt_db_path lyk/output/gpt1_2_lshv3_refined_valid.db \
  --output_db_path lyk/output/gpt1_3_lshv3_refined_valid_gpp17.db \
  --processes 12 \
  --timeout 2
'''
'''
python lyk/gpt1_3_execute_test.py \
  --dataset valid \
  --pair_data_path data/edit_distance/refined_pair_code_edit_dist_valid.txt \
  --workspace lyk/output/tmp/gpt1_3/gpt1_3_lshv2fs_refined_valid \
  --stmt_db_path lyk/output/gpt1_2_lshv2fs_refined_valid.db \
  --output_db_path lyk/output/gpt1_3_lshv2fs_refined_valid_gpp17.db \
  --processes 12 \
  --timeout 2
'''

import argparse
import multiprocessing
import os
import re
import time
import traceback
from typing import List, Dict, Tuple, Iterable, Any
import subprocess
import sys

from tqdm import tqdm
import pandas as pd

from utils import gpp14_compile_code, gpp17_compile_code, Sqlite3Db, Sqlite3TableGpt1_2_stmt, Sqlite3TableGpt1_3, PairDataV1, PDCodeV1



def main():
  # unit_test_execute_test()

  parser = argparse.ArgumentParser()
  parser.add_argument('--dataset', type=str, default='valid',
    help='데이터셋 이름 (train, valid, test)')
  parser.add_argument('--pair_data_path', type=str, default='data/edit_distance/refined_pair_code_edit_dist_valid.txt',
    help='pair data가 있는 파일 경로')
  parser.add_argument('--workspace', type=str, default='lyk/output/tmp/gpt1_3_NAME',
    help='임시 작업 폴더 경로 (컴파일 결과물 등)')
  parser.add_argument('--stmt_db_path', type=str, default='lyk/output/gpt1_2_NAME.db',
    help='GPT가 생성한 stmt 데이터베이스 파일 경로')
  parser.add_argument('--stmt_db_table_name', type=str, default='',
    help='GPT가 생성한 stmt 데이터베이스 테이블 이름 (비우면 기본값)')
  parser.add_argument('--output_db_path', type=str, default='lyk/output/gpt1_3_NAME.db',
    help='출력 데이터베이스 파일 경로')
  parser.add_argument('--output_db_table_name', type=str, default='',
    help='출력 데이터베이스 테이블 이름 (비우면 기본값)')
  parser.add_argument('--processes', type=int, default=multiprocessing.cpu_count(),
    help='프로세스 개수')
  parser.add_argument('--timeout', type=int, default=2,
    help='제한 시간 (초) (보통 2초)')
  args = parser.parse_args()

  gpt1_3_execute_test_stmt_dir(
    dataset = args.dataset,
    pair_data_path = args.pair_data_path,
    workspace = args.workspace,
    stmt_db_path = args.stmt_db_path,
    stmt_db_table_name = args.stmt_db_table_name,
    output_db_path = args.output_db_path,
    output_db_table_name = args.output_db_table_name,
    processes = args.processes,
    timeout = args.timeout,
  )
  


# TDD 멀티스레드 함수 유닛 테스트
def unit_test_execute_test():
  # 테스트 할 코드
  code = '''
  #include <iostream>
  using namespace std;
  int main() {
    int a, b;
    cin >> a >> b;
    cout << a + b << endl;
    return 0;
  }
  '''
  # 컴파일 된 실행 파일
  exec_file = 'lyk/output/execute_test.exe'
  # 테스트 할 입력
  inputs = [
    '1 2',
    '3 4',
    '5 6',
  ]
  # 예상되는 정답 출력
  outputs = [
    '3',
    '7',
    '-1',
  ]
  # 제한 시간 (초) (보통 2초)
  timeout = 2

  # 테스트
  result = execute_test(
    ('P0C0I0', code, exec_file, inputs, outputs, timeout),
  )
  print(result) # ('P0C0I0', ['AC', 'AC', 'WA'])
  assert result == ('P0C0I0', ['AC', 'AC', 'WA'])

  code = '''
  #include <iostream>
  using namespace std;
  int main() {
    int a, b;
    cinasdfasdf >> a >> b;
    cout << a + b << endl;
    return 0;
  }
  '''
  result = execute_test(
    ('P0C0I0', code, exec_file, inputs, outputs, timeout),
  )
  print(result) # ('P0C0I0', ['CE', 'CE', 'CE'])
  assert result == ('P0C0I0', ['CE', 'CE', 'CE'])



# 멀티 프로세스로 실행될 테스트 함수
# 테스트 결과 (AC (Accept), TLE (Time Limit Exceeded), WA (Wrong Answer), RE(Runtime Error), CE (Compile Error) 리스트)
def execute_test(
  args: Tuple[str, str, str, List[str], List[str], int],
  # uid: str, # 구분용 인덱스 (일반적으로, P{pid}C{cid}I{iid} 형식)
  # code: str, # 테스트 할 코드, 혹은 AC, WA, TLE, CE, RE 일 경우 결과값으로 반환
  # exec_file: str, # 컴파일 된 실행 파일
  # inputs: List[str], # 테스트 할 입력
  # outputs: List[str], # 예상되는 정답 출력
  # timeout: int, # 제한 시간 (초) (보통 2초)
) -> Tuple[str, List[str]]: # uid, 테스트 결과 리스트
  try:
    # 인수 풀기
    uid, code, exec_file, inputs, outputs, timeout = args

    # code검사
    if code in ['AC', 'WA', 'TLE', 'CE', 'RE']:
      return (uid, [code] * len(inputs))

    # 컴파일
    returncode, stdout, stderr = gpp17_compile_code(code, exec_file)
    if returncode != 0:
      # print(f'Compile Error: {uid} {returncode} {stdout} {stderr}')
      return (uid, ['CE'] * len(inputs))

    # 테스트
    results = []
    for input, output in zip(inputs, outputs):
      # 실행 파일을 subprocess를 통해 실행, timeout 시간을 넘어가면 프로세스를 종료
      proc = subprocess.Popen(
        [exec_file],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
      )
      try:
        stdout_data, stderr_data = proc.communicate(input.encode(), timeout=timeout)
      except subprocess.TimeoutExpired:
        proc.kill()
        results.append('TLE')
        continue

      # stderr가 비어 있지 않으면 RE
      if stderr_data:
        results.append('RE')
        continue
      # 테스트 결과를 저장
      if stdout_data.decode().strip() == output.strip():
        results.append('AC')
      else:
        results.append('WA')
    
    # 테스트 결과를 반환
    return (uid, results)
  # Catch All Exception
  except Exception as e:
    # Print stack trace
    print(e)
    traceback.print_exc()
    return (uid, ['CE'] * len(inputs))
  


# 멀티 프로세스로 gcc 테스트를 실행하는 함수
def multi_process_execute_test(
  processes: int, # 프로세스 개수, 비어 있으면 CPU 개수로 설정
  task_count: int, # 전체 테스트 개수
  data_iter: Iterable[Tuple[str, str, str, List[str], List[str], int]],
  # uid: str, # 구분용 인덱스 (일반적으로, P{pid}C{cid}I{iid} 형식)
  # code: str, # 테스트 할 코드
  # exec_file: str, # 컴파일 된 실행 파일
  # inputs: List[str], # 테스트 할 입력
  # outputs: List[str], # 예상되는 정답 출력
  # timeout: int, # 제한 시간 (초) (보통 2초)
) -> Iterable[Tuple[str, List[str]]]: # uid, 테스트 결과 리스트

  # processes가 설정 안되어 있으면 CPU 개수로 설정
  if not processes:
    processes = multiprocessing.cpu_count()

  # with tqdm, Pool, imap_unordered
  with tqdm(total=task_count) as pbar:
    with multiprocessing.Pool(processes=processes) as pool:
      for result in pool.imap_unordered(execute_test, data_iter):
        pbar.update(1)
        yield result

    # cleanup
    pool.close()
    pool.join()



# 싱글 스레드로 gcc 테스트를 실행하는 함수
def single_process_execute_test(
  task_count: int, # 전체 테스트 개수
  data_iter: Iterable[Tuple[str, str, str, List[str], List[str], int]],
  # uid: str, # 구분용 인덱스 (일반적으로, P{pid}C{cid}I{iid} 형식)
  # code: str, # 테스트 할 코드
  # exec_file: str, # 컴파일 된 실행 파일
  # inputs: List[str], # 테스트 할 입력
  # outputs: List[str], # 예상되는 정답 출력
  # timeout: int, # 제한 시간 (초) (보통 2초)
) -> Iterable[Tuple[str, List[str]]]: # uid, 테스트 결과 리스트

  # with tqdm, imap
  with tqdm(total=task_count) as pbar:
    for result in map(execute_test, data_iter):
      pbar.update(1)
      yield result



# input, output sample 들을 읽어오는 함수
def read_samples(
  dataset: str, # 데이터셋 이름 (train, valid, test)
  pid: str or int, # 프로그램 아이디
) -> Tuple[List[str], List[str]]:
  public_testcases_path = f'data/samples_{dataset}/{str(pid)}.txt'
  private_testcases_path = f'data/private_samples_{dataset}/{str(pid)}.txt'
  generated_testcases_path =  f'data/generated_samples_{dataset}/{str(pid)}.txt'
        
  def add_testcase(filename, inputs, outputs):
    with open(filename, 'r') as f:
      lines = f.readlines()
      for l in range(0,len(lines), 2):
        input = lines[l].split('"')
        if len(input) < 2:
          break
        input = input[1]
        output = lines[l+1].split('"')[1]

        inputs.append(input)
        outputs.append(output)
              
  inputs, outputs = [], []
  add_testcase(public_testcases_path, inputs, outputs)
  add_testcase(private_testcases_path, inputs, outputs)
  add_testcase(generated_testcases_path, inputs, outputs)

  return inputs, outputs



# GPT가 생성한 stmt로 고장난 코드를 고쳐 테스트 후 디비에 저장
def gpt1_3_execute_test_stmt_dir(
  dataset: str, # 데이터셋 이름 (train, valid, test)
  pair_data_path: str, # pair data가 있는 파일 경로
  workspace: str, # 작업 폴더 경로
  stmt_db_path: str, # GPT가 생성한 stmt 데이터베이스 파일 경로
  stmt_db_table_name: str, # GPT가 생성한 stmt 데이터베이스 테이블 이름
  output_db_path: str, # 데이터베이스 파일 경로
  output_db_table_name: str, # 데이터베이스 테이블 이름
  processes: int, # 프로세스 개수
  timeout: int, # 제한 시간 (초) (보통 2초)
) -> None:

  # 작업 폴더 생성 mkdir -p
  if not os.path.exists(workspace):
    os.makedirs(workspace)

  # pair data를 읽어옴
  pair_data = PairDataV1.from_csv(pair_data_path)

  # GPT가 생성한 stmt 데이터베이스 연결 (읽기 전용이라 try except db.close 필요 없음)
  stmt_db = Sqlite3Db(stmt_db_path)
  stmt_db_table = Sqlite3TableGpt1_2_stmt(stmt_db, stmt_db_table_name)
  stmt_db_count = stmt_db_table.count()
  # !!! 멀티프로세스 제너레이터 안에서 DB 인스턴스 접근 불가로 인해 모든 데이터를 preload 함 (수정 필요할 수 있음)
  stmt_db_rows = []
  cursor = stmt_db_table.cursor_reader_dict(batch_size=1000)
  for rows in cursor:
    for row in rows:
      stmt_db_rows.append(row)

  # Fail safe required: 멀티프로세싱용 제너레이터
  def generator_read_data(
    stmt_db_rows: List[Dict[str, Any]],
    pair_data: PairDataV1,
    timeout: int,
  ) -> Iterable[Tuple[str, str, str, List[str], List[str], int]]:
    debug_name = ''
    try:
      uid = ''
      code = ''
      exec_file = ''
      inputs = []
      outputs = []
      timeout = timeout

      incorrect_code = ''

      # * GPT가 생성한 stmt 데이터베이스 loop
      for row in stmt_db_rows:
        pid = row['pid']
        cid = row['cid']
        iid = row['iid']
        line_no = row['line_no']
        stmt = row['stmt']

        # *** 구분용 인덱스
        uid = f'P{pid}C{cid}I{iid}'
        # 멀티 프로세싱 추가 디버깅 정보 제공용
        debug_name = uid
        # *** 컴파일 된 실행 파일
        exec_file = os.path.join(workspace, f'{uid}.exe')

        # pair_data에서 pid, cid, iid에 해당하는 incorrect_code를 찾음
        incorrect_code = ''
        ret = pair_data.find_by_pid_cid_iid(int(pid), int(cid), int(iid))
        if ret[0] != -1:
          incorrect_code = ret[1][4]

        # * incorrect_code가 비어 있으면 테스트 크래시 (stmt 셋을 생성하는데 사용된 pair_data가 아닐 가능성이 높음)
        if not incorrect_code:
          print(f'Not exists pair data in pair_data: {uid}')
          exit(1)
        else:
          incorrect_pdcode = PDCodeV1.from_str(incorrect_code)
          # * 변경된 코드가 원본 코드 범위 밖이면 Compile Error처리
          if len(incorrect_pdcode) < line_no:
            code = 'CE'
          else:
            # * 해당 라인 코드 변경
            incorrect_pdcode.change_line(line_no, stmt)
            code = incorrect_pdcode.to_code() # 줄번호 없이 \n로 구분된 코드
            # ********** code 조립 과정 끝 **********
        
        # * 테스트 할 입력과 예상되는 정답 출력을 생성
        inputs, outputs = read_samples(dataset, pid)
        if len(inputs) != len(outputs):
          print(f'Invalid samples in data/samples_{dataset}/{pid}.txt')
          exit(1)

        # * 테스트 generator
        yield (uid, code, exec_file, inputs, outputs, timeout)
    # Catch all Exception
    except Exception as e:
      # Print stack trace
      print(f'debug_name {debug_name}', e)
      traceback.print_exc()
      # Exit with error code
      exit(1)
    
  # generator_read_data를 multi_process_execute_test에 넣어서 실행
  result_iter = multi_process_execute_test(
    processes,
    stmt_db_count,
    generator_read_data(
      stmt_db_rows,
      pair_data,
      timeout,
    ),
  )
  # # 디버깅용 싱글 스레드 솔루션
  # result_iter = single_process_execute_test(
  #   stmt_db_count,
  #   generator_read_data(
  #     stmt_db_rows,
  #     pair_data,
  #     timeout,
  #   ),
  # )

  # stmt 데이터베이스 종료
  stmt_db.close()
  stmt_db = None
  stmt_db_table = None

  # 테스트 결과를 데이터베이스에 저장
  db = Sqlite3Db(db_file = output_db_path)
  db_table = Sqlite3TableGpt1_3(sqlite3db = db, table_name = output_db_table_name)
  for uid, results in result_iter:
    # Parse pid, cid, iid
    pid, cid, iid = re.match(r'P(\d+)C(\d+)I(\d+)', uid).groups()
    # Insert into database
    db_table.safe_insert_many_tuple([
      (pid, cid, iid, i, result)
      for i, result in enumerate(results)
    ])
  
  # 데이터베이스 종료
  db.close()
  db = None
  db_table = None



if __name__ == '__main__':
  main()
