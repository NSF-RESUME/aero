import pandas as pd
import pickle
import os

from proxystore import proxy
from proxystore.connectors.file import FileConnector
from proxystore.store import register_store
from proxystore.store import Store
from proxystore.store.utils import get_key

# endpoint_id: str = os.getenv('DATABASE_HOST') if os.getenv('DATABASE_HOST') is not None else "7693ee99-090c-429f-a972-7f88bf7df614" 
store: Store = Store(name="osprey_data_store", connector=FileConnector(store_dir='databases'))
register_store(store)

def proxify(name: str, data: list[dict]) -> str:
    """Proxy JSON object as a Pandas DataFrame."""
    df = pd.DataFrame(data)
    proxy = store.proxy(df)
    return str(get_key(proxy))
