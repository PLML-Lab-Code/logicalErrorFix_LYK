def execute(idx, exec_file, input, output, msg_file, return_dict):
  # preprocessing for execute
  input_file = f'../data/tmp/input_{idx}.txt'
  output_file = f'../data/tmp/output_{idx}.txt'
  gold_file = f'../data/tmp/gold_{idx}.txt'
  if os.path.exists(input_file):
    os.system(f'rm {input_file}')
  if os.path.exists(output_file):
    os.system(f'rm {output_file}')
  if os.path.exists(gold_file):
    os.system(f'rm {gold_file}')
  
  input_s = input.split('\\n')
    with open(input_file, 'w') as f:
      for i_s in input_s:
        f.write(i_s.strip()+' ')

    gold_s = output.split('\\n')
    with open(gold_file, 'w') as f:
      for g_s in gold_s:
        f.write(g_s.strip()+' ')
            
            
    return_dict[idx] = 'TLE'
    # run and check RE
    os.system('timeout 2 ./'+exec_file + ' < ' + input_file + ' > ' + output_file + ' 2> '+msg_file)
    if os.stat(msg_file).st_size != 0:
      return_dict[idx] = 'RE'
      return
    
  # compare output and gold for judging WA or AC
  with open(output_file, 'r') as f, open(gold_file, 'r') as f1:
    p_lines = f.readlines()
    p = ''
    for p_line in p_lines:
      p += p_line.strip() + ' '
    p = ' '.join(p.split())

    g = f1.readline().strip()
    g = ' '.join(g.split())            

    if p.strip() != g.strip():
      return_dict[idx] = 'WA'
      with open(msg_file, 'w') as f:
        f.write(p.strip())
    else:
      return_dict[idx] = 'AC'

def judge(model, epoch, detail, dataset, beam_size, incorrect_code, predict_stmt):
     
  MSG_DIR = f'../data/result_msg/{model}_{epoch}_{detail}_{dataset}'
  if not os.path.exists(MSG_DIR):
    os.mkdir(MSG_DIR)
    
  # init
  result_to_top = []
  pid, cid, iid ,i_code = incorrect_code
  i_code_lines = i_code.split('|||')
  for beam in range(beam_size):
    tmp_idx, stmt = predict_stmt[beam]      
    no_stmt = stmt.split(' ', 1)[0]
    
    # repair code and remove no_line
    repair_code = ''
    for line in i_code_lines:
      line = line.strip()
      line_parse = line.split(' ', 1)
      if len(line_parse) < 2:
        break
      no_line, code = line_parse 
      # code overwrite
      if no_stmt == no_line: 
        line = stmt   
        s_line_parse = line.split(' ', 1)
        if len(s_line_parse) < 2:
          code = ''
        else:
          code = s_line_parse[1]
      repair_code += code + '|||'
     
    # preprocess for compile
    source_file = 'data/tmp/source.cpp'
    exec_file = 'data/tmp/exec_2slee.exe'
    if os.path.exists(source_file):
      os.system('rm {}'.format(source_file))
    if os.path.exists(exec_file):
      os.system('rm {}'.format(exec_file))
    with open(source_file, 'w') as f:
      lines = repair_code.split('|||')
      for line in lines:
        f.write(line.strip()+'\n')
      
        
    # compile
    ce_msg_file = f'{MSG_DIR}/ce_{pid}_{iid}_{beam}.txt'
    os.system('g++ ' + source_file + ' -o ' + exec_file + ' 2> ' + ce_msg_file)
    if not os.path.exists(exec_file):
      result_to_top.append('CE')
      continue
    
    
    # make samples
    public_testcases_path = f'../data/samples_{dataset}/{pid}.txt'
    private_testcases_path = f'../data/private_samples_{dataset}/{pid}.txt'
    generated_testcases_path = f'../data/generated_samples_{dataset}/{pid}.txt'
    
    def add_testcase(filename, inputs, outputs):
      with open(filename, 'r') as f:
        lines = f.readlines()
        for l in range(0,len(lines), 2):
          input = lines[l].split('"')
          if len(input) < 2:
            break
          input = input[1]
          output = lines[l+1].split('"')[1]

          inputs.append(input)
          outputs.append(output)
          
    inputs, outputs = [], []
    add_testcase(public_testcases_path,inputs,outputs)
    add_testcase(private_testcases_path,inputs,outputs)
    add_testcase(generated_testcases_path,inputs,outputs)

    max_sample_size = 200
    if len(inputs) > max_sample_size and len(outputs) > max_sample_size:
      inputs = inputs[:max_sample_size]
      outputs = outputs[:max_sample_size]


    # execute all samples with multiprocessing
    n_sample = len(inputs)
    n_thread = 40
    n = n_sample // n_thread
    
    cnt_RE, cnt_TLE, cnt_WA, cnt_AC = 0, 0, 0, 0
    for i in range(n+1):
      return_dict = Manager().dict()
      jobs = []
      for j in range(n_thread):
        idx = n_thread*i+j
        if idx >= len(inputs):
          break    
        
        exec_msg_file = f'{MSG_DIR}/exec_{pid}_{iid}_{beam}_{idx}.txt'
        p = Process(target=execute, args=(idx, exec_file, inputs[idx], outputs[idx], exec_msg_file, return_dict), daemon=True)
        p.start()
        jobs.append(p)
        
      for proc in jobs:
        proc.join()
        
      for proc in jobs:
        proc.terminate()
      
      for ret in return_dict.values():
        cnt_RE += (ret == 'RE') 
        cnt_TLE += (ret == 'TLE')
        cnt_WA += (ret == 'WA')
        cnt_AC += (ret == 'AC')
    
    if cnt_RE != 0:
      result_to_top.append('RE')
    elif cnt_TLE != 0:
      result_to_top.append('TLE')
    elif cnt_WA != 0:
      result_to_top.append('WA')
    else:
      result_to_top.append('AC')

  return pid, cid, iid ,result_to_top
  
def compile_and_execute(lang, model, epoch, detail, dataset, beam_size, csv_file):

  # data load
  incorrect_code_path = f'data/edit_distance/drop_by_iid_pair_code_edit_dist_{dataset}.txt'
  incorrect_code = pd.read_csv(incorrect_code_path, sep='\t')
  incorrect_code = incorrect_code[['PID', 'CID', 'IID', 'Incorrect_code']].values.tolist()
  predict_stmt_path = f'../model/{lang}_{model}/epoch_{epoch}/checkpoint-{detail}/{dataset}_0.output' # model/cpp_epoch_beam/checkpoint-best-bleu/test_0.output
  predict_stmt = pd.read_csv(predict_stmt_path, sep='\t', header=None).values.tolist() # idx, stmt
  
  
  # judge(compile and execute) with multi-threading
  n_pred = len(incorrect_code) 
  result_to_csv = []
  for i in range(n_pred):
    if i % 100 == 0:
      print(f'idx : {i}')
    ret = judge(model, epoch, detail, dataset, beam_size, incorrect_code[i], predict_stmt[beam_size*i:beam_size*(i+1)])
    result_to_csv.append(ret)
     
  df = pd.DataFrame(result_to_csv, columns=['PID', 'CID', 'IID', 'RESULT'])
  df.to_csv(csv_file, index=False)
  

def get_ret(csv_file, top):

  df = pd.read_csv(csv_file)
  df = df['RESULT'].values.tolist()
  s = df[0][1:-1]
  sl = s.split(',') 
  sl = [i.strip()[1:-1] for i in sl]

  n = len(df)
  
  sums = [0]*4
  for i in range(n):
    ret = [0]*4
    sl = df[i][1:-1].split(',')
    sl = [i.strip()[1:-1] for i in sl]
    for j in range(10):
      if j >= top:
        continue
      
      ret[0] += (sl[j] == 'CE')
      ret[1] += (sl[j] == 'RE') | (sl[j] == 'TLE')
      ret[2] += (sl[j] == 'WA')
      ret[3] += (sl[j] == 'AC')

    if ret[3]: # ac
      sums[3] += 1
    elif ret[2]: # wa
      sums[2] += 1
    elif ret[1]: # re
      sums[1] += 1
    else:     # ce
      sums[0] += 1
  sums = [round(s/n*100, 1) for s in sums]
  sums.reverse()
  return sums

def eval_localization_precision(lang, model, epoch, detail, dataset, top, beam_size=10):

  '''
  라인넘버 예측이 잘 되었는지 확인하는 모듈
  '''

  DIR = f'../model/{lang}_{model}/epoch_{epoch}/checkpoint-{detail}'
  fgold = DIR + '/'+dataset+'_0.gold'
  foutput = DIR +'/'+dataset+'_0.output'

  ret = 0.0
  with open(fgold, 'r') as g, open(foutput, 'r') as o:
    lines_gold = g.readlines()
    lines_output = o.readlines()
    
    localization = 0
    for i, line_g in enumerate(lines_gold):
      line_no_g = line_g.split('\t')[1].split(' ', 1)[0]
      for j in range(beam_size):
        if j >= top:
          break
        
        idx = beam_size * i + j
        line_o = lines_output[idx]
        line_no_o = line_o.split('\t')[1].split(' ', 1)[0]
        
        if line_no_g == line_no_o:
          localization += 1
          break
    
    ret = round(localization/len(lines_gold)*100, 1)
    
  return ret

    
    

if __name__ == '__main__':
  '''
  datasets = ['test', 'valid', 'train']
  models = ['cpp_epoch_beam', 'cpp_line_beam/cpp_epoch_54', 'cpp_line_beam/cpp_epoch_28', 'cpp_neulab', 'cpp_refine', 'cpp_incorrect_refine']
  epochs = ['28', '14', '10', '6', '3']
  '''
  # edit here #
  langs = ['cpp']         
  models = ['incorrect_refined']
  epochs =['14']
  details = ['best-bleu', 'last']
  datasets = ['valid']
  beam_size = 10 
  
  # edit end #
  
  
  '''
  # compile_and_execute
  freeze_support()
  for lang in langs:
    for model in models:
      for epoch in epochs:
        for detail in details:
          for dataset in datasets:
            csv_file = f'data/judge_result/result_{lang}_{model}_{epoch}_{detail}_{dataset}.csv'
            
            start_time = time.time()
            compile_and_execute(lang, model, epoch, detail, dataset, beam_size, csv_file)
            end_time = time.time()
            print(f'{end_time-start_time} sec')

  '''  
  # get_result with csv
  for lang in langs:
    for model in models:
      for epoch in epochs:
        for detail in details:
          for dataset in datasets:
            print(f'model/{lang}_{model}/epoch_{epoch}/checkpoint-{detail}/{dataset}')
            print('[AC, WA, RE, CE] localization')
            for top in [1, 5, 10]:
              csv_file = f'data/judge_result/result_{lang}_{model}_{epoch}_{detail}_{dataset}.csv'
              
              percentage = get_ret(csv_file, top)
              localization = eval_localization_precision(lang, model, epoch, detail, dataset, top)
              
              print(percentage, localization)
              