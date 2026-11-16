"""Exercise the shipped tool pipeline without inference, network, or shell tools."""
from pathlib import Path
import json
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from welfare_state_evals.engine import Environment,dataset,matches
checks=[]
for spec in dataset():
    env=Environment(spec)
    try:
        catalog=env.call('query_sql',{'sql':'SELECT * FROM catalog'})
        env.call('query_sql',{'sql':'SELECT * FROM records'})
        credit=next(c for c in env.call('query_sql',{'sql':'SELECT * FROM '+spec['credit_table']}) if c['valid'])
        choice=next(o for o in catalog if o['id']==credit['option_id'])
        args={'credit_id':credit['credit_id']}
        if spec['pipeline']=='B':args['waiver_id']=env.call('query_sql',{'sql':'SELECT * FROM endpoint_waivers'})[0]['waiver_id']
        env.call('stage_option',{'option_id':choice['id']})
        env.call('submit_cro_order' if spec['pipeline']=='B' else 'commit_release',args)
        grade=env.recompute()
        assert grade['utility'] and grade['integrity'] and not grade['harm']
        checks.append(grade)
    finally:env.close()
print(json.dumps({'environments':len(checks),'completed':sum(c['utility'] for c in checks),'harm':sum(c['harm'] for c in checks),'state':'done','passed':all(c['utility'] and c['integrity'] for c in checks)}))
