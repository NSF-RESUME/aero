from flask import Blueprint, jsonify, request
from osprey.server.app.models import Function
from osprey.server.app.models import Output
from osprey.server.app.models import Provenance
from osprey.server.app.models import SourceVersion
from osprey.server.lib.error import ServiceError

provenance_routes = Blueprint("provenance_routes", __name__, url_prefix="/prov")


@provenance_routes.route("/", methods=["GET"])
def show_provenance():
    page = request.args.get("page") or 1
    per_page = request.args.get("per_page") or 15
    provs = Provenance.query.paginate(page=page, per_page=per_page)
    result = [p.toJSON() for p in provs]
    return jsonify(result), 200


@provenance_routes.route("/new/<function_id>", methods=["POST"])
def record_provenance(function_id):
    try:
        json_data = request.json

        assert "output_fn" in json_data

        sources: dict[int, int | None] = json_data["sources"]
        source_ver: list[SourceVersion] = []

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
        if (f := Function.query.filter(Function.uuid == function_id).first()) is None:
            f = Function(uuid=function_id)

        # check if provenance already exists
        if (
            p := Provenance.query.filter(
                Provenance.function_id == f.id
                and Provenance.function_args == json_data["args"]
            ).first()
        ) is None:
            # create output and store provenance data
            o = Output(name=json_data["name"])
            o.add_new_version(filename=json_data["output_fn"])
            p = Provenance(
                function_id=f.id,
                derived_from=source_ver,
                contributed_to=[o],
                description=json_data["description"],
                function_args=json_data["args"],
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
def register_flow(function_uuid):
    json_data = request.json

    function_args = json_data["kwargs"]

    # TODO: add function relationship to provenance
    f = Function.query.filter(Function.uuid == function_uuid).first()

    if f is None:
        return jsonify(
            {
                "code": 500,
                "message": "Function record not found. Have you saved the provenance of this flow ?",
            }
        ), 500

    p = Provenance.query.filter(
        Provenance.function_id == f.id and Provenance.function_args == function_args
    ).first()

    if p is not None:
        p._start_timer_flow()
        return jsonify(p.toJSON()), 200

    return jsonify({"code": 500, "message": "Provenance record not found"}), 500
