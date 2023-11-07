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
# Running the script to create necessary volumes, and build projects
export DSAAS_EMAIL_PASSWORD="<password>" GCS_ROOT_DIR="<dir>"
source scripts/prepare_start.sh

docker compose up

```

## Contributions

### Updating Models

flask_sqlalchemy is the library of choice for handling migrations for tables. Docs can be found at https://flask-migrate.readthedocs.io/en/latest/

1. When creating a new model, create in `osprey/server`. Ensure that the new model inherits from db.Model, so that the flask_sqlalchemy can automatically detect the changes to the model variables.
2. When a new column is added, run `flask db migrate -m <-message->` to commit the changes. The command automatically creates a migration file, which can be reused to recreate the database schema.
3. Docker Exec into the WEB application container and then run `flask db upgrade` to run the migrations. Ensure that the database docker container is running, so the migration can be successful
4. All models in `osprey/worker` serve just extensions. So you can load the same values that server models have created, and write custom worker related functions


### Adding New config

1. You can add editable configs in docker-compose.yml to the respective application
2. Non-editable configs for the worker/server can be added to osprey/<-service-name->/config.py
