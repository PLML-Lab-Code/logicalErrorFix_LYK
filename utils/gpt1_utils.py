import os

_prompt_cache = {}
def gpt1_build_prompt(
  path: str, # 프롬프트 파일 경로
  code: str, # 코드
) -> str:
  if _prompt_cache.get(path) is None:
    if not os.path.exists(path):
      raise Exception('File not found: {}'.format(path))
    with open(path, 'r', encoding='utf-8') as f:
      _prompt_cache[path] = f.read()

  return _prompt_cache[path].format(code)
