# `fl2-1-convert_dataset.py`
#   - 기존 `refined_pair_code_edit_dist_[test,train,valid].txt` 기반 파일에서 수정해야 하는 코드 stmt에서 line_no 만 남겨서 fl용으로 변환
#   - Input: `data/edit_distance/refined_pair_code_edit_dist_[test,train,valid].txt`
#   - Output: `data/edit_distance/refined_pair_code_edit_dist_fl_[test,train,valid].txt`

# How to use:
# python lyk/fl2-1-convert_dataset.py

import pandas as pd
from tqdm import tqdm
# import utils 


COLUMNS = ['Correct_code', 'Incorrect_code', 'Statement']
# LINE_SPLITTER = '||| '
# array of files
INPUT_FILE = 'data/edit_distance/refined_pair_code_edit_dist_{}.txt'
OUTPUT_FILE = 'data/edit_distance/refined_pair_code_edit_dist_fl_{}.txt'
FILE_TYPE = [
  'test',
  'test_0',
  'test_1',
  'test_2',
  'test_3',
  'test_4',
  'test_5',
  'train',
  'valid'
]

# [problem_id]	[correct_id]	[incorrect_id]	[correct_code]	[incorrect_code]	[statement]
# Ex: 1000	1000	1000	1 #include <bits/stdc++.h>||| 2 using namespace std;||| 3 void run_case() {||| ...	1 #include <bits/stdc++.h>||| 2 using namespace std;||| 3 void run_case() {||| ...	2 #include <bits/stdc++.h>
# def process_one_line(line: str) -> str:
#   # check and remove last \n
#   if line[-1] == '\n':
#     line = line[:-1]

#   last_tab = line.rfind('\t')
#   # if last_tab not found just return
#   if last_tab == -1:
#     return line
#   # split with last_tab
#   line_front = line[:last_tab]
#   line_back = line[last_tab+1:]
#   # split line_back with first whitespace
#   line_back_split = line_back.split(' ', 1)
#   # if line_back_split is not 2, just return
#   if len(line_back_split) != 2:
#     return line

#   return line_front + '\t' + line_back_split[0]

def process_one_file(input_file: str, output_file: str):
  # with tqdm
  data = pd.read_csv(input_file, sep='\t', header=[0])
  # Change statement format ([line_no] [stmt] -> [line_no])
  data['Statement'] = data['Statement'].apply(lambda x: str(x.split(' ', 1)[0]))
  # Save to file
  data.to_csv(output_file, sep='\t', index=False)

def main():
  # wih tqdm
  for file_type in tqdm(FILE_TYPE, desc='Processing files'):
    process_one_file(INPUT_FILE.format(file_type), OUTPUT_FILE.format(file_type))

if __name__ == '__main__':
  main()
