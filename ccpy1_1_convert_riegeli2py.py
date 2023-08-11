# Original file: 93suhwan/logicalErrorFix/convert_riegeli2cpp.py
# How to use:
# 1. 93suhwan/logicalErrorFix 지시 사항을 따라 bazel과 riegeli를 준비
# 2. 이 스크립트를 logicalErrorFix/code_contests/covert_riegeli2cpp.py 에 덮어쓰기
# 3. 실행: cd logicalErrorFix/code_contests
# 3. 실행: bazel run -c opt :convert_riegeli2cpp /tmp/dm-code_contests/*
import io
import os
import sys

import riegeli
import contest_problem_pb2

DIR='/'.join(os.path.realpath(__file__).split('/')[0:-2]) + '/data/'
FILETYPE=['_train', '_valid', '_test']
CODE_TYPE=['_correct', '_incorrect']

def _all_problems(filenames):
  """Iterates through all ContestProblems in filenames."""
  for filename in filenames:
    reader = riegeli.RecordReader(io.FileIO(filename, mode='rb'),)
    for problem in reader.read_messages(contest_problem_pb2.ContestProblem):
      yield problem

def make_py_files(filenames, fileType):
  #data/cppfiles_batch_[correct,incorrect]_[test,train,valid]/[problem_id].txt
  p_cpp_correct_batch = os.path.join(DIR, 'cppfiles_batch' + CODE_TYPE[0] + fileType)
  p_cpp_incorrect_batch = os.path.join(DIR, 'cppfiles_batch' + CODE_TYPE[1] + fileType)
  p_desc = os.path.join(DIR, 'descriptions' + fileType)
  p_sample = os.path.join(DIR, 'samples' + fileType)
  p_private_sample = os.path.join(DIR, 'private_samples' + fileType)
  p_generated_sample = os.path.join(DIR, 'generated_samples' + fileType)

  if not os.path.exists(p_cpp_correct_batch):
    os.makedirs(p_cpp_correct_batch)
  
  if not os.path.exists(p_cpp_incorrect_batch):
    os.makedirs(p_cpp_incorrect_batch)

  if not os.path.exists(p_desc):
    os.makedirs(p_desc)

  if not os.path.exists(p_sample):
    os.makedirs(p_sample)

  if not os.path.exists(p_private_sample):
    os.makedirs(p_private_sample)

  if not os.path.exists(p_generated_sample):
    os.makedirs(p_generated_sample)

  for program_id, problem in enumerate(_all_problems(filenames)):
    # batch export format: \n¶¶¶\n[id]\n¶¶\n[code]\n¶¶¶\n[id]\n¶¶\n[code] ...
    # Correct code batch export
    is_empty = True
    p_cpp_correct_batch_file = os.path.join(p_cpp_correct_batch, str(program_id) + '.txt')
    with open(p_cpp_correct_batch_file, 'w') as corrFile:
      for correct_id, correct in enumerate(problem.solutions):
        if correct.language==2: # 2: C++
          is_empty = False
          corrFile.write('\n¶¶¶\n' + str(correct_id) + '\n¶¶\n' + correct.solution)
    if is_empty:
      os.remove(p_cpp_correct_batch_file)

    # Incorrect code batch export
    is_empty = True
    p_cpp_incorrect_batch_file = os.path.join(p_cpp_incorrect_batch, str(program_id) + '.txt')
    with open(p_cpp_incorrect_batch_file, 'w') as incorrFile:
      for incorrect_id, incorrect in enumerate(problem.incorrect_solutions):
        if incorrect.language==2: # 2: C++
          is_empty = False
          incorrFile.write('\n¶¶¶\n' + str(incorrect_id) + '\n¶¶\n' + incorrect.solution)
    if is_empty:
      os.remove(p_cpp_incorrect_batch_file)

    # Description export
    p_desc_file = os.path.join(p_desc, str(program_id) + '.txt')
    with open(p_desc_file, 'w') as descFile:
      descFile.write(problem.description)

    # Sample export
    p_sample_file = os.path.join(p_sample, str(program_id) + '.txt')
    with open(p_sample_file, 'w') as sampleFile:
      sampleFile.write(str(problem.public_tests))
  
    # Private sample export
    p_private_sample_file = os.path.join(p_private_sample, str(program_id) + '.txt')
    with open(p_private_sample_file, 'w') as privateSampleFile:
      privateSampleFile.write(str(problem.private_tests))

    # Generated sample export
    p_generated_sample_file = os.path.join(p_generated_sample, str(program_id) + '.txt')
    with open(p_generated_sample_file, 'w') as generatedSampleFile:
      generatedSampleFile.write(str(problem.generated_tests))



def main():
  for fileType in FILETYPE:
    print('Creating pyfiles' + fileType + '...')
    filenames = [name for name in sys.argv[1:] if fileType in name]
    make_py_files(filenames, fileType)

if __name__ == '__main__':
  main()
