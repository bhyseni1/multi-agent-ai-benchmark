"""Reproducible, real API multi-agent experiment. No mock results."""
import argparse, csv, json, os, random, time, uuid, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

ROLES = {
    'planner': 'Plan a short, correct approach to the arithmetic problem. Do not claim to have calculated with tools.',
    'solver': 'Solve the arithmetic problem carefully. Return the numeric answer in the format ANSWER: <number>.',
    'critic': 'Independently check the solution and point out any arithmetic error. Return a corrected numeric answer in the format ANSWER: <number>.',
    'writer': 'Provide the final correct numerical answer. Your final line MUST be ANSWER: <number>.',
    'coordinator': 'You coordinate solutions. Compare candidate answers and produce the correct result. Final line: ANSWER: <number>.'
}

def api_call(model, system, user, timeout):
    key = os.getenv('OPENAI_API_KEY')
    if not key:
        raise RuntimeError('OPENAI_API_KEY is missing; real LLM runs cannot proceed.')
    payload = json.dumps({'model':model,'messages':[{'role':'system','content':system},{'role':'user','content':user}], 'temperature':0}).encode()
    req = urllib.request.Request('https://api.openai.com/v1/chat/completions', data=payload, headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'}, method='POST')
    start = time.perf_counter()
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.load(resp)
    latency = time.perf_counter()-start
    usage = data.get('usage', {})
    return {'text':data['choices'][0]['message'].get('content') or '', 'latency_s':latency, 'input_tokens':usage.get('prompt_tokens'), 'output_tokens':usage.get('completion_tokens'), 'total_tokens':usage.get('total_tokens'), 'model_returned':data.get('model', model)}

def tasks(n, seed):
    rng = random.Random(seed)
    output=[]
    for i in range(n):
        a,b,c=[rng.randint(10,999) for _ in range(3)]
        level=i%3
        if level==0: expression=f'{a} + {b}'; expected=a+b
        elif level==1: expression=f'({a} + {b}) - {c}'; expected=a+b-c
        else: expression=f'({a} * {b}) - ({c} * 3)'; expected=a*b-c*3
        output.append({'task_id':f'T{i+1:04d}', 'complexity':level+1, 'prompt':f'Compute exactly: {expression}', 'expected':expected})
    return output

def answer(text):
    import re
    matches=re.findall(r'ANSWER:\s*([-+]?\d[\d,]*)',text,re.I)
    return int(matches[-1].replace(',','')) if matches else None

def run_architecture(arch, model, prompt, timeout):
    traces=[]
    def call(role, content):
        result=api_call(model,ROLES[role],content,timeout)
        traces.append({'role':role, **result})
        return result['text']
    if arch=='single':
        final=call('writer',prompt)
    elif arch=='sequential':
        plan=call('planner',prompt)
        solved=call('solver',f'{prompt}\nPlan:\n{plan}')
        checked=call('critic',f'{prompt}\nCandidate:\n{solved}')
        final=call('writer',f'{prompt}\nChecked solution:\n{checked}')
    elif arch=='parallel':
        # Independent solutions run concurrently; coordinator combines results.
        with ThreadPoolExecutor(max_workers=3) as pool:
            futures=[pool.submit(api_call,model,ROLES['solver'],prompt,timeout) for _ in range(3)]
            candidates=[f.result() for f in futures]
        for r in candidates: traces.append({'role':'solver',**r})
        final=call('coordinator',f'{prompt}\nIndependent candidates:\n'+ '\n'.join(x['text'] for x in candidates))
    elif arch=='hierarchical':
        plan=call('planner',prompt)
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures=[pool.submit(api_call,model,ROLES['solver'],f'{prompt}\nPlan: {plan}',timeout) for _ in range(2)]
            candidates=[f.result() for f in futures]
        for r in candidates: traces.append({'role':'solver',**r})
        final=call('coordinator',f'{prompt}\nPlan: {plan}\nSolutions:\n'+'\n'.join(x['text'] for x in candidates))
    else: raise ValueError(arch)
    return final,traces

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--model',required=True,help='Real model identifier available to your OpenAI account')
    p.add_argument('--tasks',type=int,default=12)
    p.add_argument('--repeats',type=int,default=3)
    p.add_argument('--seed',type=int,default=42)
    p.add_argument('--timeout',type=int,default=120)
    p.add_argument('--out',default='results')
    args=p.parse_args()
    if args.tasks<1 or args.repeats<1: p.error('tasks and repeats must be positive')
    if not os.getenv('OPENAI_API_KEY'): p.error('OPENAI_API_KEY required; no simulation fallback')
    out=Path(args.out);out.mkdir(parents=True,exist_ok=True)
    run_id=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:8]
    metadata={'run_id':run_id,'model_requested':args.model,'tasks':args.tasks,'repeats':args.repeats,'seed':args.seed,'timestamp_utc':datetime.now(timezone.utc).isoformat(),'provider':'OpenAI API','temperature_requested':0,'pricing':'not estimated; input/output tokens are recorded'}
    (out/f'{run_id}.metadata.json').write_text(json.dumps(metadata,indent=2))
    fields=['run_id','task_id','complexity','architecture','repeat','expected','predicted','correct','latency_s','input_tokens','output_tokens','total_tokens','api_calls','model_requested','model_returned','error']
    tracefile=out/f'{run_id}.traces.jsonl'
    with (out/f'{run_id}.csv').open('w',newline='') as f, tracefile.open('w') as tf:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();f.flush()
        combinations=[(t,a,r) for t in tasks(args.tasks,args.seed) for a in ['single','sequential','parallel','hierarchical'] for r in range(1,args.repeats+1)]
        random.Random(args.seed).shuffle(combinations)
        for t,arch,rep in combinations:
            start=time.perf_counter();row={'run_id':run_id,'task_id':t['task_id'],'complexity':t['complexity'],'architecture':arch,'repeat':rep,'expected':t['expected'],'model_requested':args.model,'error':''}
            try:
                final,trace=run_architecture(arch,args.model,t['prompt'],args.timeout)
                predicted=answer(final)
                row.update(predicted=predicted,correct=int(predicted==t['expected']),input_tokens=sum(x['input_tokens'] or 0 for x in trace),output_tokens=sum(x['output_tokens'] or 0 for x in trace),total_tokens=sum(x['total_tokens'] or 0 for x in trace),api_calls=len(trace),model_returned=';'.join(sorted(set(x['model_returned'] for x in trace))))
                tf.write(json.dumps({'task':t,'architecture':arch,'repeat':rep,'traces':trace,'final':final})+'\n');tf.flush()
            except (urllib.error.HTTPError,urllib.error.URLError,TimeoutError,RuntimeError,KeyError,ValueError) as e:
                row.update(predicted='',correct='',input_tokens='',output_tokens='',total_tokens='',api_calls='',model_returned='',error=str(e))
            row['latency_s']=round(time.perf_counter()-start,5)
            w.writerow(row);f.flush()
            print(t['task_id'],arch,rep,'correct=',row.get('correct'),'error=',row['error'][:100],flush=True)
    print('Saved',out/f'{run_id}.csv')

if __name__=='__main__':main()
