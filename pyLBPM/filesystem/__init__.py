"""HPC Filesystem abstraction layer for pyLBPM.

Use get_filesystem() to obtain a LocalFilesystem instance.

Example::

    from pyLBPM.filesystem import get_filesystem
    fs = get_filesystem()
    data = fs.read_file("/path/to/sim/input.db")
"""

from pyLBPM.filesystem.base import HPCFilesystem
from typing import Optional

def get_filesystem(config: Optional[dict] = None) -> HPCFilesystem:
    """Return an HPCFilesystem instance (currently LocalFilesystem only).

    Args:
        config: Unused; kept for API compatibility.

    Returns:
        A LocalFilesystem instance.
    """
    from pyLBPM.filesystem.local import LocalFilesystem
    return LocalFilesystem()
