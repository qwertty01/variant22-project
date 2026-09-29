import unittest

from src.vfs import Vfs, VfsError


class VfsTests(unittest.TestCase):
    def setUp(self):
        self.vfs = Vfs.from_dict(
            {
                "type": "dir",
                "children": [
                    {
                        "name": "a.txt",
                        "type": "file",
                        "data": "aGVsbG8=",
                    },
                    {
                        "name": "folder",
                        "type": "dir",
                        "children": [],
                    },
                ],
            }
        )

    def test_resolve_and_size(self):
        self.assertEqual(self.vfs.read_file("/a.txt"), b"hello")
        self.assertEqual(self.vfs.size("/a.txt"), 5)

    def test_create_nodes_in_memory(self):
        self.vfs.make_dir("/folder/sub")
        self.vfs.make_file("/folder/sub/file.txt")
        self.assertEqual(self.vfs.normalize("/folder/sub"), "/folder/sub")

    def test_missing_path(self):
        with self.assertRaises(VfsError):
            self.vfs.resolve("/missing")
