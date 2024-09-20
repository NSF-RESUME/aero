import uuid
import json

from flask import Blueprint, jsonify, request

from aero.app import db

from aero.app.decorators import authenticated
from aero.models.function import Function
from aero.models.flows import Flow
from aero.models.flows import TriggerEnum
from aero.models.data import Data
from aero.globus.error import ServiceError

flow_routes = Blueprint("flow_routes", __name__, url_prefix="/flow")


@flow_routes.route("/", methods=["GET"])
@authenticated
def show_flows():
    page = request.args.get("page") or 1
    per_page = request.args.get("per_page") or 15
    provs = Flow.query.order_by(Flow.id.desc()).paginate(page=page, per_page=per_page)
    result = [p.toJSON() for p in provs]
    return jsonify(result), 200


@flow_routes.route("/<flow_id>", methods=["GET"])
@authenticated
def get_flow(flow_id):
    flow = db.session.get(Flow, flow_id)

    if flow is None:
        return jsonify({"code": 404, "message": "Not found"}), 404
    return jsonify(flow.toJSON()), 200


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
                endpoint=json_data["endpoint"],
                email=json_data.get("email", None),
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


@flow_routes.route("/register", methods=["POST"])
@authenticated
def register():
    json_data = request.json

    function_args = json.dumps(json_data)

    # required
    collection_uuid = json_data["collection_uuid"]
    collection_url = json_data["collection_url"]
    gc_endpoint = json_data["gc_endpoint"]

    # optional parameters
    function_uuid = json_data.get("function_uuid", uuid.UUID(int=0))
    input_data = json_data.get("input_data", [])
    output_data = json_data.get("output_data", None)
    description = json_data.get("description", None)
    _ = json_data.get("tags", [])
    rule = json_data.get("rule", None)
    timer = json_data.get("timer", 86400)
    email = json_data.get("email", "")

    fl: Flow | None = None

    # check if function already exists

    f = Function.query.filter(Function.id == function_uuid).first()

    # function does not already exist, so record it
    if f is None:
        f = Function(uuid=function_uuid)
    else:  # function already exists, check if exact flow already exists
        fl = Flow.query.filter(
            Flow.function_id == f.id and Flow.function_args == function_args
        ).first()

    if fl is None:  # flow does not already exist, so we can go ahead and register it
        contributed_to = []

        for out_data in output_data:
            if rule == TriggerEnum.INGESTION:
                o = Data(
                    name=out_data["name"],
                    url=out_data["url"],
                    collection_uuid=collection_uuid,
                    collection_url=collection_url,
                    description=description,
                )
            else:
                o = Data(
                    name=out_data["name"],
                    collection_uuid=collection_uuid,
                    collection_url=collection_url,
                    description=description,
                )

            contributed_to.append(o)

        fl = Flow(
            function_id=f.id,
            derived_from=input_data,
            description=description,
            function_args=function_args,
            policy=rule,
            timer=timer,
            contributed_to=contributed_to,
            endpoint=gc_endpoint,
            email=email,
        )
    else:
        fl.timer = 86400
        # return {'status': 'flow exists'}

    if rule is not None and rule == TriggerEnum.INGESTION:
        fl.timer_job_id = None
        job_id = fl._start_ingestion_flow()
        out = job_id
        fl.timer_job_id = job_id
    elif rule is not None:
        out = fl._run_flow()

    else:
        out = fl._run_flow()

    return json.dumps({"my out": out})


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
    endpoint: str = json_data["endpoint"]

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
            endpoint=endpoint,
            email=json_data.get("email", None),
        )

    if trigger is not None and trigger == 0:
        job_id = p._start_timer_flow()
        p.timer_job_id = job_id
    elif trigger is not None:
        p._run_flow()

    db.session.add(p)
    db.session.commit()

    return jsonify(p.toJSON()), 200
