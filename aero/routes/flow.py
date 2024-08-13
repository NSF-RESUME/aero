import uuid
import json

from flask import Blueprint, jsonify, request

from aero.app import db

from aero.app.decorators import authenticated
from aero.models.function import Function
from aero.models.flows import Flow
from aero.models.data import Data
from aero.globus.error import ServiceError

flow_routes = Blueprint("flow_routes", __name__, url_prefix="/prov")


@flow_routes.route("/", methods=["GET"])
@authenticated
def show_flows():
    page = request.args.get("page") or 1
    per_page = request.args.get("per_page") or 15
    provs = Flow.query.order_by(Flow.id.desc()).paginate(page=page, per_page=per_page)
    result = [p.toJSON() for p in provs]
    return jsonify(result), 200


@flow_routes.route("/new", methods=["POST"])
@authenticated
def record_flow():
    try:
        json_data = request.json

        assert "output_fn" in json_data

        sources: list[str] | None = json_data.get("data", None)
        derived_from: list[Data] = []
        function_uuid = (
            json_data["function_uuid"] if "function_uuid" in json_data else None
        )

        # currently just gets last version
        if sources is not None:
            for k in sources:
                derived_from.append(Data.query.filter(Data.id == k).first())

        # check if function exists, if not create one
        if function_uuid is None:
            function_uuid = str(uuid.uuid4())
        if (f := Function.query.filter(Function.id == function_uuid).first()) is None:
            f = Function(uuid=function_uuid)

        # check if provenance already exists
        if (
            p := Flow.query.filter(
                Flow.function_id == f.id and Flow.function_args == json_data["kwargs"]
            ).first()
        ) is None:
            # create output and store provenance data
            o = Data(
                name=json_data["name"],
                description=json_data["description"],
                collection_url=json_data["collection_url"],
                collection_uuid=json_data["collection_uuid"],
            )
            o.add_new_version(
                new_file=json_data["output_fn"],
                checksum=json_data["checksum"],
                format=json_data["format"],
                size=json_data["size"],
            )
            p = Flow(
                function_id=f.id,
                derived_from=derived_from,
                contributed_to=[o],
                description=json_data["description"],
                function_args=json_data["kwargs"],
            )
        else:
            # find output instance and add a new version
            # assumes no duplicate names
            o = Data.query.filter(Data.name == json_data["name"]).first()
            o.add_new_version(
                new_file=json_data["output_fn"],
                checksum=json_data["checksum"],
                format=json_data["format"],
                size=json_data["size"],
            )

        return jsonify(p.toJSON()), 200
    except ServiceError as s:
        return jsonify(p.toJSON()), s.code
    except Exception as e:
        print("test", e)
        return jsonify({"code": 500, "message": str(e)}), 500


@flow_routes.route("/timer/<function_uuid>", methods=["POST"])
@authenticated
def register_flow(function_uuid):
    json_data = request.json

    derived_from: list[Data] = []
    function_args = json.dumps(json_data)
    sources = json_data.get("data", None)
    description = json_data["description"]
    trigger: int | None = json_data.get("policy")
    timer_delay: int | None = json_data.get("timer_delay")

    p: Flow | None = None

    # currently just gets last version
    if sources is not None:
        for k in sources:
            derived_from.append(Data.query.filter(Data.id == k).first())

    # TODO: add function relationship to provenance
    f = Function.query.filter(Function.id == function_uuid).first()

    if f is None:
        f = Function(uuid=function_uuid)
    else:
        p = Flow.query.filter(
            Flow.function_id == f.id and Flow.function_args == function_args
        ).first()

    if p is None:
        contributed_to = []
        if "name" in json_data and "url" in json_data:
            o = Data(
                name=json_data["name"],
                url=json_data["url"],
                collection_uuid=json_data["collection_uuid"],
                collection_url=json_data["collection_url"],
                description=json_data["description"],
            )
            o.add_new_version(
                new_file=json_data["output_fn"],
                checksum=json_data["checksum"],
                format=json_data["format"],
                size=json_data["size"],
            )
            contributed_to.append(o)

        p = Flow(
            function_id=f.id,
            derived_from=derived_from,
            description=description,
            function_args=function_args,
            policy=trigger,
            timer=timer_delay,
            contributed_to=contributed_to,
        )

    if trigger is not None and trigger == 0:
        job_id = p._start_timer_flow()
        p.timer_job_id = job_id
    elif trigger is not None:
        p._run_flow()

    db.session.add(p)
    db.session.commit()

    return jsonify(p.toJSON()), 200
