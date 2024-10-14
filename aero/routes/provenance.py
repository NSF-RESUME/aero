from flask import Blueprint, jsonify, request

from aero.app import db
from aero.app.decorators import authenticated
from aero.models.data import Data
from aero.models.data_version import DataVersion
from aero.models.provenance import Provenance

provenance_routes = Blueprint("provenance_routes", __name__, url_prefix="/prov")


@provenance_routes.route("/", methods=["GET"])
@authenticated
def list_prov():
    page = request.args.get("page", type=int) or 1
    per_page = request.args.get("per_page", type=int) or 15
    provs = Provenance.query.order_by(Provenance.id.desc()).paginate(
        page=page, per_page=per_page
    )
    result = [p.toJSON() for p in provs]
    return jsonify(result), 200


@provenance_routes.route("/new", methods=["POST"])
@authenticated
def add_record():
    try:
        json_data = request.json

        # get versions for input data
        aero_data = json_data["aero"]
        inputs = aero_data["input_data"]
        outputs = aero_data["output_data"]
        flow_id = aero_data["flow_id"]

        input_versions = [
            DataVersion.query.filter(
                (DataVersion.data_id == i["id"]) & (DataVersion.version == i["version"])
            ).first()
            for i in inputs.values()
        ]
        # create new versions for output data
        output_versions = []
        for o in outputs.values():
            d = db.session.get(Data, o["id"])
            d.add_new_version(
                new_file=o["file_bn"],
                format=o["file_format"],
                checksum=o["checksum"],
                size=o["size"],
                created_at=o["created_at"],
                encoding=o.get("encoding", "utf-8"),
            )

            # TODO: maybe fix
            d.rerun_flow()
            output_versions.append(d.last_version())

        p = Provenance(
            flow_id=flow_id, contributed_to=output_versions, derived_from=input_versions
        )
    except Exception as e:
        return jsonify({"code": 500, "message": str(e)}), 500

    return jsonify(p.toJSON())
