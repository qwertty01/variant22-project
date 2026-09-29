import unittest

from src.commands import Shell
from src.vfs import Vfs


class CommandTests(unittest.TestCase):
    def setUp(self):
        self.vfs = Vfs.from_dict(
            {
                "type": "dir",
                "children": [
                    {
                        "name": "data.txt",
                        "type": "file",
                        "data": "b25lCm9uZQp0d28=",
                    },
                    {
                        "name": "dir",
                        "type": "dir",
                        "children": [],
                    },
                ],
            }
        )
        self.shell = Shell(self.vfs)

    def test_ls(self):
        self.assertIn("data.txt", self.shell.execute("ls"))

    def test_cd(self):
        self.assertEqual(self.shell.execute("cd dir"), "/dir")
        self.assertEqual(self.shell.cwd, "/dir")

    def test_du(self):
        self.assertEqual(self.shell.execute("du /data.txt"), "11")

    def test_uniq(self):
        self.assertEqual(self.shell.execute("uniq /data.txt"), "one\ntwo")

    def test_mkdir_and_touch(self):
        self.assertEqual(self.shell.execute("mkdir new"), "")
        self.assertEqual(self.shell.execute("touch new/file.txt"), "")
        self.assertIn("file.txt", self.shell.execute("ls new"))

    def test_errors(self):
        self.assertTrue(self.shell.execute("cd missing").startswith("Ошибка:"))
        self.assertTrue(self.shell.execute("unknown").startswith("Ошибка:"))

    def test_exit(self):
        self.assertEqual(self.shell.execute("exit"), "Выход.")
        self.assertFalse(self.shell.running)
