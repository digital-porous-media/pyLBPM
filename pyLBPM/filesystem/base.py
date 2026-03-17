"""Abstract base class for HPC filesystem backends."""

from abc import ABC, abstractmethod
from typing import Callable, List, Optional


class HPCFilesystem(ABC):
    """Backend-agnostic interface for reading/writing files on local or remote HPC systems."""

    @abstractmethod
    def list_dir(self, path: str) -> List[str]:
        """Return a list of filenames in the given directory."""

    @abstractmethod
    def read_file(self, path: str) -> bytes:
        """Read and return the full contents of a file as bytes."""

    @abstractmethod
    def write_file(self, path: str, data: bytes) -> None:
        """Write bytes to a file, creating or overwriting it."""

    @abstractmethod
    def mkdir(self, path: str) -> None:
        """Create a directory (and any missing parents)."""

    @abstractmethod
    def exists(self, path: str) -> bool:
        """Return True if the path exists (file or directory)."""

    @abstractmethod
    def file_size(self, path: str) -> int:
        """Return the size of a file in bytes."""

    @abstractmethod
    def put_file(
        self,
        local_path: str,
        remote_path: str,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> None:
        """Transfer a local file to the remote path.

        Args:
            local_path: Absolute path to the local source file.
            remote_path: Destination path on the remote/target filesystem.
            progress_callback: Optional callable(bytes_transferred, total_bytes).
        """
