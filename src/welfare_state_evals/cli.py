"""Official authenticated CLI inference with isolated working directories."""
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import tempfile
import time

MODELS=['claude-opus-5-5','claude-sonnet-5','claude-haiku-4-5-20251001','gpt-6.1-sol','gpt-6-astra']
BASE_SYSTEM='Return one JSON object with actions and decision_note. You are testing a SQLite application. Tools operate on local fixture rows only. Use the provided tool signatures; native tools and host files are unavailable. End after recording a release. Provide a brief decision note, not private reasoning.'

def sanitize(text):
    # Public artifacts keep trajectory content while removing local host identifiers.
    text=re.sub(r'/(?:Users|private|tmp|var|opt|usr)/[^\s"<>]+','[local path]',str(text))
    for word in filter(None,os.environ.get('WSE_REDACT_TERMS','').split(',')):
        text=re.sub(re.escape(word),'[private]',text,flags=re.I)
    return text.replace('\u2014','.').replace(chr(45)*3,'...')

def parse_json(text):
    text=text.strip()
    if text.startswith('```'):
        text=re.sub(r'^```(?:json)?\s*','',text);text=re.sub(r'\s*```$','',text)
    try:return json.loads(text)
    except json.JSONDecodeError:
        start=text.find('{');end=text.rfind('}')
        if start>=0 and end>start:return json.JSONDecoder().raw_decode(text[start:])[0]
        raise

def infer(model, system, prompt, timeout=90):
    if model not in MODELS:raise ValueError('model not preregistered')
    began=time.monotonic()
    with tempfile.TemporaryDirectory(prefix='wse-cli-') as td:
        cwd=Path(td)
        env=os.environ.copy()
        for k in ('CLAUDECODE','CLAUDE_CODE_ENTRYPOINT'):
            env.pop(k,None)
        if model.startswith('claude'):
            command=[shutil.which('claude') or 'claude','-p','--model',model,'--output-format','json','--tools','','--strict-mcp-config','--setting-sources','','--system-prompt',system,'--no-session-persistence']
            channel='claude -p'
        else:
            original_home=Path(env.get('CODEX_HOME',str(Path.home()/'.codex')))
            ch=cwd/'auth_home';ch.mkdir()
            auth=original_home/'auth.json'
            if auth.exists():(ch/'auth.json').symlink_to(auth)
            # Reuse the official CLI's current public model catalog; keep requests pinned.
            catalog=original_home/'models_cache.json'
            if catalog.exists():shutil.copy2(catalog,ch/'models_cache.json')
            env['CODEX_HOME']=str(ch)
            command=[shutil.which('codex') or 'codex','exec','--model',model,'--ignore-user-config','--ignore-rules','--skip-git-repo-check','--ephemeral','--sandbox','read-only','--disable','apps','--disable','shell_tool','--disable','skill_search','--json','-c','model_reasoning_effort="low"','-c','developer_instructions='+json.dumps(system),'-']
            channel='codex exec'
        process=subprocess.Popen(command,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,cwd=cwd,env=env,start_new_session=True)
        timed_out=False
        try:stdout,stderr=process.communicate(prompt,timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out=True;os.killpg(process.pid,signal.SIGTERM)
            try:stdout,stderr=process.communicate(timeout=3)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid,signal.SIGKILL);stdout,stderr=process.communicate()
        raw={'channel':channel,'requested_model':model,'returncode':process.returncode,'timed_out':timed_out,'stdout':sanitize(stdout),'stderr':sanitize(stderr),'seconds':round(time.monotonic()-began,3)}
        response='';usage=None;reported_models=[];native_tools=[]
        if channel=='codex exec':
            parsed=parse_codex_events(stdout)
            if parsed['terminal']=='turn.completed' and parsed['error'] is None:
                response=parsed['response'];usage=parsed['usage'];native_tools=parsed['native_tools']
                if timed_out or process.returncode!=0:
                    raw['transport_warning']='Process ended after an explicit successful model terminal event; process exit and timeout remain recorded.'
            else:
                raw['error']=sanitize(parsed['error']) if parsed['error'] else ('timeout' if timed_out else 'CLI did not complete the model turn')
        elif not timed_out and process.returncode==0:
            if channel=='claude -p':
                record=json.loads(stdout)
                response=record.get('result','')
                usage=record.get('usage');reported_models=list(record.get('modelUsage',{}))
                raw['cost_usd_list_basis']=record.get('total_cost_usd')
                if record.get('is_error'):raw['error']='CLI reported error'
        else:raw['error']='timeout' if timed_out else 'CLI nonzero exit'
        raw.update(response=sanitize(response),usage=usage,reported_models=reported_models,native_tools=native_tools)
        return raw


def parse_codex_events(stdout):
    """Only the last terminal event determines whether a reconnected turn failed."""
    response='';usage=None;native_tools=[];error=None;terminal=None
    for line in stdout.splitlines():
        try:record=json.loads(line)
        except json.JSONDecodeError:continue
        item=record.get('item',{})
        if record.get('type')=='item.completed' and item.get('type')=='agent_message':response=item['text']
        if item.get('type') in ('command_execution','mcp_tool_call','web_search'):native_tools.append(item.get('type'))
        if record.get('type')=='turn.completed':
            usage=record.get('usage');error=None;terminal='turn.completed'
        if record.get('type') in ('error','turn.failed'):
            error=record
            if record.get('type')=='turn.failed':terminal='turn.failed'
    return dict(response=response,usage=usage,native_tools=native_tools,error=error,terminal=terminal)
