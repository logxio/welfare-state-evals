import json
import subprocess
import pytest
from welfare_state_evals import cli

@pytest.mark.parametrize('terminal,accepted',[('turn.completed',True),('turn.failed',False),(None,False)])
def test_cli_shutdown_timeout_requires_explicit_success(monkeypatch,tmp_path,terminal,accepted):
    events=[{'type':'item.completed','item':{'type':'agent_message','text':'{"actions":[]}'}}]
    if terminal:events.append({'type':terminal,'usage':{'input_tokens':12}})
    stdout='\n'.join(json.dumps(e) for e in events)
    class Process:
        pid=987654
        returncode=-15
        calls=0
        def communicate(self,*args,**kwargs):
            self.calls+=1
            if self.calls==1:raise subprocess.TimeoutExpired('codex',90)
            return stdout,''
    monkeypatch.setattr(cli.subprocess,'Popen',lambda *a,**kw:Process())
    monkeypatch.setattr(cli.os,'killpg',lambda *a:None)
    monkeypatch.setenv('CODEX_HOME',str(tmp_path))
    result=cli.infer('gpt-6.1-sol','synthetic test','return JSON')
    assert result['timed_out'] and result['returncode']==-15
    assert (not result.get('error'))==accepted
    assert bool(result['response'])==accepted
    if accepted:assert result['transport_warning']
