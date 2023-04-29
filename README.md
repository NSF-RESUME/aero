## Prototype

Example of a scraper that retrieves (once) data from the City of Chicago portal, stores data into a ProxyStore endpoint
and provides a REST API for client to retrieve ProxyStore data.

### Installation

Clone this repo and install by running:
`python -m pip install -e .[dev]`

### Starting the server

Create a ProxyStore endpoint and modify the endpoint ID in `osprey/server/proxies.py`. 
Then, the server can be started by running `osprey/server/server.py`.

### Using the client.

Update the URL of the server in `osprey/client/client.py` and access the client API as per example in `osprey/examples/app.py`.

