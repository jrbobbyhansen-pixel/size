#!/usr/bin/env python3
"""size — CLI directory size analyzer.

Recursively calculate directory sizes with human-readable output,
sorting, depth control, and file-type filtering. Zero external deps.
"""

import argparse
import os
import sys
import textwrap

__version__ = "1.0.0"
__prog__ = "size"


# ── helpers ──────────────────────────────────────────────────────────────

_UNITS = ["B", "KB", "MB", "GB", "TB"]


def _human(size: int) -> str:
    """Convert byte count to human-readable string."""
    if size == 0:
        return "0 B"
    unit_idx = 0
    fsize = float(size)
    while fsize >= 1024 and unit_idx < len(_UNITS) - 1:
        fsize /= 1024
        unit_idx += 1
    if unit_idx == 0:
        return f"{int(fsize)} B"
    return f"{fsize:.2f} {_UNITS[unit_idx]}"


def _walk_size(
    root: str,
    max_depth: int | None,
    file_ext: str | None,
    _depth: int = 0,
) -> int:
    """Recursively compute total size of *root*.

    Parameters
    ----------
    root : str
        Directory or file path to measure.
    max_depth : int or None
        Maximum recursion depth (None = unlimited).
    file_ext : str or None
        If set, only count files with this extension (e.g. ".py").
    _depth : int
        Internal recursion depth tracker.

    Returns
    -------
    int
        Total size in bytes.
    """
    if max_depth is not None and _depth > max_depth:
        return 0

    try:
        if os.path.isfile(root) or os.path.islink(root):
            if file_ext and not root.endswith(file_ext):
                return 0
            try:
                return os.path.getsize(root)
            except OSError:
                return 0

        total = 0
        with os.scandir(root) as it:
            for entry in it:
                try:
                    if entry.is_dir(follow_symlinks=False):
                        total += _walk_size(
                            entry.path, max_depth, file_ext, _depth + 1
                        )
                    elif entry.is_file(follow_symlinks=False):
                        if file_ext and not entry.name.endswith(file_ext):
                            continue
                        try:
                            total += entry.stat(follow_symlinks=False).st_size
                        except OSError:
                            pass
                except OSError:
                    continue
        return total
    except (PermissionError, OSError):
        return 0


def _collect(
    root: str,
    max_depth: int | None,
    file_ext: str | None,
) -> list[tuple[str, int]]:
    """Collect (path, size) for every immediate child of *root*.

    Each child's size is computed recursively (respecting depth/ext).
    """
    results: list[tuple[str, int]] = []
    try:
        with os.scandir(root) as it:
            for entry in it:
                try:
                    if entry.is_dir(follow_symlinks=False):
                        size = _walk_size(
                            entry.path, max_depth, file_ext,
                        )
                    elif entry.is_file(follow_symlinks=False):
                        if file_ext and not entry.name.endswith(file_ext):
                            continue
                        try:
                            size = entry.stat(follow_symlinks=False).st_size
                        except OSError:
                            size = 0
                    else:
                        continue
                    results.append((entry.path, size))
                except OSError:
                    continue
    except (PermissionError, OSError):
        pass

    results.sort(key=lambda x: x[1], reverse=True)
    return results


# ── CLI ───────────────────────────────────────────────────────────────────


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=__prog__,
        description="Analyze directory sizes recursively.",
        epilog=textwrap.dedent("""\
            Examples:
              %(prog)s                          # current directory
              %(prog)s /var/log                  # specific path
              %(prog)s --depth 1                 # top-level only
              %(prog)s --type .log               # only .log files
              %(prog)s --type .py --depth 2 src   # Python files, 2 levels
              %(prog)s --raw /tmp                 # raw bytes, no sorting
        """),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Directory to analyze (default: current directory)",
    )
    parser.add_argument(
        "--depth", "-d",
        type=int,
        default=None,
        metavar="N",
        help="Max recursion depth (default: unlimited)",
    )
    parser.add_argument(
        "--type", "-t",
        type=str,
        default=None,
        metavar="EXT",
        help="Only count files with this extension (e.g. .py, .log)",
    )
    parser.add_argument(
        "--raw",
        action="store_true",
        help="Output raw byte counts instead of human-readable",
    )
    parser.add_argument(
        "--no-sort",
        action="store_true",
        help="Skip sorting (show entries in filesystem order)",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    target = args.path

    if not os.path.exists(target):
        print(f"error: path does not exist: {target}", file=sys.stderr)
        return 1

    if not os.path.isdir(target):
        # Single file mode
        if args.type and not target.endswith(args.type):
            print(f"0 B\t{target}")
            return 0
        try:
            size = os.path.getsize(target)
        except OSError as e:
            print(f"error: cannot read file: {e}", file=sys.stderr)
            return 1
        if args.raw:
            print(f"{size}\t{target}")
        else:
            print(f"{_human(size)}\t{target}")
        return 0

    # Directory mode
    entries = _collect(target, args.depth, args.type)

    if not args.no_sort:
        entries.sort(key=lambda x: x[1], reverse=True)

    if not entries:
        return 0

    # Find padding width
    if args.raw:
        max_w = max(len(str(s)) for _, s in entries)
        for path, size in entries:
            print(f"{size:>{max_w}}\t{path}")
    else:
        labels = [_human(s) for _, s in entries]
        max_w = max(len(l) for l in labels)
        for (path, _), label in zip(entries, labels):
            print(f"{label:>{max_w}}\t{path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
