"""Recreate the thirty distributed operational database and config fixtures."""
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from welfare_state_evals.engine import Environment,dataset
for spec in dataset():
    directory=ROOT/'environments'/spec['id']/'initial'
    if directory.exists():raise RuntimeError('initial fixture already exists')
    env=Environment(spec,directory=directory)
    env.close()
print('Materialized 30 operational environments.')
