import json
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

import json
import os

_cached_prompts = {}
def gpt1_json_prompt_reader(prompt_path: str, code: str):
  """Reads a prompt from a file and returns it as a string.
  If the prompt has already been read, it will be cached and returned from the cache.
  """
  if prompt_path not in _cached_prompts:
    prompt = json.load(open(prompt_path, "r"))
    _cached_prompts[prompt_path] = prompt
  else:
    prompt = _cached_prompts[prompt_path]
  
  # Deep copy prompt
  prompt = json.loads(json.dumps(prompt))
  
  # Check prompt is array
  if not isinstance(prompt, list):
    raise ValueError("Prompt file must contain a JSON array. (type: {})".format(type(prompt)))

  # Check each prompt has a "format" boolean is true and "content" is a string
  for p in prompt:
    if not isinstance(p, dict):
      raise ValueError("Prompt file must contain a JSON array of objects.")
    if "role" not in p or not isinstance(p["role"], str):
      raise ValueError("Prompt file must contain a JSON array of objects with a 'role' string.")
    if "content" not in p or not isinstance(p["content"], str):
      raise ValueError("Prompt file must contain a JSON array of objects with a 'content' string.")
    if p.get("format", False) == True:
      p["content"] = p["content"].format(code=code)
      # remove format key
      del p["format"]
    
  return prompt


# TDD
# unit test: python -m lyk.utils.gpt1_utils
if __name__ == "__main__":
  print('🧪 Unit test of lyk/utils/gpt1_utils.py')
  # Test get_prompt_reader
  print('🧪 Unit test gpt1_json_prompt_reader')
  example_prompts = [
    {
      "role": "assistant",
      "content": "The system is trying to {code}."
    },
    {
      "role": "user",
      "format": True,
      "content": "The user is trying to {code}."
    },
  ]

  with open("test_prompts.json", "w") as f:
    json.dump(example_prompts, f)

  parsed = gpt1_json_prompt_reader("test_prompts.json", "test")
  assert parsed == [
    {
      "role": "assistant",
      "content": "The system is trying to {code}."
    },
    {
      "role": "user",
      "content": "The user is trying to test."
    },
  ]

  os.remove("test_prompts.json")
  print('✅ OK')

