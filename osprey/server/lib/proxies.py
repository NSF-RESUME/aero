import os

from proxystore import proxy
from proxystore.connectors.endpoint import EndpointConnector
from proxystore.store import register_store
from proxystore.store import Store
from proxystore.store.utils import get_key

store: Store = Store(name="osprey_data_store", connector=EndpointConnector(endpoints=[os.getenv('PROXYSTORE_ENDPOINT_UUID')], proxystore_dir='/app/osprey/server/proxystore-faker'))
register_store(store)

def proxify(name: str, data) -> str:
    """Proxy JSON object as a Pandas DataFrame."""
    proxy = store.proxy(data)
    return str(get_key(proxy))
