import pandas as pd

from proxystore import proxy
from proxystore.store.endpoint import EndpointStore

url_proxies: dict[str, list[str]] = {}
endpoint_id: str = "f8add8e3-fb27-4cb2-b0c7-be4eb4657507"
store: EndpointStore = EndpointStore(name="osprey_data_store", endpoints=[endpoint_id])


def proxify(name: str, data: list[dict]) -> None:
    """Proxy JSON object as a Pandas DataFrame."""
    df = pd.DataFrame(data)
    proxy = store.proxy(df)

    if name not in url_proxies:
        url_proxies[name] = [proxy]
    else:
        url_proxies[name].append(proxy)
