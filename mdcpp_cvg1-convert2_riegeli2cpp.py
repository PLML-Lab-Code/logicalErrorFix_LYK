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

def make_cpp_files(filenames, fileType):
  #data/cppfiles_batch_[correct,incorrect]_[test,train,valid]/[problem_id].txt
  if not os.path.exists(DIR + 'cppfiles_batch' + CODE_TYPE[0] + fileType):
    os.makedirs(DIR + 'cppfiles_batch' + CODE_TYPE[0] + fileType)
  
  if not os.path.exists(DIR + 'cppfiles_batch' + CODE_TYPE[1] + fileType):
    os.makedirs(DIR + 'cppfiles_batch' + CODE_TYPE[1] + fileType)

  if not os.path.exists(DIR + 'descriptions' + fileType):
    os.makedirs(DIR + 'descriptions' + fileType)

  if not os.path.exists(DIR + 'samples' + fileType):
    os.makedirs(DIR + 'samples' + fileType)

  if not os.path.exists(DIR + 'generated_samples' + fileType):
    os.makedirs(DIR + 'generated_samples' + fileType)

  for program_id, problem in enumerate(_all_problems(filenames)):
    # batch export format: \n¶¶¶\n[id]\n¶¶\n[code]\n¶¶¶\n[id]\n¶¶\n[code] ...
    # Correct code batch export
    with open(DIR + 'cppfiles_batch' + CODE_TYPE[0] + fileType + '/' + str(program_id) + '.txt', 'w') as corrFile:
      for correct_id, correct in enumerate(problem.solutions):
        if correct.language==2: # 2: C++
          corrFile.write('\n¶¶¶\n' + str(correct_id) + '\n¶¶\n' + correct.solution)

    # Incorrect code batch export
    with open(DIR + 'cppfiles_batch' + CODE_TYPE[1] + fileType + '/' + str(program_id) + '.txt', 'w') as incorrFile:
      for incorrect_id, incorrect in enumerate(problem.incorrect_solutions):
        if incorrect.language==2: # 2: C++
          incorrFile.write('\n¶¶¶\n' + str(incorrect_id) + '\n¶¶\n' + incorrect.solution)

    with open(DIR + 'descriptions' + fileType + '/' + str(program_id) + '.txt', 'w') as descFile:
      descFile.write(problem.description)

    with open(DIR + 'samples' + fileType + '/' + str(program_id) + '.txt', 'w') as sampleFile:
      sampleFile.write(str(problem.public_tests))

    with open(DIR + 'generated_samples' + fileType + '/' + str(program_id) + '.txt', 'w') as generatedSampleFile:
      generatedSampleFile.write(str(problem.generated_tests))

def main():
  for fileType in FILETYPE:
    print('Creating cppfiles' + fileType + '...')
    filenames = [name for name in sys.argv[1:] if fileType in name]
    make_cpp_files(filenames, fileType)

if __name__ == '__main__':
 main()
