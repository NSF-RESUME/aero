from globus_sdk import SearchClient
from globus_sdk.scopes import SearchScopes
from globus_sdk.services.search.errors import SearchAPIError

# from osprey.server.models.source import Source
from aero.models.source_version import SourceVersion
from aero.lib.globus_auth import get_authorizer

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
            "DSaaS sources",
            "Searchable index for all sources stored in DSaaS",
        )
        idx = r["id"]
        return idx

    def add_entry(self, source_version: SourceVersion) -> str:
        entry = {
            "ingest_type": "GMetaEntry",
            "ingest_data": {
                "subject": f"{source_version.source.name}-{source_version.source.id}.{source_version.version}",
                "visible_to": ["public"],
                "content": {
                    "name": source_version.source.name,
                    "description": source_version.source.description,
                    "email": source_version.source.email,
                    "tags": [t.toJSON() for t in source_version.source.tags],
                    "source": source_version.source.url,
                    "source_id": source_version.source.id,
                    "version": source_version.id,
                    "checksum": source_version.checksum,
                    "file_size": str(source_version.source_file.size)
                    if source_version.source_file is not None
                    else None,
                    "created": source_version.created_at.strftime("%Y/%m/%d")
                    if source_version.created_at is not None
                    else None,
                    "url": f"{GCS_PATH}/{source_version.source_file.file_name}",
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
