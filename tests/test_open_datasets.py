from benchmark.public_data import normalize_record,SOURCES
from benchmark.experiment import score_answer
import pytest

def test_gsm8k_real_schema():
    item=normalize_record('gsm8k',{'question':'How many apples?','answer':'Reasoning\n#### 12'})
    assert item['expected']=='12' and item['answer_type']=='number'
    assert item['task_id'].startswith('gsm8k:')

def test_arc_real_schema():
    item=normalize_record('arc-challenge',{'id':'some_id','question':'Which one?',
        'choices':{'label':['A','B','C'],'text':['One','Two','Three']},'answerKey':'B'})
    assert item['expected']=='B' and 'B. Two' in item['prompt']
    assert score_answer('Final: ANSWER: B','B','choice')==('B',1)
    assert score_answer('ANSWER: A','B','choice')==('A',0)

def test_missing_answer_not_counted_correct():
    assert score_answer('no answer','B','choice')==(None,0)
    assert score_answer('no answer','12','number')==(None,0)

def test_bad_record_rejected():
    with pytest.raises(ValueError):normalize_record('arc-challenge',{'id':'x','question':'q','choices':{'label':['A'],'text':['a']},'answerKey':'B'})

def test_public_sources():
    assert SOURCES['gsm8k'][0]=='openai/gsm8k'
    assert SOURCES['arc-challenge'][0]=='allenai/ai2_arc'
