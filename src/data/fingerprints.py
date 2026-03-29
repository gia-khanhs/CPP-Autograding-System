import hashlib
from pathlib import Path


def fingerprint_directory(root: Path) -> str:
    hasher = hashlib.sha256()

    for path in sorted(root.rglob("*")):
        if path.is_file():
            stat = path.stat()
            hasher.update(str(path.relative_to(root)).encode("utf-8"))
            hasher.update(str(stat.st_mtime_ns).encode("utf-8"))
            hasher.update(str(stat.st_size).encode("utf-8"))

    return hasher.hexdigest()