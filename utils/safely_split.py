# safely_split.py

def safely_split(str, delimiter=' ', expected_len=-1):
  '''
  Safely split a string by delimiter
  '''
  splited = str.split(delimiter, expected_len)
  if expected_len > 0 and len(splited) != expected_len:
    # convert to expected_len
    splited = splited + [''] * (expected_len - len(splited))

  return splited
