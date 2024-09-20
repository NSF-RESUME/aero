from globus_sdk import SearchClient
from globus_sdk.scopes import SearchScopes
from globus_sdk.services.search.errors import SearchAPIError

# from osprey.server.models.source import Source
from aero.models.data_version import DataVersion
from aero.globus.auth import get_authorizer

GCS_PATH = "https://g-c952d0.1305de.36fe.data.globus.org/source"


class DSaaSSearchClient:
    index: str
    client: SearchClient

    def __init__(self, index=None):
        authorizer = get_authorizer(scopes=SearchScopes.all)
        self.client = SearchClient(authorizer=authorizer)

        if index is not None:
            self.index = index
        else:
            self.index = self.create_source_idx()
            print(f"Created new search index: {self.index}")

    def create_source_idx(self):
        r = self.client.create_index(
            "AERO data",
            "Searchable index for all AERO data",
        )
        idx = r["id"]
        return idx

    def add_entry(self, data_version: DataVersion) -> str:
        entry = {
            "ingest_type": "GMetaEntry",
            "ingest_data": {
                "subject": f"{data_version.data.name}-{data_version.data.id}.{data_version.version}",
                "visible_to": ["public"],
                "content": {
                    "name": data_version.data.name,
                    "description": data_version.data.description,
                    "created_by": data_version.data.output_data[0].toJSON(),
                    "tags": [t.toJSON() for t in data_version.data.tags],
                    "source": data_version.data.url,
                    "data_id": data_version.data.id,
                    "version_id": data_version.id,
                    "version": data_version.version,
                    "checksum": data_version.checksum,
                    "file_size": str(data_version.data_file.size)
                    if data_version.data_file is not None
                    else None,
                    "created": data_version.created_at.strftime("%Y/%m/%d")
                    if data_version.created_at is not None
                    else None,
                    "url": f"{data_version.data.collection_url}/{data_version.data_file.file_name}",
                },
            },
        }

        try:
            response = self.client.ingest(self.index, entry)
            return response.text
        except SearchAPIError as e:
            return e.raw_json

    # def populate_source_idx(self) -> None:
    #     sources = Source.query.all()

    #     entries = {
    #         "ingest_type": "GMetaList",
    #         "ingest_data": {
    #             "gmeta": [
    #                 {
    #                     "subject": f"{s.name}-{s.id}.{v.version}",
    #                     "visible_to": ["public"],
    #                     "content": {
    #                         "name": s.name,
    #                         "description": s.description,
    #                         "email": s.email,
    #                         "tags": [t.toJSON() for t in s.tags],
    #                         "source": s.url,
    #                         "source_id": s.id,
    #                         "version": v.id,
    #                         "checksum": v.checksum,
    #                         "file_size": str(v.source_file.size)
    #                         if v.source_file is not None
    #                         else None,
    #                         "created": v.created_at.strftime("%Y/%m/%d")
    #                         if v.created_at is not None
    #                         else None,
    #                         "url": f"{GCS_PATH}/{v.source_file.file_name}"
    #                         if v.source_file
    #                         else None,
    #                     },
    #                 }
    #                 for s in sources
    #                 for v in s.versions
    #             ]
    #         },
    #     }
    #     try:
    #         self.client.ingest(self.index, entries)
    #     except SearchAPIError as e:
    #         print("Error in populating index", e.raw_json)

    # def create_output_idx(self) -> None:
    #     _ = self.client.create_index(
    #         "DSaaS outputs", "Searchable index for all outputs stored in DSaaS"
    #     )


if __name__ == "__main__":
    from aero.app import create_app

    app = create_app()

    with app.app_context():
        sc = DSaaSSearchClient()
#         sc.populate_source_idx()
# print(sc.index)
# print(sc.get_index(index_id=idx)) #.search(idx, )
