# #!/bin/bash

# export NUMEXPR_MAX_THREADS="12"

# # epoch 3 6 10 14 28
# lang=cpp_refined_fl/epoch_14 #programming language
# lr=5e-5
# batch_size=13
# beam_size=100
# source_length=512
# target_length=64
# data_dir=./data/edit_distance
# output_dir=model/$lang
# train_file=$data_dir/refined_pair_code_edit_dist_train.txt
# dev_file=$data_dir/refined_pair_code_edit_dist_valid.txt
# eval_steps=1000 #400 for ruby, 600 for javascript, 1000 for others
# train_steps=50000 #20000 for ruby, 30000 for javascript, 50000 for others
# pretrained_model=microsoft/codebert-base #Roberta: roberta-base
# #pretrained_model=neulab/codebert-cpp
# python run-lyk1.py --do_train --do_eval --model_type roberta --model_name_or_path $pretrained_model --train_filename $train_file --dev_filename $dev_file --output_dir $output_dir --max_source_length $source_length --max_target_length $target_length --beam_size $beam_size --train_batch_size $batch_size --eval_batch_size $batch_size --learning_rate $lr --train_steps $train_steps --eval_steps $eval_steps 

# 위 코드의 python 버전

# fl2-2-run-train.sh
# - 기존 `train.sh에서 run.py` 를 통해 학습을 하던 것을 `fl2` 프로젝트용으로 변경해 실행
# - Input: `data/edit_distance/refined_pair_code_edit_dist_fl_[test,train,valid].txt`
# - Output: `model/cpp_refined_fl`

# How to use:
# python lyk/fl2-2-run-train.py

from tqdm import tqdm
import subprocess
import sys
import utils

# epoch 3 6 10 14 28
lang = 'cpp_refined_fl2/epoch_{}'
epochs = [3, 6, 10, 14, 28]
lr = 5e-5
# batch_size = 13 # utils.get_epoch(train_steps, train_examples, wanted_epoch)
beam_size = 10
source_length = 512
target_length = 64
data_dir = './data/edit_distance'
output_dir = f'model/{lang}'
train_file = data_dir + '/refined_pair_code_edit_dist_fl_train.txt'
dev_file = data_dir + '/refined_pair_code_edit_dist_fl_valid.txt'
eval_steps = 1000 #400 for ruby, 600 for javascript, 1000 for others
train_steps = 50000 #20000 for ruby, 30000 for javascript, 50000 for others
pretrained_model = 'microsoft/codebert-base' #Roberta: roberta-base
#pretrained_model=neulab/codebert-cpp

def main():
  # read train_file to get train_examples (-1 for header)
  train_examples = 0
  with open(train_file, 'r') as f:
    train_examples = len(f.readlines()) - 1
  print(f'📚 train_examples: {train_examples}')

  # tqdm for epochs
  for epoch in tqdm(epochs, desc='⏳ Epochs'):
    try:
      # output dir
      output_dir_epoch = output_dir.format(epoch)

      # Get batch size
      batch_size = utils.get_epoch(train_steps=train_steps, train_examples=train_examples, wanted_epoch=epoch)
      tqdm.write(f'🔥 Epoch {epoch} / Batch size {batch_size}')

      # Start new python process
      process = subprocess.Popen([
        'python', 'changsup_run_v1.py',
        '--do_train', '--do_eval',
        '--model_type', 'roberta',
        '--model_name_or_path', pretrained_model,
        '--train_filename', train_file,
        '--dev_filename', dev_file,
        '--output_dir', output_dir_epoch,
        '--max_source_length', str(source_length),
        '--max_target_length', str(target_length),
        '--beam_size', str(beam_size),
        '--train_batch_size', str(batch_size),
        '--eval_batch_size', str(batch_size),
        '--learning_rate', str(lr),
        '--train_steps', str(train_steps),
        '--eval_steps', str(eval_steps)
      ], stdout=sys.stdout, stderr=sys.stderr)

      # Wait for process to finish
      process.wait()

      # If process is not successful, raise exception
      if process.returncode != 0:
        raise Exception(f'❌ Process failed on epoch {epoch}')

    except Exception as e:
      print(f'💥 Unexpected error occurred on epoch {epoch}')
      print(sys.exc_info()[0])
      print(e)
      continue

  print(f'✅ Done')

if __name__ == '__main__':
  main()
