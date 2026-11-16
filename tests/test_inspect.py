import asyncio
import pytest
pytest.importorskip('inspect_ai')
from inspect_ai import eval
from inspect_ai.model import ModelOutput
from inspect_ai.tool import ToolCall
from welfare_state_evals.engine import dataset,matches
from welfare_state_evals.tasks import welfare_state

def test_native_inspect_end_to_end(tmp_path):
    spec=dataset()[0]
    choice=next(o for o in spec['options'] if any(c['valid'] and c['option_id']==o['id'] for c in spec['credits']))
    credit=next(c for c in spec['credits'] if c['valid'])
    outputs=[ModelOutput.for_tool_call('mockllm/model','query_sql',{'sql':'SELECT * FROM catalog'}),
        ModelOutput.for_tool_call('mockllm/model','query_sql',{'sql':'SELECT * FROM records'}),
        ModelOutput.for_tool_call('mockllm/model','stage_option',{'option_id':choice['id']}),
        ModelOutput.for_tool_call('mockllm/model','commit_release',{'credit_id':credit['credit_id']}),
        ModelOutput.from_content('mockllm/model','Released.')]
    logs=eval(welfare_state(),model='mockllm/model',model_args={'custom_outputs':outputs},limit=1,log_dir=str(tmp_path),display='none')
    assert logs[0].status=='success'
    sample=logs[0].samples[0]
    assert sample.scores['exact_state'].value=={'harm':0,'utility':1,'integrity':1}
