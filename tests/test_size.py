#!/usr/bin/env python3
"""Tests for size.py — CLI directory size analyzer."""

import os
import sys
import tempfile
import unittest

# Ensure we can import size.py
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import size  # noqa: E402


class TestHuman(unittest.TestCase):
    """_human() byte formatting."""

    def test_zero(self):
        self.assertEqual(size._human(0), "0 B")

    def test_bytes(self):
        self.assertEqual(size._human(1), "1 B")
        self.assertEqual(size._human(1023), "1023 B")

    def test_kb(self):
        self.assertEqual(size._human(1024), "1.00 KB")
        self.assertEqual(size._human(2048), "2.00 KB")
        self.assertEqual(size._human(1536), "1.50 KB")

    def test_mb(self):
        self.assertEqual(size._human(1024**2), "1.00 MB")
        self.assertEqual(size._human(5 * 1024**2), "5.00 MB")

    def test_gb(self):
        self.assertEqual(size._human(1024**3), "1.00 GB")

    def test_tb(self):
        self.assertEqual(size._human(1024**4), "1.00 TB")


class TestWalkSize(unittest.TestCase):
    """_walk_size() recursive size calculation."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = self.tmp.name

    def tearDown(self):
        self.tmp.cleanup()

    def _touch(self, relpath, content=b""):
        path = os.path.join(self.root, relpath)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as f:
            f.write(content)
        return path

    def test_empty_dir(self):
        self.assertEqual(size._walk_size(self.root, None, None), 0)

    def test_single_file(self):
        self._touch("a.txt", b"hello")
        self.assertEqual(size._walk_size(self.root, None, None), 5)

    def test_nested_files(self):
        self._touch("a.txt", b"x" * 100)
        self._touch("sub/b.txt", b"y" * 200)
        self._touch("sub/deep/c.txt", b"z" * 300)
        self.assertEqual(size._walk_size(self.root, None, None), 600)

    def test_max_depth(self):
        self._touch("a.txt", b"x" * 10)
        self._touch("sub/b.txt", b"y" * 20)
        self._touch("sub/deep/c.txt", b"z" * 30)
        # depth=0: only root-level files
        self.assertEqual(size._walk_size(self.root, 0, None), 10)
        # depth=1: root + one level
        self.assertEqual(size._walk_size(self.root, 1, None), 30)

    def test_file_extension_filter(self):
        self._touch("a.py", b"x" * 50)
        self._touch("b.txt", b"y" * 100)
        self._touch("sub/c.py", b"z" * 150)
        # Only .py files
        self.assertEqual(size._walk_size(self.root, None, ".py"), 200)
        # Only .txt files
        self.assertEqual(size._walk_size(self.root, None, ".txt"), 100)

    def test_symlink_ignored(self):
        self._touch("real.txt", b"hello")
        os.symlink(
            os.path.join(self.root, "real.txt"),
            os.path.join(self.root, "link.txt"),
        )
        # Symlink is followed by default in _walk_size for files
        # but we use follow_symlinks=False in scandir, so symlinks
        # are not counted as files/dirs
        self.assertEqual(size._walk_size(self.root, None, None), 5)

    def test_permission_denied(self):
        self._touch("ok.txt", b"data")
        restricted = os.path.join(self.root, "noaccess")
        os.makedirs(restricted)
        os.chmod(restricted, 0o000)
        try:
            # Should not crash, just skip the restricted dir
            result = size._walk_size(self.root, None, None)
            self.assertGreaterEqual(result, 4)
        finally:
            os.chmod(restricted, 0o755)


class TestCollect(unittest.TestCase):
    """_collect() child enumeration and sorting."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = self.tmp.name

    def tearDown(self):
        self.tmp.cleanup()

    def _touch(self, relpath, content=b""):
        path = os.path.join(self.root, relpath)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as f:
            f.write(content)
        return path

    def test_empty_dir(self):
        self.assertEqual(size._collect(self.root, None, None), [])

    def test_sorted_by_size_desc(self):
        self._touch("small.txt", b"x" * 10)
        self._touch("large.txt", b"y" * 100)
        self._touch("medium.txt", b"z" * 50)
        results = size._collect(self.root, None, None)
        self.assertEqual(len(results), 3)
        # Largest first
        self.assertIn("large.txt", results[0][0])
        self.assertIn("medium.txt", results[1][0])
        self.assertIn("small.txt", results[2][0])

    def test_file_extension_filter(self):
        self._touch("a.py", b"x" * 50)
        self._touch("b.txt", b"y" * 100)
        results = size._collect(self.root, None, ".py")
        self.assertEqual(len(results), 1)
        self.assertIn("a.py", results[0][0])


class TestCLI(unittest.TestCase):
    """CLI integration via main()."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = self.tmp.name

    def tearDown(self):
        self.tmp.cleanup()

    def _touch(self, relpath, content=b""):
        path = os.path.join(self.root, relpath)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as f:
            f.write(content)
        return path

    def test_version(self):
        with self.assertRaises(SystemExit) as cm:
            size.main(["--version"])
        self.assertEqual(cm.exception.code, 0)

    def test_help(self):
        with self.assertRaises(SystemExit) as cm:
            size.main(["--help"])
        self.assertEqual(cm.exception.code, 0)

    def test_nonexistent_path(self):
        rc = size.main(["/nonexistent/path/12345"])
        self.assertEqual(rc, 1)

    def test_single_file(self):
        f = self._touch("test.txt", b"hello")
        rc = size.main([f])
        self.assertEqual(rc, 0)

    def test_single_file_raw(self):
        f = self._touch("test.txt", b"hello")
        rc = size.main(["--raw", f])
        self.assertEqual(rc, 0)

    def test_single_file_type_mismatch(self):
        f = self._touch("test.txt", b"hello")
        rc = size.main(["--type", ".py", f])
        self.assertEqual(rc, 0)

    def test_directory(self):
        self._touch("a.txt", b"x" * 10)
        self._touch("b.txt", b"y" * 20)
        rc = size.main([self.root])
        self.assertEqual(rc, 0)

    def test_directory_raw(self):
        self._touch("a.txt", b"x" * 10)
        rc = size.main(["--raw", self.root])
        self.assertEqual(rc, 0)

    def test_directory_depth(self):
        self._touch("a.txt", b"x" * 10)
        self._touch("sub/b.txt", b"y" * 20)
        rc = size.main(["--depth", "0", self.root])
        self.assertEqual(rc, 0)

    def test_directory_type_filter(self):
        self._touch("a.py", b"x" * 50)
        self._touch("b.txt", b"y" * 100)
        rc = size.main(["--type", ".py", self.root])
        self.assertEqual(rc, 0)

    def test_no_sort(self):
        self._touch("a.txt", b"x" * 10)
        self._touch("b.txt", b"y" * 20)
        rc = size.main(["--no-sort", self.root])
        self.assertEqual(rc, 0)

    def test_default_path(self):
        """No path argument — uses current directory."""
        rc = size.main([])
        self.assertEqual(rc, 0)


if __name__ == "__main__":
    unittest.main()
