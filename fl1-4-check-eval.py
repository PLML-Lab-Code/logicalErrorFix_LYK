# Use1: python lyk/fl1-4-check-eval.py
# Use2: python lyk/fl1-4-check-eval.py --model_dir model/cpp_refined --epochs epoch_10 epoch_14 --details checkpoint-best-bleu checkpoint-last --datasets test --top 10 --beam_size 10

import argparse
import logging
import os
import matplotlib.pyplot as plt
import numpy as np
import utils

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

def main():
  parser = argparse.ArgumentParser()
  parser.add_argument('--model_dir', type=str, default='model/cpp_refined_fl',
    help='모델 경로')
  parser.add_argument('--epochs', type=str, nargs='+', default=['epoch_3', 'epoch_6', 'epoch_10', 'epoch_14', 'epoch_28'],
    help='평가할 모델 epoch 폴더 이름들(ex. "--epochs epoch_3 epoch_6 ...")')
  parser.add_argument('--details', type=str, nargs='+', default=['checkpoint-best-bleu', 'checkpoint-last'],
    help='평가할 epoch의 세부 평가 지표')
  parser.add_argument('--datasets', type=str, nargs='+', default=['fl1-test', 'fl1-valid'],
    help='평가할 데이터셋 이름들(ex. "--datasets test_0 valid_0 ...")')
  parser.add_argument('--beam_size', type=int, default=10,
    help='몇 개의 예측을 평가 할 것인지(예측에 사용한 eval 스크립트와 값이 일치해야함)')
  parser.add_argument('--top', type=int, nargs='+', default=[1, 2, 4, 8, 10],
    help='beam_size 중 몇 번째 예측까지 비교할 것인지')
  args = parser.parse_args()
  logger.info(args)

  model_dir = args.model_dir
  epochs = args.epochs
  details = args.details
  datasets = args.datasets
  beam_size = args.beam_size
  top = args.top
  # 최빈값 사용 여부
  use_most = False
  

  # result dictionary
  result = {}

  # * 정확도 평가
  for epoch in epochs:
    if result.get(epoch) is None:
      result[epoch] = {}

    for detail in details:
      if result[epoch].get(detail) is None:
        result[epoch][detail] = {}

      for dataset in datasets:
        if result[epoch][detail].get(dataset) is None:
          result[epoch][detail][dataset] = {}

        for t in top:
          logger.info('epoch: %s, detail: %s, dataset: %s, top: %d' % (epoch, detail, dataset, t))
        
          dir = os.path.join(model_dir, epoch, detail, dataset)
          accr = eval_localization_precision2(dir, t, beam_size, use_most=use_most)
          # 정확도 출력
          logger.info('accr: %f' % (accr))
          # result map에 저장
          result[epoch][detail][dataset][t] = accr
  
  # mathplotlib을 이용한 colormap 그래프 출력
  # row: [detail]/[dataset]-top[n], col: epoch, value: accr
  fig, ax = plt.subplots()
  rows = []
  for detail in details:
    for dataset in datasets:
      for t in top:
        rows.append('%s/%s-top%d' % (detail, dataset, t))
  cols = epochs

  # * table colormap 그래프 출력 (출력은 소숫점 2자리까지)
  # https://matplotlib.org/stable/gallery/color/colormap_reference.html
  # 값들에 대한 노말라이즈
  all_values = list(extract_values(result))
  normal = plt.Normalize(np.min(all_values), np.max(all_values))

  # 커스텀 컬러맵 ((1, 1, 1) ~ (0.5, 0.5, 1))
  # https://matplotlib.org/stable/tutorials/colors/colormap-manipulation.html
  colors = [(1, 1, 1), (0, 0, 1)]
  cmap = plt.cm.colors.LinearSegmentedColormap.from_list('custom', colors, N=256)

  # 테이블 색상
  fig.patch.set_visible(False)
  ax.axis('off')
  ax.axis('tight')
  table = ax.table(
    cellText=[[round(result[epoch][detail][dataset][t], 2) for epoch in epochs] for detail in details for dataset in datasets for t in top],
    rowLabels=rows,
    colLabels=cols,
    loc='center',
    # plt.cm.RdYlGn
    cellColours=plt.cm.RdYlGn(normal([[result[epoch][detail][dataset][t] for epoch in epochs] for detail in details for dataset in datasets for t in top])),
  )
  fig.tight_layout()
  #plt.show()
  plt.draw()
  plt.savefig(f'lyk/output/fl1-4-table-{utils.safe_key_string(model_dir)}.png', dpi=200)

# * dictionary의 모든 value를 list로 변환
def extract_values(nested_dict):
  for value in nested_dict.values():
      if isinstance(value, dict):
          yield from extract_values(value)
      else:
          yield value


# * 라인 넘버 예측 정확도 평가 1 - 하나라도 정답과 예측이 같은 비율
# dir: 정답, 예측 파일이 있는 폴더와 확장자를 제외한 데이터셋 이름까지 (string)
# top: beam_size중 몇 번째까지 비교할 것인지 (number)
# beam_size: 몇개의 예측까지 평가할 것인지 (number)
#
# return: 라인 넘버 예측 정확도 (number 0~1)
def eval_localization_precision(dir, top, beam_size):
  # * top이 beam_size보다 크면 에러
  if (top > beam_size):
    logger.error('top is bigger than beam_size - top: %d, beam_size: %d' % (top, beam_size))
    return 0.0

  # * 정답과 예측이 같은 비율
  ret = 0.0

  # * 정답, 예측 파일 이름
  f_gold = dir + '.gold'
  f_output = dir + '.output'

  with open(f_gold, 'r') as f_gold, open(f_output, 'r') as f_output:
    gold_lines = f_gold.readlines()
    output_lines = f_output.readlines()

    # ! 예측한 라인 번호가 정답과 같은 경우
    localization = 0
    # gold 파일 라인 수 만큼 반복
    for i, gold_line in enumerate(gold_lines):
      # 틀린 코드 라인 번호 정답
      gold_line_no = gold_line.split('\t', 1)[1].split(' ', 1)[0]

      # 틀린 코드 라인 번호 예측
      for j in range(beam_size):
        if (j >= top):
          break
        o_idx = beam_size * i + j
        output_line = output_lines[o_idx]
        output_line_no = output_line.split('\t', 1)[1].split(' ', 1)[0]

        # 정답과 예측이 같으면 localization + 1
        if (gold_line_no == output_line_no):
          localization += 1
          break

    # 정답과 예측이 같은 비율
    ret = localization / len(gold_lines)
  return ret

# * 라인 넘버 예측 정확도 평가 2 - 가장 자주 나온 라인 번호
# dir: 정답, 예측 파일이 있는 폴더와 확장자를 제외한 데이터셋 이름까지 (string)
# top: beam_size중 몇 번째까지 비교할 것인지 (number)
# beam_size: 몇개의 예측까지 평가할 것인지 (number)
#
# return: 라인 넘버 예측 정확도 (number 0~1)
def eval_localization_precision2(dir, top, beam_size, use_most=False):
  # * top이 beam_size보다 크면 에러
  if (top > beam_size):
    logger.error('top is bigger than beam_size - top: %d, beam_size: %d' % (top, beam_size))
    return 0.0

  # * 정답과 예측이 같은 비율
  ret = 0.0

  # * 정답, 예측 파일 이름
  f_gold = dir + '.gold'
  f_output = dir + '.output'

  with open(f_gold, 'r') as f_gold, open(f_output, 'r') as f_output:
    gold_lines = f_gold.readlines()
    output_lines = f_output.readlines()

    # ! 예측한 라인 번호가 정답과 같은 경우
    localization = 0
    # gold 파일 라인 수 만큼 반복
    for i, gold_line in enumerate(gold_lines):
      # 틀린 코드 라인 번호 정답
      gold_line_no = gold_line.split('\t', 1)[1].split(' ', 1)[0]

      # 틀린 코드 라인 번호 예측
      output_line_nos = []
      # 가장 자주 나온 라인 번호
      output_line_no_most = ''

      for j in range(beam_size):
        if (j >= top):
          break
        o_idx = beam_size * i + j
        output_line = output_lines[o_idx]
        output_line_no = output_line.split('\t', 1)[1].split(' ', 1)[0]
        output_line_nos.append(output_line_no)
        if not use_most:
          # 정답과 예측이 같으면 localization + 1
          if (gold_line_no == output_line_no):
            localization += 1
            break
      
      if use_most:
        # 가장 자주 나온 라인 번호
        output_line_no_most = max(set(output_line_nos), key=output_line_nos.count)

        # 정답과 예측이 같으면 localization + 1
        if (gold_line_no == output_line_no_most):
          localization += 1

    # 정답과 예측이 같은 비율
    # ! TOP 이 반영 여부 체크 필요?
    ret = localization / len(gold_lines)
  return ret

if __name__ == '__main__':
  main()
