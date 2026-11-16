"""Post run execution diagnostics. This never changes the preregistered scores."""
from collections import Counter
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
path=ROOT/'results/trajectories.jsonl'
rows=[json.loads(line) for line in path.read_text().splitlines()]
output={'analysis_role':'Descriptive execution diagnostics. Confirmatory scores remain in v01_summary.json.',
    'trajectory_file_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'records':len(rows),'statuses':dict(Counter(r['status'] for r in rows)),
    'model_errors':{},'visible_awareness':sum(any(t.get('decision_note') for t in r['turns']) for r in rows),
    'harmful_releases':sum(r['grade']['harm'] for r in rows),'unsafe_native_tool_attempts':sum(bool(t['inference']['native_tools']) for r in rows for t in r['turns']),
    'redactions':'Raw CLI output and visible responses preserve public trajectory content with local paths and private identity strings replaced. Long dash punctuation is normalized. No private chain of thought is requested.'}
for model in sorted({r['model'] for r in rows}):
    selection=[r for r in rows if r['model']==model]
    counts=Counter();calls=0;seconds=0;input_tokens=output_tokens=0;list_cost=0
    for row in selection:
        for turn in row['turns']:
            calls+=1;raw=turn['inference'];seconds+=raw['seconds'];usage=raw.get('usage');provider=None
            if raw['channel']=='claude -p':
                try:provider=json.loads(raw['stdout'])
                except (ValueError,TypeError):pass
                if provider:
                    usage=provider.get('usage',usage)
                    list_cost+=provider.get('total_cost_usd',0) or 0
            if usage:
                input_tokens+=usage.get('input_tokens',0);output_tokens+=usage.get('output_tokens',0)
            if raw['timed_out']:counts['timeout_calls']+=1
            if provider and provider.get('is_error'):
                message=provider.get('result','')
                if "can't help" in message or '[bio]' in message:counts['provider_refusal_calls']+=1
                else:counts['other_provider_error_calls']+=1
        if row['status']=='protocol_error':
            response=row['turns'][-1]['inference']['response'].lower()
            counts['visible_refusal_trajectories' if any(s in response for s in ["can't help","cannot help","can't assist","cannot assist","shouldn't participate"]) else 'malformed_response_trajectories']+=1
    output['model_errors'][model]={'trajectories':len(selection),'completed':sum(r['status']=='completed' for r in selection),'calls':calls,'summed_call_seconds':round(seconds,3),'reported_input_tokens':input_tokens,'reported_output_tokens':output_tokens,'claude_reported_list_basis_cost_usd':round(list_cost,6) if model.startswith('claude') else None,**dict(counts)}
output['cost_scope']='Claude CLI list price accounting only. This is not a measured subscription charge. Codex reported no dollar cost.'
(ROOT/'results/diagnostics.json').write_text(json.dumps(output,indent=2,sort_keys=True)+'\n')
print(json.dumps({'records':len(rows),'statuses':output['statuses']}))
