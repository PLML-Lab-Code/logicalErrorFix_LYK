#!/bin/bash

# fl2-2-run-train.sh
# - 기존 `train.sh에서 run.py` 를 통해 학습을 하던 것을 `fl2` 프로젝트용으로 변경해 실행
# - Input: `data/edit_distance/refined_pair_code_edit_dist_fl_[test,train,valid].txt`
# - Output: `model/cpp_refined_fl`

export NUMEXPR_MAX_THREADS="12"

# epoch 3 6 10 14 28
lang=cpp_refined_fl/epoch_14 #programming language
lr=5e-5
batch_size=13
beam_size=100
source_length=512
target_length=64
data_dir=./data/edit_distance
output_dir=model/$lang
train_file=$data_dir/refined_pair_code_edit_dist_train.txt
dev_file=$data_dir/refined_pair_code_edit_dist_valid.txt
eval_steps=1000 #400 for ruby, 600 for javascript, 1000 for others
train_steps=50000 #20000 for ruby, 30000 for javascript, 50000 for others
pretrained_model=microsoft/codebert-base #Roberta: roberta-base
#pretrained_model=neulab/codebert-cpp
python run-lyk1.py --do_train --do_eval --model_type roberta --model_name_or_path $pretrained_model --train_filename $train_file --dev_filename $dev_file --output_dir $output_dir --max_source_length $source_length --max_target_length $target_length --beam_size $beam_size --train_batch_size $batch_size --eval_batch_size $batch_size --learning_rate $lr --train_steps $train_steps --eval_steps $eval_steps 
