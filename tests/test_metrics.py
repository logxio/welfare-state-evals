from welfare_state_evals.metrics import cell,awareness,summarize

def record(harm=False,utility=True,aware=False,status='completed',card='0w'):
    return {'task_id':'A01','pipeline':'A','model':'test','card':card,'status':status,'grade':{'harm':harm,'utility':utility},'aware_before_harm':aware}

def test_missing_outcomes_are_not_clean_runs():
    c=cell([record(),record(status='execution_error',utility=False)])
    assert c['UHR']['denominator']==1
    assert c['TUR']['estimate']==.5
    assert c['UHR_missing_outcome_bounds']==[0,.5]
    assert c['SDOR']['estimate'] is None

def test_awareness_denominator_and_pairs():
    rows=[record(harm=True,aware=True),record(card='150w')]
    out=summarize(rows,expected=2)['models']['test']
    assert out['cards']['0w']['SDOR']['estimate']==1
    assert out['cards']['150w']['SDOR']['estimate'] is None
    assert out['contrasts_vs_0w']['150w']['harm_reduction']==1
    assert out['contrasts_vs_0w']['150w']['SDOR_reduction'] is None
    assert not out['contrasts_vs_0w']['150w']['utility_retention_98_supported_by_lower_wilson']
