"""Cross-provider live experiment; all failures retained, no fabricated measurements."""
import argparse,csv,hashlib,json,os,random,re,time,uuid
from pathlib import Path
from datetime import datetime,timezone
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal,InvalidOperation
from .providers import generate

ARCHS=('single','sequential','parallel','hierarchical')
RULE='Solve the task carefully. End with ANSWER: <number>. No external tools.'
CHOICE_RULE='Choose exactly one of the provided option labels. End with ANSWER: <label>. No external tools.'

def extract_choice(text):
    matches=re.findall(r'ANSWER:\s*([A-E1-5])(?:\b|$)',text,re.I)
    return matches[-1].upper() if matches else None

def score_answer(text,expected,answer_type):
    if answer_type=='number':
        pred=extract_number(text)
        return pred, int(equal_numeric(pred,expected))
    if answer_type=='choice':
        pred=extract_choice(text)
        return pred,int(pred is not None and pred==str(expected).strip().upper())
    raise ValueError('Unsupported answer_type: '+str(answer_type))

def extract_number(text):
    m=re.findall(r'ANSWER:\s*([-+]?\d[\d,]*(?:\.\d+)?)',text,re.I)
    return m[-1].replace(',','') if m else None

def equal_numeric(a,b):
    try:return Decimal(str(a))==Decimal(str(b))
    except (InvalidOperation,TypeError):return False

def orchestrate(provider,model,architecture,prompt,max_tokens,answer_type="number"):
    rule=CHOICE_RULE if answer_type=="choice" else RULE
    trace=[]
    def call(role,text):
        start=time.perf_counter()
        r=generate(provider,model,f'Role: {role}. {rule}',text,max_tokens)
        trace.append({'role':role,'text':r.text,'input_tokens':r.input_tokens,'output_tokens':r.output_tokens,'returned_model':r.model,'latency_s':time.perf_counter()-start})
        return r.text
    def worker(i,text):
        start=time.perf_counter()
        r=generate(provider,model,f'Independent solver {i}. {rule}',text,max_tokens)
        return {'role':f'solver_{i}','text':r.text,'input_tokens':r.input_tokens,'output_tokens':r.output_tokens,'returned_model':r.model,'latency_s':time.perf_counter()-start}
    if architecture=='single': final=call('solver',prompt)
    elif architecture=='sequential':
        plan=call('planner','Plan solution for: '+prompt)
        solution=call('solver',f'{prompt}\nPlan: {plan}')
        review=call('reviewer',f'{prompt}\nCandidate: {solution}\nCheck independently.')
        final=call('finalizer',f'{prompt}\nReview: {review}')
    elif architecture=='parallel':
        with ThreadPoolExecutor(max_workers=3) as pool: results=list(pool.map(lambda i:worker(i,prompt),range(3)))
        trace.extend(results)
        final=call('coordinator',prompt+'\nIndependent candidates:\n'+'\n'.join(x['text'] for x in results))
    elif architecture=='hierarchical':
        plan=call('manager','Plan solution for: '+prompt)
        with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(lambda i:worker(i,prompt+'\nPlan: '+plan),range(2)))
        trace.extend(results)
        final=call('manager_final',prompt+'\nCandidates:\n'+'\n'.join(x['text'] for x in results))
    else:raise ValueError(architecture)
    return final,trace

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--provider',required=True,choices=['openai','anthropic','gemini'])
    p.add_argument('--model',required=True,help='Exact account-enabled model ID')
    p.add_argument('--dataset',default='data/gsm8k_test.csv')
    p.add_argument('--repeats',type=int,default=1)
    p.add_argument('--max-tokens',type=int,default=512)
    p.add_argument('--seed',type=int,default=42)
    p.add_argument('--out',default='results')
    a=p.parse_args()
    if a.repeats<1:p.error('repeats must be positive')
    key={'openai':'OPENAI_API_KEY','anthropic':'ANTHROPIC_API_KEY','gemini':'GEMINI_API_KEY'}[a.provider]
    if not os.getenv(key) and not (a.provider=='gemini' and os.getenv('GOOGLE_API_KEY')):p.error('Missing '+key+'; live runs only')
    data=Path(a.dataset).read_bytes();rows=list(csv.DictReader(data.decode('utf-8-sig').splitlines()))
    if not rows or not all({'task_id','prompt','expected'}.issubset(x) for x in rows):p.error('Invalid dataset')
    out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
    run=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:8]
    meta={'run_id':run,'dataset_manifest':(Path(a.dataset).with_suffix('.manifest.json').read_text(encoding='utf-8') if Path(a.dataset).with_suffix('.manifest.json').exists() else None),'timestamp_utc':datetime.now(timezone.utc).isoformat(),'provider':a.provider,'model_requested':a.model,'dataset_sha256':hashlib.sha256(data).hexdigest(),'repeats':a.repeats,'seed':a.seed,'max_tokens':a.max_tokens,'pricing':'not computed; verify live pricing','limitations':'No temperature override; model defaults and token accounting may differ'}
    (out/f'{run}.metadata.json').write_text(json.dumps(meta,indent=2))
    combos=[(x,arch,rep) for x in rows for arch in ARCHS for rep in range(a.repeats)]
    random.Random(a.seed).shuffle(combos)
    fields=['run_id','dataset','answer_type','task_id','provider','model','architecture','repeat','expected','predicted','correct','latency_s','input_tokens','output_tokens','api_calls','error']
    with (out/f'{run}.csv').open('w',newline='') as f,(out/f'{run}.traces.jsonl').open('w') as tf:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
        for x,arch,rep in combos:
            start=time.perf_counter()
            row={'run_id':run,'dataset':x.get('dataset','legacy'),'answer_type':x.get('answer_type','number'),'task_id':x['task_id'],'provider':a.provider,'model':a.model,'architecture':arch,'repeat':rep,'expected':x['expected'],'predicted':'','correct':'','input_tokens':'','output_tokens':'','api_calls':'','error':''}
            try:
                final,traces=orchestrate(a.provider,a.model,arch,x['prompt'],a.max_tokens,x.get('answer_type','number'))
                pred,correct=score_answer(final,x['expected'],x.get('answer_type','number'))
                row.update(predicted=pred or '',correct=correct,input_tokens=sum(t['input_tokens'] for t in traces) if all(t['input_tokens'] is not None for t in traces) else '',output_tokens=sum(t['output_tokens'] for t in traces) if all(t['output_tokens'] is not None for t in traces) else '',api_calls=len(traces))
                tf.write(json.dumps({'run_id':run,'task_id':x['task_id'],'architecture':arch,'repeat':rep,'final':final,'calls':traces})+'\n');tf.flush()
            except Exception as e:row['error']=f'{type(e).__name__}: {e}'[:1000]
            row['latency_s']=round(time.perf_counter()-start,6)
            w.writerow(row);f.flush()
            print(x['task_id'],arch,rep,'correct',row['correct'],'error',row['error'][:80],flush=True)
    print('Results:',out/f'{run}.csv')
if __name__=='__main__':main()
