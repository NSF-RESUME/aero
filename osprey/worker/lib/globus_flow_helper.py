
from osprey.server.lib.globus_compute import register_function, execute_function, get_result

def download(*args, **kwargs):
    from osprey.worker.models.source import Source
    from osprey.worker.models.database import Session

    source_id = kwargs['source_id']
    with Session() as session:
        source = session.query(Source).get(source_id)
        file, file_format = source.download()

        kwargs['file']       = file
        kwargs['file_format']= file_format
        kwargs['download']   = True
        return args, kwargs
    

# def user_function_wrapper(*args, **kwargs):
#     try:
#         tracker = execute_function(kwargs['function_uuid'], kwargs['endpoint_uuid'])
#         args, kwargs = get_result(tracker)
#     except:
#         pass

#     return args, kwargs


def database_commit(*args, **kwargs):
    from osprey.worker.models.source import Source
    from osprey.worker.models.database import Session

    source_id = kwargs['source_id']
    with Session() as session:
        source = session.query(Source).get(source_id)
        source.add_new_version(kwargs['file'], kwargs['file_format'])


if __name__ == "__main__":
    print("Globus Flow download",        register_function(download))
    print("Globus Flow database commit", register_function(database_commit))