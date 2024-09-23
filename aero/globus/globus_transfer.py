import subprocess


class GlobusTransfer:
    @classmethod
    def ls(cls, endpoint_id) -> str:
        process = subprocess.run(
            ["globus", "ls", f"{endpoint_id}:/~/"], capture_output=True
        )
        return process.stdout.decode()

    @classmethod
    def transfer(cls, src_id, source_file, dest_id, dest_file):
        pass
