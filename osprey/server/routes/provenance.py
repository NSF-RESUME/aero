import uuid

from datetime import datetime
from flask import Blueprint, jsonify, request

from osprey.server.app import db

from osprey.server.app.decorators import authenticated
from osprey.server.app.models import Function
from osprey.server.app.models import Output
from osprey.server.app.models import Provenance
from osprey.server.app.models import SourceVersion
from osprey.server.lib.error import ServiceError

provenance_routes = Blueprint("provenance_routes", __name__, url_prefix="/prov")


@provenance_routes.route("/", methods=["GET"])
@authenticated
def show_provenance():
    page = request.args.get("page") or 1
    per_page = request.args.get("per_page") or 15
    provs = Provenance.query.order_by(Provenance.id.desc()).paginate(
        page=page, per_page=per_page
    )
    result = [p.toJSON() for p in provs]
    return jsonify(result), 200


@provenance_routes.route("/new", methods=["POST"])
@authenticated
def record_provenance():
    try:
        json_data = request.json

        assert "output_fn" in json_data

        sources: list[int] | dict[int, int | None] = json_data["sources"]
        source_ver: list[SourceVersion] = []
        function_uuid = json_data["function_uuid"]

        if isinstance(sources, list):
            sources = {s: None for s in sources}

        # currently just gets last version
        for k, v in sources.items():
            if v is None:
                source_ver.append(
                    SourceVersion.query.filter(SourceVersion.source_id == k)
                    .order_by(SourceVersion.version.desc())
                    .first()
                )
            else:
                source_ver.append(
                    SourceVersion.query.filter(
                        SourceVersion.source_id == k and SourceVersion.version == v
                    ).first()
                )

        # check if function exists, if not create one
        if (
            function_uuid is None
            or (f := Function.query.filter(Function.uuid == function_uuid).first())
            is None
        ):
            function_uuid = str(uuid.uuid4())
            f = Function(uuid=function_uuid)

        # check if provenance already exists
        if (
            p := Provenance.query.filter(
                Provenance.function_id == f.id
                and Provenance.function_args == json_data["kwargs"]
            ).first()
        ) is None:
            # create output and store provenance data
            o = Output(name=json_data["name"])
            o.add_new_version(
                filename=json_data["output_fn"], checksum=json_data["checksum"]
            )
            p = Provenance(
                function_id=f.id,
                derived_from=source_ver,
                contributed_to=[o],
                description=json_data["description"],
                function_args=json_data["kwargs"],
            )
        else:
            # find output instance and add a new version
            # assumes no duplicate names
            o = Output.query.filter(Output.name == json_data["name"]).first()
            o.add_new_version(filename=json_data["output_fn"])

        return jsonify(p.toJSON()), 200
    except ServiceError as s:
        return jsonify(p.toJSON()), s.code
    except Exception as e:
        return jsonify({"code": 500, "message": str(e)}), 500


@provenance_routes.route("/timer/<function_uuid>", methods=["POST"])
@authenticated
def register_flow(function_uuid):
    json_data = request.json

    source_ver: list[SourceVersion] = []
    function_args = json_data["kwargs"]
    sources = json_data["sources"]
    description = json_data["description"]
    policy: int | None = json_data.get("policy")
    timer_delay: int | None = json_data.get("timer_delay")

    p: Provenance | None = None

    if isinstance(sources, list):
        sources = {s: None for s in sources}

    # currently just gets last version
    if sources is not None:
        for k, v in sources.items():
            if v is None:
                source_ver.append(
                    SourceVersion.query.filter(SourceVersion.source_id == k)
                    .order_by(SourceVersion.version.desc())
                    .first()
                )
            else:
                source_ver.append(
                    SourceVersion.query.filter(
                        SourceVersion.source_id == k and SourceVersion.version == v
                    ).first()
                )

    # TODO: add function relationship to provenance
    f = Function.query.filter(Function.uuid == function_uuid).first()

    if f is None:
        f = Function(uuid=function_uuid)
    else:
        p = Provenance.query.filter(
            Provenance.function_id == f.id and Provenance.function_args == function_args
        ).first()

    if p is None:
        p = Provenance(
            function_id=f.id,
            derived_from=source_ver,
            description=description,
            function_args=function_args,
            policy=policy,
            timer=timer_delay,
        )

    if policy is not None and policy == 0:
        job_id = p._start_timer_flow()
        p.timer_job_id = job_id
    elif policy is not None:
        p._run_flow()
        p.last_executed = datetime.now()

    db.session.add(p)
    db.session.commit()

    return jsonify(p.toJSON()), 200
