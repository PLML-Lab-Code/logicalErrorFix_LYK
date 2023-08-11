# Db for ccpy1 - CodeContest Python code raw data
#
#  Table problem
# - primary key: `problem_id`
# - colums: `[INT]problem_id`, `[TEXT]description`

from typing import List, Tuple, Any, Dict, Generator

from . import Sqlite3Db, Sqlite3Table

class Sqlite3TableCcpy1RawProblem(Sqlite3Table):
  
  def __init__(self, sqlite3db: Sqlite3Db):
    super().__init__(sqlite3db, table_name = 'problem')

  def _init_db(self) -> None:
    self._db.conn.execute(f'CREATE TABLE IF NOT EXISTS {self._table_name} (\
      problem_id INT PRIMARY KEY,\
      description TEXT\
    )')
    self._db.conn.commit()

  def tuple_to_dict(self, row) -> Dict[str, Any]:
    return {
      'problem_id': row[0],
      'description': row[1]
    }
  
  def safe_insert_many_tuple(self, rows: List[Tuple[int, str]]) -> None:
    super().safe_insert_many_tuple(rows)

  def cursor_reader_tuple(self, batch_size: int = 1000) -> Generator[Tuple[int, str], None, None]:
    return super().cursor_reader_tuple(batch_size)
  
  def join_cursor_reader_dict(
    self,
    correct_table: Sqlite3TableCcpy1RawCorrect, # Many to one
    incorrect_table: Sqlite3TableCcpy1RawCorrect, # Many to one
    public_test_table: Sqlite3TableCcpy1RawTest, # Many to one
    private_test_table: Sqlite3TableCcpy1RawTest, # Many to one
    generated_test_table: Sqlite3TableCcpy1RawTest, # Many to one
    batch_size: int = 1000
  ) -> Generator[Dict[str, Any], None, None]:
    cursor = self._db.conn.cursor()
    cursor.execute(f'SELECT {self._table_name}.problem_id, \
      {self._table_name}.description, \
      {correct_table._table_name}.correct_id, \
      {incorrect_table._table_name}.incorrect_id, \
      {public_test_table._table_name}.public_test_id, \
      {private_test_table._table_name}.private_test_id, \
      {generated_test_table._table_name}.generated_test_id \
      FROM {self._table_name} \
      LEFT JOIN {correct_table._table_name} \
      ON {self._table_name}.problem_id = {correct_table._table_name}.problem_id \
      LEFT JOIN {incorrect_table._table_name} \
      ON {self._table_name}.problem_id = {incorrect_table._table_name}.problem_id \
      LEFT JOIN {public_test_table._table_name} \
      ON {self._table_name}.problem_id = {public_test_table._table_name}.problem_id \
      LEFT JOIN {private_test_table._table_name} \
      ON {self._table_name}.problem_id = {private_test_table._table_name}.problem_id \
      LEFT JOIN {generated_test_table._table_name} \
      ON {self._table_name}.problem_id = {generated_test_table._table_name}.problem_id \
      ORDER BY {self._table_name}.problem_id')
    while True:
      rows = cursor.fetchmany(batch_size)
      if not rows:
        break
      for row in rows:
        yield {
          'problem_id': row[0],
          'description': row[1],
          'correct_id': row[2],
          'incorrect_id': row[3],
          'public_test_id': row[4],
          'private_test_id': row[5],
          'generated_test_id': row[6]
        }

