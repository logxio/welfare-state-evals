import json
from welfare_state_evals.cli import parse_codex_events

def stream(*events):return '\n'.join(json.dumps(e) for e in events)

def test_successful_reconnect_clears_only_transient_errors():
    output=parse_codex_events(stream({'type':'error','message':'Reconnecting 2/5'},
        {'type':'item.completed','item':{'type':'agent_message','text':'{"actions":[]}'}},
        {'type':'turn.completed','usage':{'input_tokens':12}}))
    assert output['terminal']=='turn.completed'
    assert output['error'] is None
    assert output['usage']['input_tokens']==12
    assert output['response']=='{"actions":[]}'

def test_terminal_failure_and_native_calls_are_preserved():
    output=parse_codex_events(stream({'type':'item.completed','item':{'type':'command_execution'}},
        {'type':'error','message':'Reconnecting 2/5'},{'type':'turn.failed','error':'disconnected'}))
    assert output['terminal']=='turn.failed'
    assert output['error']['type']=='turn.failed'
    assert output['native_tools']==['command_execution']

def test_incomplete_stream_is_not_a_completed_turn():
    output=parse_codex_events(stream({'type':'error','message':'disconnected'}))
    assert output['terminal'] is None
    assert output['error'] is not None


def test_json_fence_with_commentary_preserves_action_object():
    from welfare_state_evals.cli import parse_json
    value={'actions':[], 'decision_note':'recorded'}
    assert parse_json('```json\n'+json.dumps(value)+'\n```\nAdditional commentary.')==value

def test_partial_json_is_not_completed_by_parser():
    import pytest
    from welfare_state_evals.cli import parse_json
    with pytest.raises(ValueError):parse_json('{"actions":[],"decision_note":"incomplete"')
