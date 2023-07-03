import traceback
from typing import List, Tuple, Callable

import pandas as pd



# "{line_no} {code}||| {line_no} {code}||| ..."
class PDCodeV1:
  def __init__(self, data: List[Tuple[int, str]]):
    self.validate_data(data)
    self.data = data
  
  @staticmethod
  def from_str(code_str: str) -> 'PDCode':
    try:
      # Fail safe
      if isinstance(code_str, PDCodeV1):
        return code_str.clone()

      # Type check
      if not isinstance(code_str, str):
        raise Exception(f'code_str must be str (code_str type: {type(code_str)})')

      data = []
      # Check double quote at the beginning and end then remove them
      if code_str[0] == '"' and code_str[-1] == '"':
        code_str = code_str[1:-1]
      for i, line in enumerate(code_str.split('||| ')):
        if len(line) == 0:
          continue
        ret = line.split(' ', 1)
        if len(ret) != 2:
          raise Exception(f'Line must be "{{line_no}} {{code}}" (idx: {i} / line: {line})')
        line_no, code = ret
        data.append((int(line_no), code.strip()))
      return PDCodeV1(data)
    except Exception as e:
      print('code_str:', code_str)
      traceback.print_exc()
      raise e

  
  @staticmethod
  def validate_data(data: List[Tuple[int, str]]) -> None:
    for i, (line_no, code) in enumerate(data):
      # check line_no, code type
      if not isinstance(line_no, int):
        raise Exception(f'line_no must be int (idx: {i} / line_no: {line_no})')
      if not isinstance(code, str):
        raise Exception(f'code must be str (idx: {i} / line_no: {line_no})')
      # check line_no, i
      if line_no != i + 1:
        raise Exception(f'line_no must be continuous (idx: {i} / line_no: {line_no})')
  
  def __str__(self) -> str:
    return self.to_str()
  
  def __len__(self) -> int:
    return len(self.data)
  
  def __eq__(self, other: 'PDCode') -> bool:
    return self.to_str() == other.to_str()

  def clone(self) -> 'PDCode':
    return PDCodeV1([(line_no, code) for line_no, code in self.data])

  def to_str(self) -> str:
    return '||| '.join([f'{line_no} {code}' for line_no, code in self.data])

  def to_code(self) -> str:
    return '\n'.join([code for _, code in self.data])
  
  def change_line(self, line_no: int, code: str) -> 'PDCode':
    # Check line_no
    if line_no < 1 or line_no > len(self.data):
      raise Exception(f'line_no must be between 1 and {len(self.data)} (line_no: {line_no})')
    self.data[line_no - 1] = (line_no, code)
    return self



# This class is used to store the data of a pair of files.
# pandas csv file: [PID, CID, IID, Correct_code, Incorrect_code, Statement]
class PairDataV1:
  def __init__(self, data: pd.DataFrame):
    self.data = data
  
  @staticmethod
  def from_csv(csv_file: str) -> 'PairDataV1':
    return PairDataV1(pd.read_csv(csv_file, sep='\t'))
  
  def to_csv(self, csv_file: str) -> None:
    self.data.to_csv(csv_file, sep='\t', index=False)

  def validate_data(self) -> None:
    # Check if the columns are correct
    if not {'PID', 'CID', 'IID', 'Correct_code', 'Incorrect_code', 'Statement'}.issubset(self.data.columns):
      raise Exception(f'Columns must be PID, CID, IID, Correct_code, Incorrect_code, Statement (columns: {self.data.columns})')
    # Check if the data is correct
    for i, row in self.data.iterrows():
      if not isinstance(row['PID'], int):
        raise Exception(f'PID must be int (idx: {i} / PID: {row["PID"]})')
      if not isinstance(row['CID'], int):
        raise Exception(f'CID must be int (idx: {i} / CID: {row["CID"]})')
      if not isinstance(row['IID'], int):
        raise Exception(f'IID must be int (idx: {i} / IID: {row["IID"]})')
      if not isinstance(row['Correct_code'], str):
        raise Exception(f'Correct_code must be str (idx: {i} / Correct_code: {row["Correct_code"]})')
      if not isinstance(row['Incorrect_code'], str):
        raise Exception(f'Incorrect_code must be str (idx: {i} / Incorrect_code: {row["Incorrect_code"]})')
      if not isinstance(row['Statement'], str):
        raise Exception(f'Statement must be str (idx: {i} / Statement: {row["Statement"]})')
  
  def find_by_pid_cid_iid(self, pid: int, cid: int, iid: int) -> Tuple[int, Tuple[int, int, int, PDCodeV1, PDCodeV1, str]]:
    for i, row in self.data.iterrows():
      if row['PID'] == pid and row['CID'] == cid and row['IID'] == iid:
        return i, (int(row['PID']), int(row['CID']), int(row['IID']), PDCodeV1.from_str(row['Correct_code']), PDCodeV1.from_str(row['Incorrect_code']), str(row['Statement']))
    return -1, None
  
  def do_for_each(
    self,
    func: Callable[[int, int, int, PDCodeV1, PDCodeV1, str], None]
  ) -> None:
    for i, row in self.data.iterrows():
      func(
        int(row['PID']),
        int(row['CID']),
        int(row['IID']),
        PDCodeV1.from_str(row['Correct_code']),
        PDCodeV1.from_str(row['Incorrect_code']),
        str(row['Statement'])
  )

  def do_map(
    self,
    func: Callable[[int, int, int, PDCodeV1, PDCodeV1, str], Tuple[int, int, int, PDCodeV1, PDCodeV1, str]]
  ) -> 'PairDataV1':
    new_data = []
    for i, row in self.data.iterrows():
      new_row = func(
        int(row['PID']),
        int(row['CID']),
        int(row['IID']),
        PDCodeV1.from_str(row['Correct_code']),
        PDCodeV1.from_str(row['Incorrect_code']),
        str(row['Statement'])
      )
      new_data.append((new_row[0], new_row[1], new_row[2], str(new_row[3]), str(new_row[4]), new_row[5]))
    return PairDataV1(pd.DataFrame(new_data, columns=self.data.columns))



# TDD
# Unit test: python -m lyk.utils.pair_data
if __name__ == '__main__':
  print('🧪 Unit test of lyk/utils/pair_data.py')
  # Test PDCode
  print('🧪 Unit test PDCodeV1')
  pdcode = PDCodeV1.from_str('1 print(1)||| 2 print(2)')
  pdcode.change_line(2, 'print(4)')
  print('1 print(1)||| 2 print(4) ==', pdcode.to_str())
  assert pdcode.to_str() == '1 print(1)||| 2 print(4)'

  # Test PairData
  print('🧪 Unit test PairDataV1')
  data = [
    (
      1, 10, 10,
      '1 print(1)||| 2 print(3)',
      '1 print(2)||| 2 print(3)',
      '1 print(1)'
    ),
    (
      2, 20, 200,
      '1 print(2)||| 2 print(3)',
      '1 print(1)||| 2 print(3)',
      '1 print(2)'
    ),
  ]
  pair_data = PairDataV1(pd.DataFrame(data, columns=['PID', 'CID', 'IID', 'Correct_code', 'Incorrect_code', 'Statement']))
  pair_data.do_map(lambda pid, cid, iid, correct_code, incorrect_code, statement: (
    pid, cid, iid,
    correct_code.change_line(2, 'print(4)'),
    incorrect_code.change_line(2, 'print(5)'),
    statement
  ))
  print('1 print(1)||| 2 print(3) ==', pair_data.data['Correct_code'][0])
  assert pair_data.data['Correct_code'][0] == '1 print(1)||| 2 print(3)'
  print('1 print(2)||| 2 print(3) ==', pair_data.data['Incorrect_code'][0])
  assert pair_data.data['Incorrect_code'][0] == '1 print(2)||| 2 print(3)'
  print('1 print(2)||| 2 print(3) ==', pair_data.data['Correct_code'][1])
  assert pair_data.data['Correct_code'][1] == '1 print(2)||| 2 print(3)'
  print('1 print(1)||| 2 print(3) ==', pair_data.data['Incorrect_code'][1])
  assert pair_data.data['Incorrect_code'][1] == '1 print(1)||| 2 print(3)'
  
  print('✅ All tests passed')
