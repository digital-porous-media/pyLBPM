"""Local filesystem backend — wraps pathlib.Path."""

import os
import shutil
from pathlib import Path
from typing import Callable, List, Optional

from pyLBPM.filesystem.base import HPCFilesystem


class LocalFilesystem(HPCFilesystem):
    """Filesystem backend that operates on the local machine."""

    def list_dir(self, path: str) -> List[str]:
        return [p.name for p in Path(path).iterdir()]

    def read_file(self, path: str) -> bytes:
        return Path(path).read_bytes()

    def write_file(self, path: str, data: bytes) -> None:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)

    def mkdir(self, path: str) -> None:
        Path(path).mkdir(parents=True, exist_ok=True)

    def exists(self, path: str) -> bool:
        return Path(path).exists()

    def file_size(self, path: str) -> int:
        return Path(path).stat().st_size

    def put_file(
        self,
        local_path: str,
        remote_path: str,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> None:
        total = os.path.getsize(local_path)
        Path(remote_path).parent.mkdir(parents=True, exist_ok=True)
        chunk_size = 1024 * 1024  # 1 MB
        transferred = 0
        with open(local_path, "rb") as src, open(remote_path, "wb") as dst:
            while True:
                chunk = src.read(chunk_size)
                if not chunk:
                    break
                dst.write(chunk)
                transferred += len(chunk)
                if progress_callback:
                    progress_callback(transferred, total)
