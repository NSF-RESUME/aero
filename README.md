# Data Streaming as a Service (DSaaS)

A prototype for the extraction, storage, validation and distribution of public epidemiological data for analysis.

### Examples for using the client.


Prerequisite:

```
pip install -e . # Ensure you are in the root repository
```

Examples:

```
python osprey/client/client.py -list_sources # Lists all the sources

python osprey/client/client.py -create_source -n <name> -u <url> -v <verifier-function-uuid> # Read instructions for creating verifier uuid

python osprey/client/client.py -get_file --source_id <source_id>
```

### To create a function uuid for the verifier/modifier

```

# From /osprey/client/example.py

# Example of the verfier/modifier function

# NOTE:

# The function must:
#   1.    Take (*args, **kwargs)
#   2.    Return args, kwargs
#   3.    For verifier: raise `Exception` if the verifier is failed
#   4.    For modifier: Before returning, kwargs['file']  = modified_file


def verifier(*args, **kwargs):

    # Your downloaded file will be found in kwargs['file']
    # Ensure that you replace the `modified` file to kwargs['file']

    return args, kwargs

from client import source_file, register_function

try:
    response = register_function(verifier)
    assert response.get('code') == 200
    function = response.get('function_id')
except Exception as e:
    print(e)

```


## Installation

### Server

All the server components are made available within a series of dockerfiles provided in Dockerfile.
To install the components, the following steps can be followed:

```
# Build and create necessary volumes

source scripts/prepare_start.sh

docker compose up

```

### Starting the server

Create a ProxyStore endpoint and modify the endpoint ID in `osprey/server/proxies.py`. 
Then, the server can be started by running `osprey/server/server.py`.

