# size — CLI directory size analyzer

Recursively calculate directory sizes with human-readable output, sorting,
depth control, and file-type filtering. Pure Python, zero external deps.

## Install

```bash
# Clone or copy size.py somewhere in your PATH
chmod +x size.py
ln -s "$(pwd)/size.py" ~/.local/bin/size
```

Or just run it directly:

```bash
python3 size.py /some/dir
```

## Usage

```bash
# Current directory
size

# Specific path
size /var/log

# Top-level only
size --depth 1

# Only .log files
size --type .log

# Python files, 2 levels deep
size --type .py --depth 2 src

# Raw byte output
size --raw /tmp

# Skip sorting
size --no-sort

# Help
size --help

# Version
size --version
```

## Features

- **Recursive size calculation** — walks the full tree by default
- **Human-readable output** — auto-scales to KB/MB/GB/TB
- **Sort by size** — largest entries first (descending)
- **Configurable max depth** — `--depth N` limits recursion
- **File-type filter** — `--type .py` only counts matching extensions
- **Raw mode** — `--raw` outputs exact byte counts
- **Portable** — works on macOS, Linux, WSL

## Tests

```bash
python3 -m unittest tests/test_size.py -v
```
