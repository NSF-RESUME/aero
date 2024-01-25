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

    source_id = kwargs["source_id"]
    with Session() as session:
        source = session.get(Source, source_id)
        fn, file_format = source.download()

        kwargs["file"] = fn
        kwargs["file_format"] = file_format
        kwargs["download"] = True
        return args, kwargs


def user_function_wrapper(*args, **kwargs):
    from osprey.worker.models.source import Source
    from osprey.worker.models.database import Session
    from osprey.server.lib.error import ServiceError, CUSTOM_FUNCTION_ERROR
    from osprey.server.lib.globus_compute import execute_function, get_result

    source_id = kwargs["source_id"]
    with Session() as session:
        source = session.get(Source, source_id)

    # Verifier
    if source.verifier is not None:
        try:
            tracker = execute_function(
                source.verifier, source.user_endpoint, *args, **kwargs
            )
            args, kwargs = get_result(tracker, block=True)
        except Exception:
            raise ServiceError(CUSTOM_FUNCTION_ERROR, "Verifier failed")

    # Modifier
    if source.modifier is not None:
        try:
            tracker = execute_function(
                source.modifier, source.user_endpoint, *args, **kwargs
            )
            args, kwargs = get_result(tracker, block=True)
        except Exception:
            raise ServiceError(CUSTOM_FUNCTION_ERROR, "Modifier failed")

    # TODO: check if data has changed

    return args, kwargs


def flow_db_update(sources: list[str], output_fn: str, function_uuid: str):
    from osprey.worker.models.database import Session
    from osprey.worker.models.function import Function
    from osprey.worker.models.output import Output
    from osprey.worker.models.provenance import Provenance
    from osprey.worker.models.source_version import SourceVersion

    source_ver: list = []

    # currently just gets last version
    with Session() as session:
        for s_id in sources:
            source_ver.append(
                session.query(SourceVersion)
                .filter(SourceVersion.source_id == int(s_id))
                .order_by(SourceVersion.version.desc())
                .first()
            )

        f = Function(uuid=function_uuid)
        session.add(f)

        o = Output(filename=output_fn)
        session.add(o)

        p = Provenance(function_id=f.id, derived_from=source_ver, contributed_to=[o])
        session.add(p)
        session.commit()


def database_commit(*args, **kwargs):
    from osprey.worker.models.source import Source
    from osprey.worker.models.database import Session

    source_id = kwargs["source_id"]
    with Session() as session:
        source = session.get(Source, source_id)
        response = source.add_new_version(kwargs["file"], kwargs["file_format"])
        return response


if __name__ == "__main__":
    print("Globus Flow download", register_function(download))
    print("Globus Flow database commit", register_function(database_commit))
    print("Globus Flow user function commit", register_function(user_function_wrapper))
    print("UDF Globus Flow db commit", register_function(flow_db_update))
