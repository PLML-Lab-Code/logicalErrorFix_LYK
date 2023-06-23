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
### 1. `mdcpp_cvrg1` (Make Data CPP _ Convert Riegeli to CPP)
1. `mdcpp_cvg1-convert2_riegeli2cpp.py`
  - 기존 `convert-riegeli2cpp.py` 와 다르게 FS 병목을 최소화 하기 위해 `data/cppfiles_batch_[correct,incorrect]_[test,train,valid]/[problem_id].txt` 에 각 문제를 `\n¶¶¶\n[id]\n¶¶\n[code]\n¶¶¶\n[id]\n¶¶\n[code] ...` 식으로 연결해서 `utf-8` 형식으로 저장
  - 나머지 데이터는 여전히 `data/[descriptions,samples,generated_samples]` 에 생성됨

### 2. `md_pr1` (Make Data _ pair - `md_cvrg1` 의 결과물을 바탕으로 `data/pair_solution` 생성)

### 3. `fl1` (Fault Localization - LCS의 cpp_refined 를 기반으로 한 Fault Localization)
- `fl1-4-check-eval.py` - .gold 파일과 예측한 .output 파일을 비교해 비교 결과 출력

### 4. `fl2` (Fault Localization - ...)

### 5. `gpt35if1` (GPT 3.5 inference only: incorrect_code + directive)
- `gpt35if1-1-create-dataset.py`