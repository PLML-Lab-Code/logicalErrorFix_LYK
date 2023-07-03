# Db for gpt1_2 - ChatGPT Code Fix inference parsing response
from typing import List, Dict, Any, Generator, Tuple

from . import Sqlite3Db, Sqlite3Table

# Table for successful parsing response
class Sqlite3TableGpt1_2_stmt(Sqlite3Table):

  def __init__(self, sqlite3db: Sqlite3Db, table_name: str = 'gpt1_2_stmt'):
    if not table_name:
      table_name = 'gpt1_2_stmt'
    super().__init__(sqlite3db, table_name)

  # pid: int - program id
  # cid: int - correct id
  # iid: int - incorrect id
  # line_no: int - line number
  # stmt: str - statement
  def _init_db(self) -> None:
    self._db.conn.execute(f'CREATE TABLE IF NOT EXISTS {self._table_name} (\
      pid INT,\
      cid INT,\
      iid INT,\
      line_no INT,\
      stmt TEXT,\
      PRIMARY KEY (pid, cid, iid, line_no)\
    )')

    # index for pid,cid,iid
    self._db.conn.execute('CREATE INDEX IF NOT EXISTS {}_pid_cid_iid ON {} (pid, cid, iid)'.format(self._table_name, self._table_name))
    self._db.conn.commit()
  
  def tuple_to_dict(self, row) -> Dict[str, Any]:
    return {
      'pid': row[0],
      'cid': row[1],
      'iid': row[2],
      'line_no': row[3],
      'stmt': row[4]
    }
  
  def ensure_keys(self, keys) -> bool:
    return super().ensure_keys(keys)
  
  def count(self) -> int:
    return super().count()

  def safe_insert_many_tuple(self, rows: List[Tuple[int, int, int, int, str]]) -> None:
    super().safe_insert_many_tuple(rows)

  def safe_insert_many_dict(self, rows: List[Dict[str, Any]]) -> None:
    super().safe_insert_many_dict(rows)
  
  def cursor_reader_tuple(self, batch_size: int = 1000) -> Generator[Tuple[int, int, int, int, str], None, None]:
    return super().cursor_reader_tuple(batch_size)
  
  def cursor_reader_dict(self, batch_size: int = 1000) -> Generator[Dict[str, Any], None, None]:
    return super().cursor_reader_dict(batch_size)
  
  def query_many_pid_cid_iid(self, pid: int, cid: int, iid: int) -> List[Tuple[int, int, int, int, str]]:
    cursor = self._db.conn.cursor()
    cursor.execute('SELECT * FROM {} WHERE pid=? AND cid=? AND iid=?'.format(self._table_name), (pid, cid, iid))
    return cursor.fetchall()

# Table for failed parsing response
class Sqlite3TableGpt1_2_failed(Sqlite3Table):
  
  def __init__(self, sqlite3db: Sqlite3Db, table_name: str = 'gpt1_2_failed'):
    if not table_name:
      table_name = 'gpt1_2_failed'
    super().__init__(sqlite3db, table_name)

  # pid: int - program id
  # cid: int - correct id
  # iid: int - incorrect id
  # response: str - response
  def _init_db(self) -> None:
    self._db.conn.execute(f'CREATE TABLE IF NOT EXISTS {self._table_name} (\
      pid INT,\
      cid INT,\
      iid INT,\
      response TEXT,\
      PRIMARY KEY (pid, cid, iid)\
    )')

    # index for pid,cid,iid
    self._db.conn.execute('CREATE INDEX IF NOT EXISTS {}_pid_cid_iid ON {} (pid, cid, iid)'.format(self._table_name, self._table_name))
    self._db.conn.commit()
  
  def tuple_to_dict(self, row) -> Dict[str, Any]:
    return {
      'pid': row[0],
      'cid': row[1],
      'iid': row[2],
      'response': row[3]
    }
  
  def ensure_keys(self, keys) -> bool:
    return super().ensure_keys(keys)
  
  def count(self) -> int:
    return super().count()

  def safe_insert_many_tuple(self, rows: List[Tuple[int, int, int, str]]) -> None:
    super().safe_insert_many_tuple(rows)

  def safe_insert_many_dict(self, rows: List[Dict[str, Any]]) -> None:
    super().safe_insert_many_dict(rows)
  
  def cursor_reader_tuple(self, batch_size: int = 1000) -> Generator[Tuple[int, int, int, str], None, None]:
    return super().cursor_reader_tuple(batch_size)
  
  def cursor_reader_dict(self, batch_size: int = 1000) -> Generator[Dict[str, Any], None, None]:
    return super().cursor_reader_dict(batch_size)
  
  def query_many_pid_cid_iid(self, pid: int, cid: int, iid: int) -> List[Tuple[int, int, int, str]]:
    cursor = self._db.conn.cursor()
    cursor.execute('SELECT * FROM {} WHERE pid=? AND cid=? AND iid=?'.format(self._table_name), (pid, cid, iid))
