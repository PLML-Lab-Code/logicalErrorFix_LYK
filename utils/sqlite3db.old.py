import re
import sqlite3
import tqdm
import os
import time
import random
from typing import List, Dict, Any, Generator, Tuple

class Sqlite3Db:
  def __init__(self, db_file: str):
    self.conn = sqlite3.connect(db_file)
    self.cur = self.conn.cursor()

  def __del__(self):
    self.conn.close()

  @staticmethod
  def ensure_safe_key_string(key: str) -> str:
    return re.sub(r'[^a-zA-Z0-9_]', '_', key)

  def table_list(self) -> List[str]:
    self.cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    # remove default table like sqlite_sequence, ...
    return [row[0] for row in self.cur.fetchall() if not row[0].startswith('sqlite')]

  # abstract
  def safe_insert_many_tuple(self, rows: List[Tuple[Any, ...]]) -> None:
    raise NotImplementedError

  # insert_many with parameterized query, transaction, and retry when database is locked
  def atomic_safe_insert_many_tuple(self, table_name: str, rows: List[Tuple[Any, ...]]) -> None:
    # Ensure safe key string
    table_name = Sqlite3Db.ensure_safe_key_string(table_name)

    # Insert parameterized query
    retry_count = 0
    self.conn.execute('BEGIN TRANSACTION')
    while True:
      try:
        self.conn.executemany('INSERT INTO {} VALUES ({})'.format(
          table_name,
          ','.join(['?'] * len(rows[0]))
        ), rows)
        self.conn.commit()
        break
      except sqlite3.OperationalError as e:
        if 'database is locked' in str(e):
          retry_count += 1
          print('🔒 Database is locked, retrying... ({} times)'.format(retry_count))
          # sleep random time between 0.1 and 0.5 seconds
          time.sleep(0.1 + 0.4 * random.random())
          continue
        else:
          # Rollback and raise exception
          self.conn.rollback()
          raise e

  # abstract
  def safe_insert_many_dict(self, rows: List[Dict[str, Any]]) -> None:
    raise NotImplementedError

  # insert_many with parameterized query, transaction, and retry when database is locked
  def atomic_safe_insert_many_dict(self, table_name: str, rows: List[Dict[str, Any]]) -> None:
    # Ensure safe key string
    rows = [{Sqlite3Db.ensure_safe_key_string(k): v for k, v in row.items()} for row in rows]
    # Ensure all keys are in the table
    self.cur.execute('SELECT * FROM {} LIMIT 0'.format(table_name))
    table_columns = [description[0] for description in self.cur.description]
    for row in rows:
      for key in row.keys():
        if key not in table_columns:
          raise Exception('Key {} not in table {}'.format(key, table_name))
    # Insert parameterized query
    retry_count = 0
    self.conn.execute('BEGIN TRANSACTION')
    while True:
      try:
        self.cur.executemany('''
          INSERT INTO {} ({})
          VALUES ({})
        '''.format(
          table_name,
          ','.join(rows[0].keys()),
          ','.join(['?'] * len(rows[0].keys()))
        ), [list(row.values()) for row in rows])
        self.conn.commit()
        break
      except sqlite3.OperationalError as e:
        if 'database is locked' in str(e):
          retry_count += 1
          print('🔒 Database is locked, retrying... ({} times)'.format(retry_count))
          # sleep random time between 0.1 and 0.5 seconds
          time.sleep(0.1 + 0.4 * random.random())
          continue
        else:
          # Rollback and raise exception
          self.conn.rollback()
          raise e

  # abstract
  def cursor_reader(self, batch_size: int = 1000) -> Generator[List[Tuple[Any, ...]], None, None]:
    raise NotImplementedError

  # Cursor reader (generator)
  def atomic_cursor_reader(self, table_name: str, batch_size: int = 1000) -> Generator[List[Tuple[Any, ...]], None, None]:
    # Ensure safe key string
    table_name = Sqlite3Db.ensure_safe_key_string(table_name)
    # New cursor for each reader
    cur = self.conn.cursor()
    cur.execute('SELECT * FROM {}'.format(table_name))
    while True:
      rows = cur.fetchmany(batch_size)
      if len(rows) == 0:
        break
      yield rows
    # Close cursor
    cur.close()



# Sqlite3DbPairCode extends Sqlite3Db
class Sqlite3DbPairCode(Sqlite3Db):
  def __init__(self, db_file: str, table_name: str):
    super().__init__(db_file)
    self._table_name = Sqlite3Db.ensure_safe_key_string(table_name)
    self.cur.execute('''
      CREATE TABLE IF NOT EXISTS {} (
        program_id INTEGER NOT NULL,
        correct_id INTEGER NOT NULL,
        incorrect_id INTEGER NOT NULL,
        correct_code TEXT NOT NULL,
        incorrect_code TEXT NOT NULL,
        stmt TEXT NOT NULL,
        PRIMARY KEY (program_id, correct_id, incorrect_id)
      )
    '''.format(self._table_name))
    # Index for program_id, correct_id, incorrect_id
    self.cur.execute('''
      CREATE INDEX IF NOT EXISTS {}_program_id_correct_id_incorrect_id
      ON {} (program_id, correct_id, incorrect_id)
    '''.format(self._table_name, self._table_name))
  
  # Override safe_insert_many_tuple
  def safe_insert_many_tuple(self, rows: List[Tuple[int,int,int,str,str,str]]) -> None:
    super().atomic_safe_insert_many_tuple(self._table_name, rows)

  # Override safe_insert_many_dict
  def safe_insert_many_dict(self, rows: List[Dict[str, Any]]) -> None:
    super().atomic_safe_insert_many_dict(self._table_name, rows)

  # Override cursor_reader (generator)
  def cursor_reader(self, batch_size: int = 1000) -> Generator[List[Tuple[int,int,int,str,str,str]], None, None]:
    return super().atomic_cursor_reader(self._table_name, batch_size)
  
  @staticmethod
  def tuple_to_dict(row: Tuple[int,int,int,str,str,str]) -> Dict[str, Any]:
    return {
      'program_id': row[0],
      'correct_id': row[1],
      'incorrect_id': row[2],
      'correct_code': row[3],
      'incorrect_code': row[4],
      'stmt': row[5],
    }



class Sqlite3DbUtils:
  @staticmethod
  def merge_db(db_merged: Sqlite3Db, db_list: List[Sqlite3Db]):
    # tqdm for db_list
    for db in tqdm.tqdm(db_list, desc='⏳ Merge db_list'):
      # tqdm for table_list
      for table_name in tqdm.tqdm(db.table_list(), desc='⏳ Merge table_list', leave=False):
        # Check if table exists
        if table_name not in db_merged.table_list():
          # Get table information
          db.cur.execute('SELECT sql FROM sqlite_master WHERE type="table" AND name="{}"'.format(table_name))
          table_info = db.cur.fetchone()[0]
          # Create table
          db_merged.cur.execute(table_info)
          db_merged.conn.commit()
        # tqdm for cursor_reader
        for rows in tqdm.tqdm(db.atomic_cursor_reader(table_name), desc='⏳ Merge cursor_reader', leave=False):
          db_merged.atomic_safe_insert_many_tuple(table_name, rows)



# TDD
# Unit test: python -m lyk.utils.sqlite3db
if __name__ == '__main__':

  # Clean up func
  def clean_up():
    if os.path.exists('tmp1.db'):
      os.remove('tmp1.db')
    if os.path.exists('tmp2.db'):
      os.remove('tmp2.db')
    if os.path.exists('tmp3-1.db'):
      os.remove('tmp3-1.db')
    if os.path.exists('tmp3-2.db'):
      os.remove('tmp3-2.db')
    if os.path.exists('tmp3-merged.db'):
      os.remove('tmp3-merged.db')


  # Ensure initial clean up
  clean_up()

  try:
    # Test1: Sqlite3Db
    print('🧪 Unit test: Sqlite3Db')
    db = Sqlite3Db('tmp1.db')

    result = db.table_list()
    print('sqlite3db.table_list() == []', result)
    assert result == []

    db.cur.execute('''
      CREATE TABLE IF NOT EXISTS test (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL
      )
    ''')
    db.cur.execute('''
      INSERT INTO test (id, name)
      VALUES (1, 'test1')
    ''')
    db.cur.execute('''
      INSERT INTO test (id, name)
      VALUES (2, 'test2')
    ''')
    db.conn.commit()

    result = db.table_list()
    print("sqlite3db.table_list() == ['test']", result)
    assert result == ['test']

    result_generator = db.atomic_cursor_reader('test')
    result = next(result_generator)
    print("sqlite3db.cursor_reader('test') == [(1, 'test1'), (2, 'test2')]", result)
    assert result == [(1, 'test1'), (2, 'test2')]

    result_generator = db.atomic_cursor_reader('test', batch_size=1)
    result = next(result_generator)
    print("sqlite3db.cursor_reader('test', batch_size=1) == [(1, 'test1')]", result)
    assert result == [(1, 'test1')]
    result = next(result_generator)
    print("sqlite3db.cursor_reader('test', batch_size=1) == [(2, 'test2')]", result)
    assert result == [(2, 'test2')]



    # Test2: Sqlite3DbPairCode
    print('🧪 Unit test: Sqlite3DbPairCode')
    db = Sqlite3DbPairCode('tmp2.db', 'test')

    result = db.table_list()
    print('sqlite3db.table_list() == [\'test\']', result)
    assert result == ['test']

    db.safe_insert_many_dict(
      [
        {
          'program_id': 1,
          'correct_id': 10,
          'incorrect_id': 100,
          'correct_code': '1 test',
          'incorrect_code': '1 test2',
          'stmt': '1 test3',
        },
        {
          'program_id': 2,
          'correct_id': 20,
          'incorrect_id': 200,
          'correct_code': '2 test',
          'incorrect_code': '2 test2',
          'stmt': '2 test3',
        }
      ]
    )

    result_generator = db.cursor_reader()
    result = next(result_generator)
    print("sqlite3db.cursor_reader() == [(1, 10, 100, '1 test', '1 test2', '1 test3'), \
      (2, 20, 200, '2 test', '2 test2', '2 test3')]", result)
    assert result == [
      (1, 10, 100, '1 test', '1 test2', '1 test3'),
      (2, 20, 200, '2 test', '2 test2', '2 test3')
    ]

    result_generator = db.cursor_reader(batch_size=1)
    result = next(result_generator)
    print("sqlite3db.cursor_reader(batch_size=1) == [(1, 10, 100, '1 test', '1 test2', '1 test3')]", result)
    assert result == [(1, 10, 100, '1 test', '1 test2', '1 test3')]
    result = next(result_generator)
    print("sqlite3db.cursor_reader(batch_size=1) == [(2, 20, 200, '2 test', '2 test2', '2 test3')]", result)
    assert result == [(2, 20, 200, '2 test', '2 test2', '2 test3')]
    try:
      result = next(result_generator)
    except StopIteration:
      result = []
    print("sqlite3db.cursor_reader(batch_size=1) == []", result)
    assert result == []



    # Test2: Sqlite3DbUtils
    print('🧪 Unit test: Sqlite3DbUtils')
    db1 = Sqlite3DbPairCode('tmp3-1.db', 'test1')
    db2_1 = Sqlite3DbPairCode('tmp3-2.db', 'test1')
    db2_2 = Sqlite3DbPairCode('tmp3-2.db', 'test2')
    db_merged = Sqlite3Db('tmp3-merged.db')

    db1.safe_insert_many_dict(
      [
        {
          'program_id': 1,
          'correct_id': 10,
          'incorrect_id': 100,
          'correct_code': '1 test',
          'incorrect_code': '1 test2',
          'stmt': '1 test3',
        }
      ]
    )
    db2_1.safe_insert_many_dict(
      [
        {
          'program_id': 2,
          'correct_id': 20,
          'incorrect_id': 200,
          'correct_code': '2 test',
          'incorrect_code': '2 test2',
          'stmt': '2 test3',
        }
      ]
    )
    db2_2.safe_insert_many_dict(
      [
        {
          'program_id': 3,
          'correct_id': 30,
          'incorrect_id': 300,
          'correct_code': '3 test',
          'incorrect_code': '3 test2',
          'stmt': '3 test3',
        }
      ]
    )
    Sqlite3DbUtils.merge_db(db_merged, [db1, db2_1]) # db2_2 is basically same as db2_1

    result_generator = db_merged.atomic_cursor_reader('test1')
    result = next(result_generator)
    print("sqlite3db.cursor_reader('test1') == [(1, 10, 100, '1 test', '1 test2', '1 test3'), \
      (2, 20, 200, '2 test', '2 test2', '2 test3')]", result)
    assert result == [
      (1, 10, 100, '1 test', '1 test2', '1 test3'),
      (2, 20, 200, '2 test', '2 test2', '2 test3')
    ]

    result_generator = db_merged.atomic_cursor_reader('test2')
    result = next(result_generator)
    print("sqlite3db.cursor_reader('test2') == [(3, 30, 300, '3 test', '3 test2', '3 test3')]", result)
    assert result == [(3, 30, 300, '3 test', '3 test2', '3 test3')]



    # Clean up
    clean_up()
    print('✅ All tests passed')
  except Exception as e:
    print('❌ Test failed')
    # Clean up
    clean_up()
    raise e
