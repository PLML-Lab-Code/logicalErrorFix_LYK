# How to use:
# python lyk/gpt1-3-execute_test.py

import argparse
import multiprocessing
import os
import re
import time
import traceback
from typing import List, Dict, Tuple, Iterable
import subprocess
import sys

from tqdm import tqdm
import pandas as pd

from utils import gpp14_compile_code, Sqlite3Db, Sqlite3TableExecute, PairDataV1, PDCodeV1



def main():
  # unit_test_execute_test()

  parser = argparse.ArgumentParser()
  parser.add_argument('--dataset', type=str, default='valid',
    help='데이터셋 이름 (train, valid, test)')
  parser.add_argument('--gpt_stmt_dir', type=str, default='lyk/output/gpt1-lcs-code',
    help='GPT가 생성한 stmt들이 있는 폴더 경로')
  parser.add_argument('--pair_data_path', type=str, default='data/edit_distance/refined_pair_code_edit_dist_valid.txt',
    help='pair data가 있는 파일 경로')
  parser.add_argument('--workspace', type=str, default='lyk/output/gpt1-3/gpt1-lcs',
    help='작업 폴더 경로')
  parser.add_argument('--db_path', type=str, default='lyk/output/gpt1-3/gpt1-lcs.db',
    help='데이터베이스 파일 경로')
  parser.add_argument('--db_table_name', type=str, default='',
    help='데이터베이스 테이블 이름 (비우면 기본값)')
  parser.add_argument('--processes', type=int, default=multiprocessing.cpu_count(),
    help='프로세스 개수')
  parser.add_argument('--timeout', type=int, default=2,
    help='제한 시간 (초) (보통 2초)')
  args = parser.parse_args()

  gpt1_3_execute_test_stmt_dir(
    dataset = args.dataset,
    gpt_stmt_dir = args.gpt_stmt_dir,
    pair_data_path = args.pair_data_path,
    workspace = args.workspace,
    db_path = args.db_path,
    db_table_name = args.db_table_name,
    processes = args.processes,
    timeout = args.timeout,
  )
  


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
# 테스트 결과 (AC (Accept), WA (Wrong Answer), TLE (Time Limit Exceeded), CE (Compile Error), RE(Runtime Error) 리스트)
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
    returncode, stdout, stderr = gpp14_compile_code(code, exec_file)
    if returncode != 0:
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
  gpt_stmt_dir: str, # GPT가 생성한 stmt들이 있는 폴더 경로
  pair_data_path: str, # pair data가 있는 파일 경로
  workspace: str, # 작업 폴더 경로
  db_path: str, # 데이터베이스 파일 경로
  db_table_name: str, # 데이터베이스 테이블 이름
  processes: int, # 프로세스 개수
  timeout: int, # 제한 시간 (초) (보통 2초)
) -> None:

  # 작업 폴더 생성 mkdir -p
  if not os.path.exists(workspace):
    os.makedirs(workspace)

  # 폴더 내 파일 리스트
  file_list = os.listdir(gpt_stmt_dir)

  # pair data를 읽어옴
  pair_data = PairDataV1.from_csv(pair_data_path)

  # 폴더 내 파일들로 for loop
  for file_name in file_list:
    # 파일 이름이 'P[pid]C[cid]I[iid].txt' 인지 확인하고 아니면 exit
    if not re.match(r'P\d+C\d+I\d+.txt', file_name):
      print(f'Invalid file name in gpt_stmt_dir: {file_name}')
      exit(1)

  # Fail safe required: this generator run in subprocess
  def generator_read_data(
    gpt_stmt_dir: str,
    processes: int,
    file_list: List[str],
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

      # 폴더 내 파일들로 for loop
      for file_name in file_list:
        debug_name = file_name
        # 파일 경로
        file_path = os.path.join(gpt_stmt_dir, file_name)
        # 파일 이름 'P[pid]C[cid]I[iid].txt' Regex로 분리
        pid, cid, iid = re.match(r'P(\d+)C(\d+)I(\d+).txt', file_name).groups()
        # *** 구분용 인덱스
        uid = f'P{pid}C{cid}I{iid}'
        # *** 컴파일 된 실행 파일
        exec_file = os.path.join(workspace, f'{uid}.exe')

        # 예측된 수정 내용 파일
        with open(file_path, 'r') as f:
          file_content = f.read()
        # 파일 내용 앞부분의 공백만 제거
        file_content = file_content.lstrip()
        line_no_and_stmts = file_content.split(' ', 1)

        # * 예측 파일 길이가 맞지 않으면 테스트 크래시
        if len(line_no_and_stmts) != 2:
          print(f'Invalid file content in gpt_stmt_dir: {file_path}')
          exit(1)
        else:
          # 첫 공백으로 분리된 첫 번째 값이 line_no
          line_no = int(line_no_and_stmts[0])
          # 첫 공백으로 분리된 두 번째 값이 stmt
          stmt = line_no_and_stmts[1]

          # pair_data에서 pid, cid, iid에 해당하는 incorrect_code를 찾음
          incorrect_code = ''
          ret = pair_data.find_by_pid_cid_iid(int(pid), int(cid), int(iid))
          if ret[0] != -1:
            incorrect_code = ret[1][4]

          # * incorrect_code가 비어 있으면 테스트 크래시 (stmt 셋을 생성하는데 사용된 pair_data가 아님)
          if not incorrect_code:
            print(f'Not exists pair data in pair_data: {uid}')
            exit(1)
          else:
            incorrect_pdcode = PDCodeV1.from_str(incorrect_code)
            # * 변경된 코드가 원본 코드 범위 밖이면 Compile Error처리
            if len(incorrect_pdcode) < line_no:
              code = 'CE'
            else:
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
    len(file_list),
    generator_read_data(
      gpt_stmt_dir,
      processes,
      file_list,
      pair_data,
      timeout,
    ),
  )
  # result_iter = single_process_execute_test(
  #   len(file_list),
  #   generator_read_data(
  #     gpt_stmt_dir,
  #     processes,
  #     file_list,
  #     pair_data,
  #     timeout,
  #   ),
  # )

  # 테스트 결과를 데이터베이스에 저장
  db = Sqlite3Db(db_file = db_path)
  db_table = Sqlite3TableExecute(sqlite3db = db, table_name = db_table_name)
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



# 아래는 이전 코드

# def execute(idx, exec_file, input, output, msg_file, return_dict):
#   # preprocessing for execute
#   input_file = f'lyk/output/gpt1-3/execute/input_{idx}.txt'
#   output_file = f'lyk/output/gpt1-3/execute/output_{idx}.txt'
#   gold_file = f'lyk/output/gpt1-3/execute/gold_{idx}.txt'
#   if os.path.exists(input_file):
#     os.system(f'rm {input_file}')
#   if os.path.exists(output_file):
#     os.system(f'rm {output_file}')
#   if os.path.exists(gold_file):
#     os.system(f'rm {gold_file}')
  
#   # Sample Input
#   input_lines = input.split('\\n')
#   with open(input_file, 'w') as f:
#     for input_line in input_lines:
#       f.write(input_line.strip()+' ')

#   # Sample Output (gold answer)
#   output_lines = output.split('\\n')
#   with open(gold_file, 'w') as f:
#     for output_line in output_lines:
#       f.write(output_line.strip()+' ')

#   # run and check TLE (Time Limit Exceeded)
#   return_dict[idx] = 'TLE'
#   # run and check RE (Runtime Error)
#   os.system(f'timeout 2 ./{exec_file} < {input_file} > {output_file} 2> {msg_file}')
#   # check msg_file is empty for RE
#   if os.stat(msg_file).st_size != 0:
#     return_dict[idx] = 'RE'
#     return
  
# # compare output and gold for judging WA (Wrong Answer) or AC (Accepted)
# with open(output_file, 'r') as f, open(gold_file, 'r') as f1:
#   program_output_lines = f.readlines()
#   program_output = ''
#   for program_output_line in program_output_lines:
#     program_output += program_output_line.strip() + ' '
#   program_output = ' '.join(program_output.split())

#   gold_output = f1.readline().strip()
#   gold_output = ' '.join(gold_output.split())            

#   # check WA (Wrong Answer)
#   if program_output.strip() != gold_output.strip():
#     return_dict[idx] = 'WA'
#     with open(msg_file, 'w') as f:
#       f.write(program_output.strip())
#   else:
#     # AC (Accepted)
#     return_dict[idx] = 'AC'

# # 잘못 된 코드를 고쳐진 코드로 바꾸어 
# def judge(
#   msg_dir_name: str, # 컴파일 로그들을 출력하는 작업 폴더명
#   beam_size: str, # 빔 사이즈 (predict_stmt의 개수와 동일하거나 낮아야함)
#   incorrect_code_data: [str, str, str, str], # [program_id, correct_id, incorrect_id, incorrect_code]
#   predict_stmt: List[Tuple[int, str]], # [(idx, stmt), ...]
# ):
#   # Base directory
#   MSG_DIR = f'lyk/output/gpt1-3/msg_dir/{msg_dir_name}'
#   if not os.path.exists(MSG_DIR):
#     os.mkdir(MSG_DIR)
    
#   # * incorrect code 준비
#   result_to_top = []
#   pid, cid, iid ,incorrect_code = incorrect_code_data
#   incorrect_code_lines = incorrect_code.split('|||')

#   # * 빔 사이즈 만큼 반복
#   for beam in range(beam_size):
#     tmp_idx, stmt = predict_stmt[beam]
#     predict_line_no = stmt.split(' ', 1)[0]

#     # line_no 제거 후 repair_code
#     repair_code = ''
#     for incorrect_code_line in incorrect_code_lines:
#       incorrect_code_line = incorrect_code_line.strip()
#       # [line_no, code]
#       incorrect_code_line_data = incorrect_code_line.split(' ', 1)
#       # 제대로 된 형식이 아니면 break
#       if len(incorrect_code_line_data) < 2:
#         break
#       line_no, incorrect_code = incorrect_code_line_data 

#       # 라인번호가 같으면 코드 덮어쓰기
#       if predict_line_no == line_no: 
#         line = stmt   
#         s_line_parse = incorrect_code_line.split(' ', 1)
#         if len(s_line_parse) < 2:
#           incorrect_code = ''
#         else:
#           incorrect_code = s_line_parse[1]
#       # !!! 에러 짐작: 잘못된 코드를 더하고 있음
#       repair_code += incorrect_code + '|||'

#     # preprocess for compile
#     source_file = 'data/tmp/source.cpp'
#     exec_file = 'data/tmp/exec_2slee.exe'
#     if os.path.exists(source_file):
#       os.system('rm {}'.format(source_file))
#     if os.path.exists(exec_file):
#       os.system('rm {}'.format(exec_file))
#     with open(source_file, 'w') as f:
#       lines = repair_code.split('|||')
#       for line in lines:
#         f.write(line.strip()+'\n')


#     # compile
#     ce_msg_file = f'{MSG_DIR}/ce_{pid}_{iid}_{beam}.txt'
#     os.system('g++ ' + source_file + ' -o ' + exec_file + ' 2> ' + ce_msg_file)
#     if not os.path.exists(exec_file):
#       result_to_top.append('CE')
#       continue


#     # make samples
#     public_testcases_path = f'../data/samples_{dataset}/{pid}.txt'
#     private_testcases_path = f'../data/private_samples_{dataset}/{pid}.txt'
#     generated_testcases_path = f'../data/generated_samples_{dataset}/{pid}.txt'
    
#     def add_testcase(filename, inputs, outputs):
#       with open(filename, 'r') as f:
#         lines = f.readlines()
#         for l in range(0,len(lines), 2):
#           input = lines[l].split('"')
#           if len(input) < 2:
#             break
#           input = input[1]
#           output = lines[l+1].split('"')[1]

#           inputs.append(input)
#           outputs.append(output)
          
#     inputs, outputs = [], []
#     add_testcase(public_testcases_path,inputs,outputs)
#     add_testcase(private_testcases_path,inputs,outputs)
#     add_testcase(generated_testcases_path,inputs,outputs)

#     max_sample_size = 200
#     if len(inputs) > max_sample_size and len(outputs) > max_sample_size:
#       inputs = inputs[:max_sample_size]
#       outputs = outputs[:max_sample_size]


#     # execute all samples with multiprocessing
#     n_sample = len(inputs)
#     n_thread = 40
#     n = n_sample // n_thread
    
#     cnt_RE, cnt_TLE, cnt_WA, cnt_AC = 0, 0, 0, 0
#     for i in range(n+1):
#       return_dict = Manager().dict()
#       jobs = []
#       for j in range(n_thread):
#         idx = n_thread*i+j
#         if idx >= len(inputs):
#           break    
        
#         exec_msg_file = f'{MSG_DIR}/exec_{pid}_{iid}_{beam}_{idx}.txt'
#         p = Process(target=execute, args=(idx, exec_file, inputs[idx], outputs[idx], exec_msg_file, return_dict), daemon=True)
#         p.start()
#         jobs.append(p)
        
#       for proc in jobs:
#         proc.join()
        
#       for proc in jobs:
#         proc.terminate()
      
#       for ret in return_dict.values():
#         cnt_RE += (ret == 'RE') 
#         cnt_TLE += (ret == 'TLE')
#         cnt_WA += (ret == 'WA')
#         cnt_AC += (ret == 'AC')
    
#     if cnt_RE != 0:
#       result_to_top.append('RE')
#     elif cnt_TLE != 0:
#       result_to_top.append('TLE')
#     elif cnt_WA != 0:
#       result_to_top.append('WA')
#     else:
#       result_to_top.append('AC')

#   return pid, cid, iid ,result_to_top
  
# def compile_and_execute(lang, model, epoch, detail, dataset, beam_size, csv_file):

#   # data load
#   incorrect_code_path = f'data/edit_distance/drop_by_iid_pair_code_edit_dist_{dataset}.txt'
#   incorrect_code = pd.read_csv(incorrect_code_path, sep='\t')
#   incorrect_code = incorrect_code[['PID', 'CID', 'IID', 'Incorrect_code']].values.tolist()
#   predict_stmt_path = f'../model/{lang}_{model}/epoch_{epoch}/checkpoint-{detail}/{dataset}_0.output' # model/cpp_epoch_beam/checkpoint-best-bleu/test_0.output
#   predict_stmt = pd.read_csv(predict_stmt_path, sep='\t', header=None).values.tolist() # idx, stmt
  
  
#   # judge(compile and execute) with multi-threading
#   n_pred = len(incorrect_code)
#   result_to_csv = []
#   for i in range(n_pred):
#     if i % 100 == 0:
#       print(f'idx : {i}')

#     # [pid, cid, iid, incorrect_code]
#     result = judge(
#       f'{model}-{epoch}-{detail}-{dataset}',
#       beam_size,
#       incorrect_code[i],
#       predict_stmt[beam_size*i:beam_size*(i+1)]
#     )
#     result_to_csv.append(result)

#   df = pd.DataFrame(result_to_csv, columns=['PID', 'CID', 'IID', 'RESULT'])
#   df.to_csv(csv_file, index=False)
  

# def get_ret(csv_file, top):

#   df = pd.read_csv(csv_file)
#   df = df['RESULT'].values.tolist()
#   s = df[0][1:-1]
#   sl = s.split(',') 
#   sl = [i.strip()[1:-1] for i in sl]

#   n = len(df)
  
#   sums = [0]*4
#   for i in range(n):
#     ret = [0]*4
#     sl = df[i][1:-1].split(',')
#     sl = [i.strip()[1:-1] for i in sl]
#     for j in range(10):
#       if j >= top:
#         continue
      
#       ret[0] += (sl[j] == 'CE')
#       ret[1] += (sl[j] == 'RE') | (sl[j] == 'TLE')
#       ret[2] += (sl[j] == 'WA')
#       ret[3] += (sl[j] == 'AC')

#     if ret[3]: # ac
#       sums[3] += 1
#     elif ret[2]: # wa
#       sums[2] += 1
#     elif ret[1]: # re
#       sums[1] += 1
#     else:     # ce
#       sums[0] += 1
#   sums = [round(s/n*100, 1) for s in sums]
#   sums.reverse()
#   return sums

# def eval_localization_precision(lang, model, epoch, detail, dataset, top, beam_size=10):

#   '''
#   라인넘버 예측이 잘 되었는지 확인하는 모듈
#   '''

#   DIR = f'../model/{lang}_{model}/epoch_{epoch}/checkpoint-{detail}'
#   fgold = DIR + '/'+dataset+'_0.gold'
#   foutput = DIR +'/'+dataset+'_0.output'

#   ret = 0.0
#   with open(fgold, 'r') as g, open(foutput, 'r') as o:
#     lines_gold = g.readlines()
#     lines_output = o.readlines()
    
#     localization = 0
#     for i, line_g in enumerate(lines_gold):
#       line_no_g = line_g.split('\t')[1].split(' ', 1)[0]
#       for j in range(beam_size):
#         if j >= top:
#           break
        
#         idx = beam_size * i + j
#         line_o = lines_output[idx]
#         line_no_o = line_o.split('\t')[1].split(' ', 1)[0]
        
#         if line_no_g == line_no_o:
#           localization += 1
#           break
    
#     ret = round(localization/len(lines_gold)*100, 1)
    
#   return ret

    
    

# if __name__ == '__main__':
#   '''
#   datasets = ['test', 'valid', 'train']
#   models = ['cpp_epoch_beam', 'cpp_line_beam/cpp_epoch_54', 'cpp_line_beam/cpp_epoch_28', 'cpp_neulab', 'cpp_refine', 'cpp_incorrect_refine']
#   epochs = ['28', '14', '10', '6', '3']
#   '''
#   # edit here #
#   langs = ['cpp']         
#   models = ['incorrect_refined']
#   epochs =['14']
#   details = ['best-bleu', 'last']
#   datasets = ['valid']
#   beam_size = 10 
  
#   # edit end #
  
  
#   '''
#   # compile_and_execute
#   freeze_support()
#   for lang in langs:
#     for model in models:
#       for epoch in epochs:
#         for detail in details:
#           for dataset in datasets:
#             csv_file = f'data/judge_result/result_{lang}_{model}_{epoch}_{detail}_{dataset}.csv'
            
#             start_time = time.time()
#             compile_and_execute(lang, model, epoch, detail, dataset, beam_size, csv_file)
#             end_time = time.time()
#             print(f'{end_time-start_time} sec')

#   '''  
#   # get_result with csv
#   for lang in langs:
#     for model in models:
#       for epoch in epochs:
#         for detail in details:
#           for dataset in datasets:
#             print(f'model/{lang}_{model}/epoch_{epoch}/checkpoint-{detail}/{dataset}')
#             print('[AC, WA, RE, CE] localization')
#             for top in [1, 5, 10]:
#               csv_file = f'data/judge_result/result_{lang}_{model}_{epoch}_{detail}_{dataset}.csv'
              
#               percentage = get_ret(csv_file, top)
#               localization = eval_localization_precision(lang, model, epoch, detail, dataset, top)
              
#               print(percentage, localization)
              