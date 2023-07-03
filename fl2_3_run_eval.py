# TODO: Need Fix: bleu score 계산 부분에서 지속적 에러로그 발생 -> 작동은 하나 수정 필요

# #!/bin/bash

# lang=cpp_refined/epoch_28 #programming language
# batch_size=128
# beam_size=100
# source_length=512
# target_length=64
# data_dir=./data/edit_distance
# output_dir=model/$lang
# dev_file=$data_dir/refined_pair_code_edit_dist_valid.txt

# #test_file=$data_dir/pair_code_edit_dist_train.txt
# #test_file=$data_dir/pair_code_edit_dist_valid.txt
# #test_file=$data_dir/pair_code_edit_dist_test.txt

# #test_model=$output_dir/checkpoint-best-bleu/pytorch_model.bin
# #test_model=$output_dir/checkpoint-best-ppl/pytorch_model.bin
# #test_model=$output_dir/checkpoint-last/pytorch_model.bin

# pretrained_model=microsoft/codebert-base #Roberta: roberta-base

# help() {
#   echo "help"
#   exit 0
# }

# while getopts "d:h" opt
# do
#   case $opt in
#     f) test_file=$OPTARG;;
#     m) test_model=$OPTARG;;
#     h) help;;
#     ?) help;;
#   esac
# done

# test_file=("valid")
# test_model=("best-bleu" "last")
# for (( i=0; i<${#test_file[@]}; i++ ))
# do
#   for (( k=0; k<${#test_model[@]}; k++ ))
#   do
#     python changsup_run_v1.py --do_test --model_type roberta --model_name_or_path $pretrained_model --load_model_path $output_dir/checkpoint-${test_model[$k]}/pytorch_model.bin  --dev_filename $dev_file --test_filename ./data/edit_distance/refined_pair_code_edit_dist_${test_file[$i]}.txt --output_dir $output_dir/checkpoint-${test_model[$k]} --max_source_length $source_length --max_target_length $target_length --beam_size $beam_size --eval_batch_size $batch_size
#   done
# done

# 위 코드의 python 버전

# fl2-3-run-eval.sh
# - 기존 `eval.sh에서 run.py` 를 통해 평가를 하던 것을 `fl2` 프로젝트용으로 변경해 실행
# - Input: `data/edit_distance/refined_pair_code_edit_dist_fl_[test,train,valid].txt`
# - Output: `model/cpp_refined_fl`

# How to use:
# python lyk/fl2-3-run-eval.py

from tqdm import tqdm
import subprocess
import sys
import utils

# epoch 3 6 10 14 28
lang = 'cpp_refined_fl/epoch_{}'
epochs = [3, 6, 10, 14, 28]
lr = 5e-5
# batch_size = 128 # utils.get_epoch(train_steps, train_examples, wanted_epoch)
beam_size = 10
source_length = 512
target_length = 64
data_dir = './data/edit_distance'
output_dir = f'model/{lang}'
dev_file = data_dir + '/refined_pair_code_edit_dist_fl_valid.txt'
test_file = data_dir + '/refined_pair_code_edit_dist_fl_test.txt'
eval_steps = 1000 #400 for ruby, 600 for javascript, 1000 for others
#train_steps = 50000 #20000 for ruby, 30000 for javascript, 50000 for others
pretrained_model = 'microsoft/codebert-base' #Roberta: roberta-base
#pretrained_model=neulab/codebert-cpp
test_files = ['valid', 'test']
test_models = ['best-bleu', 'last']

def main():
  # read train_file to get train_examples (-1 for header)
  train_examples = 0
  with open(dev_file, 'r') as f:
    train_examples = len(f.readlines()) - 1
  print(f'📚 train_examples: {train_examples}')

  # tqdm for epochs
  for epoch in tqdm(epochs, desc='⏳ Epochs'):
    try:
      # get train_steps (No need to get batch_size)
      # train_steps = utils.get_train_steps(train_examples, epoch)
      # batch_size = utils.get_batch_size(train_steps)

      # 🔒 Fixed batch_size on eval
      batch_size = 128

      # output dir
      output_dir_epoch = output_dir.format(epoch)

      # run eval for each test file with tqdm
      for test_file in tqdm(test_files, desc='⏳ Test files', leave=False):
        # run eval for each test model with tqdm
        for test_model in tqdm(test_models, desc='⏳ Test models', leave=False):
          
          subprocess.run([
            'python', 'changsup_run_v1.py',
            '--do_test',
            '--model_type', 'roberta',
            '--model_name_or_path', pretrained_model,
            '--load_model_path', output_dir_epoch + f'/checkpoint-{test_model}/pytorch_model.bin',
            '--dev_filename', dev_file,
            '--test_filename', data_dir + f'/refined_pair_code_edit_dist_fl_{test_file}.txt',
            '--output_dir', output_dir_epoch + f'/checkpoint-{test_model}',
            '--max_source_length', str(source_length),
            '--max_target_length', str(target_length),
            '--beam_size', str(beam_size),
            '--eval_batch_size', str(batch_size),
          ])
    except Exception as e:
      print(f'💥 Unexpected error occurred on epoch {epoch}')
      print(sys.exc_info()[0])
      print(e)
      continue
    
  print(f'✅ Done')
    
if __name__ == '__main__':
  main()
