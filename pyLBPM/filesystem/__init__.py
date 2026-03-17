"""HPC Filesystem abstraction layer for pyLBPM.

Use get_filesystem() to obtain a backend based on ~/.pyLBPM/config.yml,
or instantiate a backend directly for testing.

Example::

    from pyLBPM.filesystem import get_filesystem
    fs = get_filesystem()
    data = fs.read_file("/scratch/myuser/sim/input.db")
"""

import os
from pathlib import Path
from typing import Optional

import yaml

from pyLBPM.filesystem.base import HPCFilesystem


def get_filesystem(config: Optional[dict] = None) -> HPCFilesystem:
    """Return an HPCFilesystem instance based on config.

    Reads ``~/.pyLBPM/config.yml`` if no config dict is provided.
    Falls back to LocalFilesystem if the config file does not exist.

    Args:
        config: Optional dict with at minimum ``filesystem.backend`` key.
                If None, reads from ``~/.pyLBPM/config.yml``.

    Returns:
        An HPCFilesystem instance for the configured backend.
    """
    if config is None:
        config_path = Path.home() / ".pyLBPM" / "config.yml"
        if config_path.exists():
            with open(config_path) as f:
                config = yaml.safe_load(f) or {}
        else:
            config = {}

    fs_config = config.get("filesystem", {})
    backend = fs_config.get("backend", "local")

    if backend == "local":
        from pyLBPM.filesystem.local import LocalFilesystem
        return LocalFilesystem()

    elif backend == "sftp":
        from pyLBPM.filesystem.sftp import SFTPFilesystem
        return SFTPFilesystem(
            host=fs_config["host"],
            username=fs_config["username"],
            key_file=fs_config.get("key_file"),
            port=fs_config.get("port", 22),
        )

    elif backend == "tapis":
        from pyLBPM.filesystem.tapis import TapisFilesystem
        return TapisFilesystem(
            base_url=fs_config["base_url"],
            tenant=fs_config["tenant"],
            token=fs_config["token"],
        )

    elif backend == "globus":
        from pyLBPM.filesystem.globus import GlobusFilesystem
        return GlobusFilesystem(
            source_endpoint=fs_config["source_endpoint"],
        )

    else:
        raise ValueError(f"Unknown filesystem backend: {backend!r}. "
                         f"Choose from: local, sftp, tapis, globus")
