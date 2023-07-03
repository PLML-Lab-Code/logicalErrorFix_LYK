# 🥼 logicalErrorFix - LYK 코드 저장소
- [93suhwan/logicalErrorFix](https://github.com/93suhwan/logicalErrorFix) 작업 간 재생산 가능한 코드 작성
- 93suhwan/logicalErrorFix 타겟 commit: [0905e284f417eef450359afb18a775d802fab3b2](https://github.com/93suhwan/logicalErrorFix/tree/0905e284f417eef450359afb18a775d802fab3b2)

---

## ❓ How to use
1. `93suhwan/logicalErrorFix` 클론 및 세팅 완료
2. `logicalErrorFix` 폴더에서
```bash
git clone https://github.com/SemteulGaram/logicalErrorFix_LYK.git
```
3. 폴더명 변경
```bash
mv logicalErrorFix_LYK lyk
```
4. 아래 Available Scripts 리스트에서 원하는 스크립트를 찾고 스크립트를 열어 최상단 `# How to use:` 지시문 따르기
5. Scripts의 모든 명령어는 `logicalErrorFix/lyk` 폴더가 아닌 `logicalErrorFix` 에서 실행해야함
---

## 📜 Available Scripts
### 1. `mdcpp1` (Make Data CPP)
1. `mdcpp1_1_convert_riegeli2cpp.py` - Riegeli 를 이용해 대회파일에서 CPP 파일과 데이터만 출력하기
  - Input File: `/tmp/dm-code_contests/*` (대회 파일, 93suhwan/logicalErrorFix 확인 할 것)
  - Output File: `data/[cppfiles_batch_[correct,incorrect]_[test,train,valid],descriptions,samples,private_samples,generated_samples]`
  - Diff: FS 병목을 해소하기 위해, `93suhwan/logicalErrorFix/convert-riegeli2cpp.py` 의 출력을 `data/cppfiles_batch_[correct,incorrect]_[test,train,valid]/[problem_id].txt` 파일에 다음과 같은 식으로 시리얼라이즈함 `\n¶¶¶\n[id]\n¶¶\n[code]\n¶¶¶\n[id]\n¶¶\n[code] ...`

*****BROKEN PIPE: unavailable `data/edit_distance/pair_solution_[test,train,valid].txt` (need request to JSH)*****

3. `mdcpp1_3-make_code_edit_dist.py`
  - Filtered with target edit_distance
  - Input: Output of `mdcpp1-1-convert_riegeli2cpp.py` and `data/edit_distance/pair_solution_[test,train,valid].txt`
  - Output: `data/edit_distance/pair_code_edit_dist_[test,train,valid].txt`
  - edit_distance: Number of tokens that need to be fixed in the original code
  - Diff: it can decode cppfiles_batch_*
4. `mdcpp1_4_make_unique_correct_list.py`- Remove duplicated dataFrame Columns from `data/edit_distance/pair_code_edit_dist_[test,train,valid].txt`
5. `mdcpp1_5_convert_cpp2gpp.py` - Filtered out only gpp can compile it (Compile)
6. `mdcpp1_6_changsup_make_code_edit_dist.py` - Filtered out only gpp can compile it (Validate) 

### 3. `fl1` (Fault Localization - LCS의 cpp_refined 를 기반으로 한 Fault Localization)
1. `fl1_4_check_eval.py` - .gold 파일과 예측한 .output 파일을 비교해 비교 결과 출력

### 4. `fl2` (Fault Localization - cpp_refined_fl 을 기반으로 한 Fault Localization)
1. `fl2_1_convert_dataset.py`
  - 기존 `refined_pair_code_edit_dist_[test,train,valid].txt` 기반 파일에서 수정해야 하는 코드 stmt에서 line_no 만 남겨서 fl용으로 변환
  - Input: `data/edit_distance/refined_pair_code_edit_dist_[test,train,valid].txt`
  - Output: `data/edit_distance/refined_pair_code_edit_dist_fl_[test,train,valid].txt`
2. `fl2_2_run_train.py`
  - 기존 `train.sh에서 run.py` 를 통해 학습을 하던 것을 `fl2` 프로젝트용으로 변경해 실행
  - Input: `data/edit_distance/refined_pair_code_edit_dist_fl_[test,train,valid].txt`
  - Output: `model/cpp_refined_fl`

### 5. `gpt1` (Code Repair using OpenAI GPT)
1. `gpt1_1_request_openai_gpt3.5.py`
  - GPT 3.5 inference를 통해 코드 생성
  - Input `data/edit_distance/refined_pair_code_edit_dist_[test,train,valid].txt`
  - Output: `lyk/output/gpt1-[NAME]`
2. `gpt_1-2_parse_and_make_code.py`
  - GPT 응답을 분석해서 구조화된 코드로 변환해 데이터베이스 저장
  - Input: `lyk/output/gpt1_[NAME]/*`
  - Output: `lyk/output/gpt1_2_[NAME].db`
3. `gpt_1_3_execute_test.py`
  - GPT 라인 수정 제안 코드를 기존 Incorrect_code 와 합쳐 수정 후 컴파일, AC, TLE, WA, RE, CE 여부 데이터베이스 저장
  - Input `data/edit_distance/refined_pair_code_edit_dist_[test,train,valid].txt`
  - Input: `lyk/output/gpt1_2_[NAME].db`
  - Output: `lyk/output/gpt1_3_[NAME].db`
4. `gpt_1_4_make_report.py`
  - 데이터베이스에 저장된 각종 정보를 기반으로 정확도와 보고서 출력
  - Input: `lyk/output/gpt1_3_[NAME].db`
  - Output: `lyk/output/gpt1_4_[NAME]/*.{png,txt}`
