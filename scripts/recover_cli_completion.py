"""Apply RECOVERY_PROTOCOL.json to terminal successes misclassified as failures."""
from concurrent.futures import ThreadPoolExecutor,as_completed
import copy
from datetime import datetime,timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from welfare_state_evals.cli import infer,parse_codex_events,parse_json
from welfare_state_evals.engine import Environment,canonical,dataset
from welfare_state_evals.metrics import awareness,summarize
spec=importlib.util.spec_from_file_location('benchmark_runner',ROOT/'scripts/run_benchmark.py')
runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner)


def selected(row):
    if row['status']!='execution_error' or not row['turns']:return False
    raw=row['turns'][-1]['inference']
    if raw['channel']!='codex exec':return False
    parsed=parse_codex_events(raw['stdout'])
    return parsed['terminal']=='turn.completed' and parsed['error'] is None and not parsed['native_tools']


def recover(original):
    row=copy.deepcopy(original)
    definition=next(s for s in dataset() if s['id']==row['task_id'])
    env=Environment(definition)
    notes=[t['decision_note'] for t in row['turns'][:-1] if 'decision_note' in t]
    try:
        for event in original['state']['events']:
            output=env.call(event['tool'],event['arguments'])
            if output!=event['result']:raise ValueError('original state replay mismatch')
        if env.committed:raise ValueError('a committed release cannot be recovered')
        current=row['turns'][-1]
        parsed=parse_codex_events(current['inference']['stdout'])
        current['inference'].update(response=parsed['response'],usage=parsed['usage'],native_tools=parsed['native_tools'])
        history=copy.deepcopy(current['input']['messages'])
        old_error=current['inference'].pop('error',None)
        current['inference']['recovered_terminal_success']=True
        status='incomplete';errors=[]
        while True:
            raw=current['inference']
            if raw.get('error'):
                status='execution_error';errors.append(raw['error']);break
            if raw['native_tools']:
                status='protocol_error';errors.append('unauthorized native tool use');break
            try:
                response=parse_json(raw['response']);actions=response['actions']
                if not isinstance(actions,list) or len(actions)>8:raise ValueError('actions must contain at most eight calls')
                note=response.get('decision_note','')
                if not isinstance(note,str):raise ValueError('decision_note must be text')
                notes.append(note);current['decision_note']=note
            except (ValueError,KeyError,TypeError) as error:
                status='protocol_error';errors.append('invalid structured response: '+str(error));break
            history.append({'role':'assistant','content':response})
            results=[]
            for action in actions:
                if not isinstance(action,dict) or not isinstance(action.get('tool'),str) or not isinstance(action.get('arguments',{}),dict):
                    status='protocol_error';errors.append('invalid action schema');break
                output=env.call(action['tool'],action.get('arguments',{}))
                results.append({'tool':action['tool'],'result':output})
                if env.committed:break
            history.append({'role':'tool','content':results});current['tool_results']=results
            if env.committed:status='completed';break
            if status=='protocol_error' or len(row['turns'])>=4:break
            current={'index':len(row['turns']),'system':current['system'],'input':{'messages':copy.deepcopy(history)},
                'inference':infer(row['model'],current['system'],canonical({'messages':history}))}
            row['turns'].append(current)
        grade=env.recompute()
        row.update(status=status,errors=errors,state=env.snapshot(),grade=grade,aware_before_harm=bool(grade['harm'] and awareness(notes)),finished_at_utc=datetime.now(timezone.utc).isoformat(),
            execution_recovery={'protocol':'RECOVERY_PROTOCOL.json','original_status':original['status'],'original_error':old_error,
                'original_model_turns':len(original['turns']),'final_model_turns':len(row['turns'])})
        return row
    finally:env.close()


def main():
    receipt=runner.verify()
    log=ROOT/'results/live_run.log'
    if json.loads(log.read_text().splitlines()[-1]).get('event')!='summary_saved':raise RuntimeError('original matrix must finish before recovery')
    source=ROOT/'results/trajectories.jsonl'
    original=ROOT/'results/original_trajectories.jsonl'
    if original.exists():raise RuntimeError('recovery has already been applied or started')
    rows=[json.loads(l) for l in source.read_text().splitlines()]
    if len(rows)!=600:raise RuntimeError('expected the complete original 600 row matrix')
    shutil.copy2(source,original)
    shutil.copy2(ROOT/'results/v01_summary.json',ROOT/'results/original_v01_summary.json')
    targets=[i for i,r in enumerate(rows) if selected(r)]
    events=[]
    with ThreadPoolExecutor(max_workers=8) as pool:
        futures={pool.submit(recover,rows[i]):i for i in targets}
        for future in as_completed(futures):
            i=futures[future];before=rows[i];after=future.result();rows[i]=after
            event={'task_id':after['task_id'],'model':after['model'],'card':after['card'],'before':before['status'],'after':after['status'],'turns':len(after['turns'])}
            events.append(event);print(json.dumps(event),flush=True)
    amendment_sha=receipt['amendment_sha256']
    for r in rows:r['preregistration_amendment_sha256']=amendment_sha
    runner.recompute_results(rows)
    temp=source.with_suffix('.tmp');temp.write_text(''.join(canonical(r)+'\n' for r in rows));temp.replace(source)
    summary=summarize(rows,expected=600)
    summary.update(preregistration=receipt,replayed_trajectories=len(rows),generated_at_utc=datetime.now(timezone.utc).isoformat(),
        recovery={'protocol':'RECOVERY_PROTOCOL.json','eligible_rows':len(targets),'original_trajectories_sha256':hashlib.sha256(original.read_bytes()).hexdigest(),'original_summary':'results/original_v01_summary.json','events':events})
    (ROOT/'results/v01_summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'recovered_rows':len(targets),'records':len(rows)}),flush=True)

if __name__=='__main__':main()
