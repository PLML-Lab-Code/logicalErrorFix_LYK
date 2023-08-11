# Db for prompt_db - for GPT inference text input
from typing import List, Dict, Any, Generator, Tuple

from . import Sqlite3Db, Sqlite3Table

# Extend Sqlite3Table
class Sqlite3TablePromptDb(Sqlite3Table):
  
    def __init__(self, sqlite3db: Sqlite3Db, table_name: str = 'prompt_db'):
      if not table_name:
        table_name = 'prompt_db'
      super().__init__(sqlite3db, table_name)
  
    def _init_db(self) -> None:
      self._db.conn.execute('CREATE TABLE IF NOT EXISTS {} (\
        pid INT,\
        cid INT,\
        iid INT,\
        prompt TEXT,\
        PRIMARY KEY (pid, cid, iid)\
      )'.format(self._table_name))
  
      self._db.conn.commit()
    
    def tuple_to_dict(self, row) -> Dict[str, Any]:
      return {
        'pid': row[0],
        'cid': row[1],
        'iid': row[2],
        'prompt': row[3]
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
      return cursor.fetchall()
