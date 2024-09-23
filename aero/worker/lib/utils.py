schema = {
    "type": "object",
    "properties": {
        "aero": {
            "type": "object",
            "properties": {
                "input_data": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "object",
                            "properties": {
                                "id": {"type": "string"},
                                "version": {"type": "integer"},
                            },
                        }
                    },
                },
                "output_data": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "object",
                            "properties": {
                                "id": {"type": "string"},
                                "filename": {"type": "string"},
                                "checksum": {"type": "string"},
                                "filesize": {"type": "integer"},
                                "created_at": {"type": "string"},
                            },
                        }
                    },
                },
                "flow_id": {"type": "string"},
            },
        },
        "function_args": {"type": "object"},
    },
}
