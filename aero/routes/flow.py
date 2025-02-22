import hashlib
import uuid
import json

from copy import deepcopy
from flask import Blueprint, jsonify, request

from aero.app import db

from aero.app.decorators import authenticated
from aero.models.function import Function
from aero.models.flows import Flow
from aero.models.data import Data

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


@flow_routes.route("/register", methods=["POST"])
@authenticated
def register():
    json_data = request.json

    flow_kwargs = json_data.get("flow_kwargs", {})

    # required
    # collection_uuid = json_data["collection_uuid"]
    # collection_url = json_data["collection_url"]
    gc_endpoint = json_data["gc_endpoint"]
    pull_function_uuid = json_data["pull_function_uuid"]
    commit_function_uuid = json_data["commit_function_uuid"]

    # optional parameters
    function_uuid = json_data.get("function_uuid", uuid.UUID(int=0))
    input_data = json_data.get("input_data", {})
    output_data = json_data.get("output_data", {})
    description = json_data.get("description", None)
    _ = json_data.get("tags", [])
    rule = json_data.get("rule", None)
    timer = json_data.get("timer", 86400)
    email = json_data.get("email", "")

    fl: Flow | None = None

    # check if function already exists

    f = Function.query.filter(Function.id == function_uuid).first()
    p_func = Function.query.filter(Function.id == pull_function_uuid).first()
    c_func = Function.query.filter(Function.id == commit_function_uuid).first()

    all_args = deepcopy(flow_kwargs)
    all_args["input_data"] = input_data
    arg_hash = hashlib.md5(
        json.dumps(all_args, sort_keys=True).encode("utf-8")
    ).hexdigest()

    # function does not already exist, so record it
    if f is None:
        f = Function(uuid=function_uuid)
    # TODO: Currently a bug here. Need to add a checksum for the flow
    else:  # function already exists, check if exact flow already exists
        fl = Flow.query.filter(
            (Flow.function_id == f.id) & (Flow.arg_hash == arg_hash)
        ).first()

    if p_func is None:
        p_func = Function(uuid=pull_function_uuid)
    if c_func is None:
        c_func = Function(uuid=commit_function_uuid)

    if fl is None:  # flow does not already exist, so we can go ahead and register it
        contributed_to = []

        for name, md in output_data.items():
            if "url" in md:
                url = md["url"]
            else:
                url = None

            o = Data(
                name=name,
                url=url,
                collection_uuid=md["collection_uuid"],
                collection_url=md["collection_url"],
                description=description,
            )

            contributed_to.append(o)
            md["id"] = str(o.id)
            md["collection_url"] = o.collection_url
            md["collection_uuid"] = o.collection_uuid

        derived_from = []

        for in_data in input_data.values():
            d = db.session.get(Data, in_data["id"])
            # add collection url to in_data
            in_data["collection_url"] = d.collection_url
            in_data["collection_uuid"] = d.collection_uuid
            derived_from.append(d)

        flow_invocation = []
        if isinstance(flow_kwargs, list):
            for fkw in flow_kwargs:
                aero_data = {}
                aero_data["input_data"] = input_data
                aero_data["output_data"] = output_data
                aero_data["flow_id"] = None

                fkw["aero"] = aero_data

            flow_invocation.append(fkw)

        else:  # assume it's just a dict of kwargs
            aero_data = {}
            aero_data["input_data"] = input_data
            aero_data["output_data"] = output_data
            aero_data["flow_id"] = None

            flow_kwargs["aero"] = aero_data

        fl = Flow(
            function_id=f.id,
            pull_function_id=p_func.id,
            commit_function_id=c_func.id,
            derived_from=derived_from,
            description=description,
            function_args=flow_kwargs,
            policy=rule,
            timer=timer,
            contributed_to=contributed_to,
            endpoint=gc_endpoint,
            email=email,
            arg_hash=arg_hash,
        )

        return json.dumps(fl.toJSON())
    else:
        return jsonify({"code": 501, "message": "Flow already exists"}), 404
