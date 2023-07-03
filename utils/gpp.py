import subprocess
from typing import Tuple

def gpp14_compile_code(
  code: str, # 컴파일 할 코드
  exec_file: str, # 컴파일된 파일명. 비워두면 출력을 생성하지 않음
) -> Tuple[int, str, str]: # 에러코드, stdout, stderr

  # 컴파일러 옵션
  compiler_options = []
  if exec_file:
    compiler_options += [
      'g++',
      '-x', 'c++',
      '-std=c++14',
      '-o', exec_file,
      '-'
    ]
  else:
    compiler_options += [
      'g++',
      '-x', 'c++',
      '-std=c++14',
      '-fsyntax-only',
      '-'
    ]
  # g++ 컴파일러를 subprocess를 통해 실행
  compiler = subprocess.Popen(
    compiler_options,
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
  )

  # 코드를 stdin으로 넣어줌, 이 때, 코드는 bytes로 인코딩 해줘야 함
  stdout_data, stderr_data = compiler.communicate(code.encode())

  # 컴파일러의 에러코드, stdout, stderr를 반환
  return compiler.returncode, stdout_data.decode(), stderr_data.decode()



def gpp17_compile_code(
  code: str, # 컴파일 할 코드
  exec_file: str, # 컴파일된 파일명. 비워두면 출력을 생성하지 않음
) -> Tuple[int, str, str]: # 에러코드, stdout, stderr

  # 컴파일러 옵션
  compiler_options = []
  if exec_file:
    compiler_options += [
      'g++',
      '-x', 'c++',
      '-static',
      '-DONLINE_JUDGE',
      '-O2',
      '-std=c++17',
      '-o', exec_file,
      '-'
    ]
  else:
    compiler_options += [
      'g++',
      '-x', 'c++',
      '-static',
      '-DONLINE_JUDGE',
      '-O2',
      '-std=c++17',
      '-fsyntax-only',
      '-'
    ]
  # g++ 컴파일러를 subprocess를 통해 실행
  compiler = subprocess.Popen(
    compiler_options,
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
  )

  # 코드를 stdin으로 넣어줌, 이 때, 코드는 bytes로 인코딩 해줘야 함
  stdout_data, stderr_data = compiler.communicate(code.encode())

  # 컴파일러의 에러코드, stdout, stderr를 반환
  return compiler.returncode, stdout_data.decode(), stderr_data.decode(
)