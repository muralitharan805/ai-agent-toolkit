#!/usr/bin/env python3
# /// script
# dependencies = []
# requires-python = ">=3.9"
# ///

"""Ownership manifest helpers for safe AI Agent Toolkit synchronization."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any

MANIFEST_FILENAME = ".toolkit-manifest.json"
MANIFEST_VERSION = 1


def hash_path(path: Path) -> str:
    """Return a deterministic SHA-256 for a file or directory tree."""
    digest = hashlib.sha256()

    if path.is_file():
        digest.update(b"file\0")
        digest.update(path.name.encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        return digest.hexdigest()

    if not path.is_dir():
        raise FileNotFoundError(str(path))

    digest.update(b"dir\0")
    for item in sorted(path.rglob("*"), key=lambda p: p.as_posix()):
        relative = item.relative_to(path).as_posix()
        if item.is_symlink():
            digest.update(b"symlink\0")
            digest.update(relative.encode("utf-8"))
            digest.update(b"\0")
            digest.update(os.readlink(item).encode("utf-8"))
        elif item.is_file():
            digest.update(b"file\0")
            digest.update(relative.encode("utf-8"))
            digest.update(b"\0")
            digest.update(item.read_bytes())
    return digest.hexdigest()


def manifest_path(root: Path) -> Path:
    return root / MANIFEST_FILENAME


def load_manifest(root: Path) -> dict[str, Any]:
    path = manifest_path(root)
    if not path.exists():
        return {"version": MANIFEST_VERSION, "managed": {}}

    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)

    if not isinstance(data, dict):
        raise ValueError("Manifest root must be a JSON object")
    if data.get("version") != MANIFEST_VERSION:
        raise ValueError(
            f"Unsupported manifest version: {data.get('version')!r}; expected {MANIFEST_VERSION}"
        )
    if not isinstance(data.get("managed"), dict):
        raise ValueError("Manifest field 'managed' must be an object")
    return data


def save_manifest(root: Path, data: dict[str, Any]) -> None:
    root.mkdir(parents=True, exist_ok=True)
    target = manifest_path(root)

    fd, tmp_name = tempfile.mkstemp(prefix=".toolkit-manifest.", suffix=".tmp", dir=root)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2, sort_keys=True)
            handle.write("\n")
        os.replace(tmp_name, target)
    except Exception:
        try:
            os.unlink(tmp_name)
        except FileNotFoundError:
            pass
        raise


def normalized_source(source: Path, toolkit_root: Path | None) -> str:
    source = source.resolve()
    if toolkit_root is not None:
        toolkit_root = toolkit_root.resolve()
        try:
            return source.relative_to(toolkit_root).as_posix()
        except ValueError:
            pass
    return str(source)


def status(root: Path, key: str, target: Path, source: Path | None) -> dict[str, Any]:
    manifest = load_manifest(root)
    entry = manifest["managed"].get(key)

    if not target.exists():
        return {"status": "missing", "key": key}

    current_hash = hash_path(target)

    if entry is None:
        if source is not None and source.exists() and current_hash == hash_path(source):
            return {
                "status": "adoptable",
                "key": key,
                "current_hash": current_hash,
            }
        return {
            "status": "unmanaged",
            "key": key,
            "current_hash": current_hash,
        }

    recorded_hash = entry.get("hash")
    if recorded_hash == current_hash:
        return {
            "status": "clean",
            "key": key,
            "current_hash": current_hash,
            "source": entry.get("source"),
        }

    return {
        "status": "modified",
        "key": key,
        "current_hash": current_hash,
        "recorded_hash": recorded_hash,
        "source": entry.get("source"),
    }


def record(
    root: Path,
    key: str,
    target: Path,
    source: Path,
    toolkit_root: Path | None,
) -> dict[str, Any]:
    if not target.exists():
        raise FileNotFoundError(f"Cannot record missing target: {target}")

    manifest = load_manifest(root)
    target_hash = hash_path(target)
    manifest["managed"][key] = {
        "source": normalized_source(source, toolkit_root),
        "hash": target_hash,
    }
    save_manifest(root, manifest)
    return {
        "status": "recorded",
        "key": key,
        "hash": target_hash,
        "source": manifest["managed"][key]["source"],
    }


def remove(root: Path, key: str) -> dict[str, Any]:
    manifest = load_manifest(root)
    existed = key in manifest["managed"]
    manifest["managed"].pop(key, None)
    save_manifest(root, manifest)
    return {"status": "removed" if existed else "absent", "key": key}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Manage AI Agent Toolkit sync ownership.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    status_parser = subparsers.add_parser("status")
    status_parser.add_argument("--root", required=True)
    status_parser.add_argument("--key", required=True)
    status_parser.add_argument("--target", required=True)
    status_parser.add_argument("--source")

    record_parser = subparsers.add_parser("record")
    record_parser.add_argument("--root", required=True)
    record_parser.add_argument("--key", required=True)
    record_parser.add_argument("--target", required=True)
    record_parser.add_argument("--source", required=True)
    record_parser.add_argument("--toolkit-root")

    remove_parser = subparsers.add_parser("remove")
    remove_parser.add_argument("--root", required=True)
    remove_parser.add_argument("--key", required=True)

    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = Path(args.root).expanduser()

    if args.command == "status":
        result = status(
            root,
            args.key,
            Path(args.target).expanduser(),
            Path(args.source).expanduser() if args.source else None,
        )
    elif args.command == "record":
        result = record(
            root,
            args.key,
            Path(args.target).expanduser(),
            Path(args.source).expanduser(),
            Path(args.toolkit_root).expanduser() if args.toolkit_root else None,
        )
    else:
        result = remove(root, args.key)

    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
