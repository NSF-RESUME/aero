# Data Streaming as a Service (DSaaS)

A prototype for the extraction, storage, validation and distribution of public epidemiological data for analysis.

## Installation

### Server

All the server components are made available within a series of dockerfiles provided in Dockerfile.
To install the components, the following steps can be followed:

```
# Build and create necessary volumes

source scripts/prepare_start.sh

docker compose up

```


Clone this repo and install  by running:
`python -m pip install -e .[dev]`

### Starting the server

Create a ProxyStore endpoint and modify the endpoint ID in `osprey/server/proxies.py`. 
Then, the server can be started by running `osprey/server/server.py`.

### Using the client.

Update the URL of the server in `osprey/client/client.py` and access the client API as per example in `osprey/examples/app.py`.

