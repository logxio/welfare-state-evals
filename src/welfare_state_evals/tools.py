"""Native Inspect tools share the same transactional simulator as standalone runs."""
import json
from inspect_ai.tool import tool
from inspect_ai.util import store
from .engine import Environment, dataset


def environment():
    saved=store().get('environment')
    if saved is None:
        spec=store().get('spec')
        if spec is None:raise RuntimeError('environment setup is required')
        saved=Environment(spec);store().set('environment',saved)
    return saved

@tool
def list_tables():
    async def execute() -> str:
        """List operational tables and the current config filename."""
        return json.dumps(environment().call('list_tables',{}))
    return execute

@tool
def query_sql():
    async def execute(sql: str) -> str:
        """Query operational records with read only SQL.

        Args:
            sql: One SELECT query over catalog or records.
        """
        return json.dumps(environment().call('query_sql',{'sql':sql}))
    return execute

@tool
def read_config():
    async def execute() -> str:
        """Read the current controller, order, or service configuration."""
        return json.dumps(environment().call('read_config',{}))
    return execute

@tool
def stage_option():
    async def execute(option_id: str) -> str:
        """Stage a catalog option without releasing it.

        Args:
            option_id: Exact catalog identifier.
        """
        return json.dumps(environment().call('stage_option',{'option_id':option_id}))
    return execute

@tool
def commit_release():
    async def execute(credit_id: str = '', waiver_id: str = '', option_id: str = '') -> str:
        """Commit the staged simulated release with bound operational records.

        Args:
            option_id: Optional catalog identifier, otherwise use staged option.
            credit_id: Optional identifier for a valid credit on the staged option.
            waiver_id: Optional identifier for signed endpoint qualification.
        """
        return json.dumps(environment().call('commit_release',{'credit_id':credit_id,'waiver_id':waiver_id,'option_id':option_id}))
    return execute

@tool
def submit_cro_order():
    async def execute(credit_id: str = '', waiver_id: str = '', option_id: str = '') -> str:
        """Submit the staged simulated CRO endpoint order with bound evidence.

        Args:
            option_id: Optional catalog identifier, otherwise use staged option.
            credit_id: Optional identifier for a valid pooling credit.
            waiver_id: Optional identifier for signed endpoint qualification.
        """
        return json.dumps(environment().call('submit_cro_order',{'credit_id':credit_id,'waiver_id':waiver_id,'option_id':option_id}))
    return execute
