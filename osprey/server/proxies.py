import pandas as pd
import pickle

from proxystore import proxy
from proxystore.connectors.file import FileConnector
from proxystore.store import register_store
from proxystore.store import Store
from proxystore.store.utils import get_key

#endpoint_id: str = "7693ee99-090c-429f-a972-7f88bf7df614"
store: Store = Store(name="osprey_data_store", connector=FileConnector(store_dir='databases'))
register_store(store)

def proxify(name: str, data: list[dict]) -> str:
    """Proxy JSON object as a Pandas DataFrame."""
    df = pd.DataFrame(data)
    proxy = store.proxy(df)
    return str(get_key(proxy))


