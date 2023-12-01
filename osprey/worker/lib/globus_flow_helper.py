
"""

NOTE:

1. Stop download if its the same file
2. Direct download using HTTPS using gcs
3. Work on authentication
    i) Use Funcx credentials to register all functions
    ii) Avoid using sudershan@uchicago.edu identity for all globus services

"""

from osprey.server.lib.globus_compute import register_function

def download(*args, **kwargs):
    from osprey.worker.models.source import Source
    from osprey.worker.models.database import Session

    source_id = kwargs['source_id']
    with Session() as session:
        source = session.get(Source, source_id)
        fn, file_format = source.download()

        kwargs['file']       = fn
        kwargs['file_format']= file_format
        kwargs['download']   = True
        return args, kwargs

def user_function_wrapper(*args, **kwargs):
    from osprey.worker.models.source import Source
    from osprey.worker.models.database import Session
    from osprey.server.lib.error import ServiceError, CUSTOM_FUNCTION_ERROR
    from osprey.server.lib.globus_compute import execute_function, get_result

    source_id = kwargs['source_id']
    with Session() as session:
        source = session.get(Source, source_id)

    # Verifier
    if source.verifier is not None:
        try:
            tracker = execute_function(source.verifier, source.user_endpoint, *args, **kwargs)
            args, kwargs = get_result(tracker, block=True)
        except:
            raise ServiceError(CUSTOM_FUNCTION_ERROR, "Verifier failed")

    # Modifier
    if source.modifier is not None:
        try:
            tracker = execute_function(source.modifier, source.user_endpoint, *args, **kwargs)
            args, kwargs = get_result(tracker, block=True)
        except:
            raise ServiceError(CUSTOM_FUNCTION_ERROR, "Modifier failed")

    #TODO: check if data has changed

    return args, kwargs

def flow_db_update(sources: list[str], output_fn: str, function_uuid: str):
    from osprey.server.models.source_version import SourceVersion
    from osprey.server.models.function import Function
    from osprey.server.models.output import Output
    from osprey.server.models.provenance import Provenance

    source_ver: list = []

    # currently just gets last version
    for s_id in sources:
        SourceVersion(version=1, source_id=s_id)
        source_ver.append(SourceVersion.query.filter(SourceVersion.source_id == int(s_id)).order_by(SourceVersion.version.desc()).first())

    f = Function(uuid=function_uuid)
    o = Output(filename=output_fn)

    p = Provenance(function_id=f.id, derived_from=source_ver, contributed_to=[o])


def database_commit(*args, **kwargs):
    from osprey.worker.models.source import Source
    from osprey.worker.models.database import Session

    source_id = kwargs['source_id']
    with Session() as session:
        source = session.get(Source, source_id)
        source.add_new_version(kwargs['file'], kwargs['file_format'])


if __name__ == "__main__":
    print("Globus Flow download",        register_function(download))
    print("Globus Flow database commit", register_function(database_commit))
    print("Globus Flow user function commit", register_function(user_function_wrapper))
    print("UDF Globus Flow db commit", register_function(flow_db_update))