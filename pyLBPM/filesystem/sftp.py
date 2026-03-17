"""SFTP filesystem backend — wraps paramiko for SSH-accessible HPC systems."""

import os
import stat
from typing import Callable, List, Optional

from pyLBPM.filesystem.base import HPCFilesystem


class SFTPFilesystem(HPCFilesystem):
    """Filesystem backend using SSH/SFTP via paramiko.

    Connection is established lazily on first use.

    Example config.yml::

        filesystem:
          backend: sftp
          host: login1.tacc.utexas.edu
          username: myuser
          key_file: ~/.ssh/id_rsa   # optional; falls back to ssh-agent / password
          port: 22                  # optional, default 22
    """

    def __init__(self, host: str, username: str, key_file: Optional[str] = None, port: int = 22):
        self.host = host
        self.username = username
        self.key_file = os.path.expanduser(key_file) if key_file else None
        self.port = port
        self._client = None
        self._sftp = None

    def _connect(self):
        import paramiko

        if self._client is not None:
            return
        self._client = paramiko.SSHClient()
        self._client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        kwargs = {"username": self.username, "port": self.port}
        if self.key_file:
            kwargs["key_filename"] = self.key_file
        self._client.connect(self.host, **kwargs)
        self._sftp = self._client.open_sftp()

    def list_dir(self, path: str) -> List[str]:
        self._connect()
        return self._sftp.listdir(path)

    def read_file(self, path: str) -> bytes:
        self._connect()
        with self._sftp.open(path, "rb") as f:
            return f.read()

    def write_file(self, path: str, data: bytes) -> None:
        self._connect()
        self._mkdir_p(os.path.dirname(path))
        with self._sftp.open(path, "wb") as f:
            f.write(data)

    def mkdir(self, path: str) -> None:
        self._connect()
        self._mkdir_p(path)

    def exists(self, path: str) -> bool:
        self._connect()
        try:
            self._sftp.stat(path)
            return True
        except FileNotFoundError:
            return False

    def file_size(self, path: str) -> int:
        self._connect()
        return self._sftp.stat(path).st_size

    def put_file(
        self,
        local_path: str,
        remote_path: str,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> None:
        self._connect()
        self._mkdir_p(os.path.dirname(remote_path))
        self._sftp.put(local_path, remote_path, callback=progress_callback)

    def _mkdir_p(self, remote_path: str) -> None:
        """Recursively create remote directories (mkdir -p equivalent)."""
        if not remote_path or remote_path == "/":
            return
        try:
            self._sftp.stat(remote_path)
        except FileNotFoundError:
            self._mkdir_p(os.path.dirname(remote_path))
            self._sftp.mkdir(remote_path)

    def close(self):
        if self._sftp:
            self._sftp.close()
        if self._client:
            self._client.close()
        self._sftp = None
        self._client = None
