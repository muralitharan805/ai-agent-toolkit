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
import shutil
import tempfile
from pathlib import Path
from typing import Any, Iterable

MANIFEST_FILENAME = ".toolkit-manifest.json"
MANIFEST_VERSION = 2
SUPPORTED_VERSIONS = {1, 2}


def hash_path(path: Path) -> str:
    """Return a deterministic SHA-256 for a file or directory tree."""
    digest = hashlib.sha256()

    if path.is_symlink():
        digest.update(b"symlink\0")
        digest.update(os.readlink(path).encode("utf-8"))
        return digest.hexdigest()

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
        return {"version": MANIFEST_VERSION, "managed": {}, "aggregates": {}}

    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)

    if not isinstance(data, dict):
        raise ValueError("Manifest root must be a JSON object")

    version = data.get("version")
    if version not in SUPPORTED_VERSIONS:
        raise ValueError(
            f"Unsupported manifest version: {version!r}; supported versions: "
            f"{sorted(SUPPORTED_VERSIONS)}"
        )
    if not isinstance(data.get("managed"), dict):
        raise ValueError("Manifest field 'managed' must be an object")
    if "aggregates" not in data:
        data["aggregates"] = {}
    if not isinstance(data.get("aggregates"), dict):
        raise ValueError("Manifest field 'aggregates' must be an object")

    data["version"] = MANIFEST_VERSION
    return data


def save_manifest(root: Path, data: dict[str, Any]) -> None:
    root.mkdir(parents=True, exist_ok=True)
    target = manifest_path(root)
    data["version"] = MANIFEST_VERSION

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
    source = source.expanduser().resolve()
    if toolkit_root is not None:
        toolkit_root = toolkit_root.expanduser().resolve()
        try:
            return source.relative_to(toolkit_root).as_posix()
        except ValueError:
            pass
    return str(source)


def target_key(root: Path, target: Path) -> str:
    root_resolved = root.expanduser().resolve()
    target_resolved = target.expanduser().resolve(strict=False)
    try:
        return target_resolved.relative_to(root_resolved).as_posix()
    except ValueError as exc:
        raise ValueError(f"Target must be inside manifest root: {target}") from exc


def status(root: Path, key: str, target: Path, source: Path | None) -> dict[str, Any]:
    manifest = load_manifest(root)
    entry = manifest["managed"].get(key)

    if not target.exists() and not target.is_symlink():
        return {"status": "missing", "key": key}

    current_hash = hash_path(target)

    if entry is None:
        if source is not None and source.exists() and current_hash == hash_path(source):
            return {"status": "adoptable", "key": key, "current_hash": current_hash}
        return {"status": "unmanaged", "key": key, "current_hash": current_hash}

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
    *,
    kind: str | None = None,
    scope: str | None = None,
    tool: str | None = None,
) -> dict[str, Any]:
    if not target.exists() and not target.is_symlink():
        raise FileNotFoundError(f"Cannot record missing target: {target}")

    manifest = load_manifest(root)
    target_hash = hash_path(target)
    manifest["managed"][key] = {
        "source": normalized_source(source, toolkit_root),
        "target": target_key(root, target),
        "kind": kind,
        "scope": scope,
        "tool": tool,
        "hash": target_hash,
    }
    save_manifest(root, manifest)
    return {"status": "recorded", "key": key, **manifest["managed"][key]}


def remove(root: Path, key: str) -> dict[str, Any]:
    manifest = load_manifest(root)
    existed = key in manifest["managed"]
    manifest["managed"].pop(key, None)
    save_manifest(root, manifest)
    return {"status": "removed" if existed else "absent", "key": key}


def source_matches(source: str | None, prefixes: Iterable[str]) -> bool:
    normalized = [prefix.rstrip("/") for prefix in prefixes if prefix]
    if not normalized:
        return True
    if not source:
        return False
    source = source.rstrip("/")
    return any(source == prefix or source.startswith(prefix + "/") for prefix in normalized)


def safe_target(root: Path, entry_key: str, entry: dict[str, Any]) -> Path:
    target_rel = entry.get("target") or entry_key
    target = root / target_rel
    root_resolved = root.resolve()
    target_resolved = target.resolve(strict=False)
    try:
        target_resolved.relative_to(root_resolved)
    except ValueError as exc:
        raise ValueError(f"Manifest target escapes root: {target_rel}") from exc
    return target


def prune_empty_parents(path: Path, root: Path) -> None:
    root = root.resolve()
    parent = path.parent
    while parent != root:
        try:
            parent.rmdir()
        except OSError:
            break
        parent = parent.parent


def clean(
    root: Path,
    *,
    force: bool = False,
    source_prefixes: Iterable[str] = (),
    kinds: Iterable[str] = (),
) -> dict[str, Any]:
    """Delete only manifest-owned paths, preserving locally modified content."""
    root = root.expanduser().resolve()
    manifest = load_manifest(root)
    removed: list[str] = []
    missing: list[str] = []
    modified: list[str] = []
    skipped: list[str] = []
    changed = False
    kind_filter = {kind for kind in kinds if kind}

    for key, raw_entry in list(manifest["managed"].items()):
        entry = raw_entry if isinstance(raw_entry, dict) else {}
        source = entry.get("source")
        if kind_filter and entry.get("kind") not in kind_filter:
            skipped.append(key)
            continue
        if not source_matches(source, source_prefixes):
            skipped.append(key)
            continue

        target = safe_target(root, key, entry)
        if not target.exists() and not target.is_symlink():
            manifest["managed"].pop(key, None)
            missing.append(key)
            changed = True
            continue

        current_hash = hash_path(target)
        if current_hash != entry.get("hash") and not force:
            modified.append(key)
            continue

        if target.is_symlink() or target.is_file():
            target.unlink()
        elif target.is_dir():
            shutil.rmtree(target)
        prune_empty_parents(target, root)

        manifest["managed"].pop(key, None)
        removed.append(key)
        changed = True

    if changed:
        save_manifest(root, manifest)

    return {
        "status": "cleaned",
        "removed": removed,
        "missing": missing,
        "modified": modified,
        "skipped": skipped,
        "remaining": len(manifest["managed"]),
    }


def aggregate_add(
    root: Path,
    name: str,
    sources: Iterable[Path],
    toolkit_root: Path | None,
) -> dict[str, Any]:
    """Add normalized source files to a named aggregate without duplicates."""
    manifest = load_manifest(root)
    aggregates = manifest.setdefault("aggregates", {})
    current = aggregates.get(name, [])
    if not isinstance(current, list):
        raise ValueError(f"Aggregate '{name}' must be a list")

    normalized = [
        normalized_source(source, toolkit_root)
        for source in sources
    ]
    merged = list(dict.fromkeys([*current, *normalized]))
    aggregates[name] = merged
    save_manifest(root, manifest)
    return {"status": "updated", "name": name, "sources": merged}


def aggregate_list(root: Path, name: str) -> dict[str, Any]:
    manifest = load_manifest(root)
    current = manifest.get("aggregates", {}).get(name, [])
    if not isinstance(current, list):
        raise ValueError(f"Aggregate '{name}' must be a list")
    return {"status": "ok", "name": name, "sources": current}


def aggregate_remove(
    root: Path,
    name: str,
    *,
    source_prefixes: Iterable[str] = (),
) -> dict[str, Any]:
    """Remove aggregate sources matching prefixes; no prefixes clears the aggregate."""
    manifest = load_manifest(root)
    aggregates = manifest.setdefault("aggregates", {})
    current = aggregates.get(name, [])
    if not isinstance(current, list):
        raise ValueError(f"Aggregate '{name}' must be a list")

    prefixes = [prefix.rstrip("/") for prefix in source_prefixes if prefix]
    if prefixes:
        kept = [source for source in current if not source_matches(source, prefixes)]
        removed = [source for source in current if source_matches(source, prefixes)]
    else:
        kept = []
        removed = list(current)

    if kept:
        aggregates[name] = kept
    else:
        aggregates.pop(name, None)
    save_manifest(root, manifest)
    return {
        "status": "updated",
        "name": name,
        "removed": removed,
        "sources": kept,
    }


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
    record_parser.add_argument("--kind")
    record_parser.add_argument("--scope")
    record_parser.add_argument("--tool")

    remove_parser = subparsers.add_parser("remove")
    remove_parser.add_argument("--root", required=True)
    remove_parser.add_argument("--key", required=True)

    clean_parser = subparsers.add_parser("clean")
    clean_parser.add_argument("--root", required=True)
    clean_parser.add_argument("--force", action="store_true")
    clean_parser.add_argument("--source-prefix", action="append", default=[])
    clean_parser.add_argument("--kind", action="append", default=[])

    aggregate_add_parser = subparsers.add_parser("aggregate-add")
    aggregate_add_parser.add_argument("--root", required=True)
    aggregate_add_parser.add_argument("--name", required=True)
    aggregate_add_parser.add_argument("--source", action="append", required=True)
    aggregate_add_parser.add_argument("--toolkit-root")

    aggregate_list_parser = subparsers.add_parser("aggregate-list")
    aggregate_list_parser.add_argument("--root", required=True)
    aggregate_list_parser.add_argument("--name", required=True)

    aggregate_remove_parser = subparsers.add_parser("aggregate-remove")
    aggregate_remove_parser.add_argument("--root", required=True)
    aggregate_remove_parser.add_argument("--name", required=True)
    aggregate_remove_parser.add_argument("--source-prefix", action="append", default=[])

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
            kind=args.kind,
            scope=args.scope,
            tool=args.tool,
        )
    elif args.command == "clean":
        result = clean(
            root,
            force=args.force,
            source_prefixes=args.source_prefix,
            kinds=args.kind,
        )
    elif args.command == "aggregate-add":
        result = aggregate_add(
            root,
            args.name,
            [Path(source).expanduser() for source in args.source],
            Path(args.toolkit_root).expanduser() if args.toolkit_root else None,
        )
    elif args.command == "aggregate-list":
        result = aggregate_list(root, args.name)
    elif args.command == "aggregate-remove":
        result = aggregate_remove(
            root,
            args.name,
            source_prefixes=args.source_prefix,
        )
    else:
        result = remove(root, args.key)

    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
