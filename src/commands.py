"""Command implementations for the shell emulator."""

import os
from pathlib import Path
from typing import Callable, List, Optional

from .vfs import Vfs, VfsError


class CommandError(Exception):
    """Raised when a shell command cannot be completed."""


class Shell:
    """Stores shell state and executes supported commands."""

    def __init__(self, vfs: Vfs):
        self.vfs = vfs
        self.cwd = "/"
        self.running = True
        self.commands = self._build_commands()

    def execute(self, line: str) -> str:
        """Parse and execute one shell input line."""
        parts = line.strip().split()
        if not parts:
            return ""
        command = parts[0]
        args = parts[1:]
        handler = self.commands.get(command)
        if handler is None:
            return f"Ошибка: неизвестная команда: {command}"
        try:
            return handler(args)
        except (CommandError, VfsError, OSError) as exc:
            return f"Ошибка: {exc}"

    def _build_commands(self) -> dict[str, Callable[[list[str]], str]]:
        return {
            "ls": self.cmd_ls,
            "cd": self.cmd_cd,
            "du": self.cmd_du,
            "uniq": self.cmd_uniq,
            "mkdir": self.cmd_mkdir,
            "touch": self.cmd_touch,
            "vfs-load": self.cmd_vfs_load,
            "exit": self.cmd_exit,
        }

    def cmd_ls(self, args: List[str]) -> str:
        """List files and directories."""
        show_all = "-a" in args
        long_mode = "-l" in args
        clean = [arg for arg in args if not arg.startswith("-")]
        if len(clean) > 1:
            raise CommandError("ls принимает не более одного пути")
        path = clean[0] if clean else self.cwd
        nodes = self.vfs.list_dir(path)
        if show_all:
            names = [".", ".."] + [node.name for node in nodes]
        else:
            names = [node.name for node in nodes]
        if long_mode:
            return "\n".join(self._ls_long(name, path) for name in names)
        return "  ".join(names)

    def _ls_long(self, name: str, path: str) -> str:
        if name == ".":
            node = self.vfs.resolve(path)
        elif name == "..":
            node = self.vfs.resolve(self._parent_path(path))
        else:
            node = self.vfs.resolve(f"{path.rstrip('/')}/{name}")
        kind = "d" if node.is_dir else "-"
        size = self.vfs.size_node(node)
        return f"{kind} {size:>8} {name}"

    def cmd_cd(self, args: List[str]) -> str:
        """Change the current VFS directory."""
        if len(args) > 1:
            raise CommandError("cd принимает не более одного пути")
        target = args[0] if args else "/"
        node = self.vfs.resolve(target, self.cwd)
        if not node.is_dir:
            raise CommandError(f"Не каталог: {target}")
        self.cwd = self.vfs.normalize(target, self.cwd)
        return self.cwd

    def cmd_du(self, args: List[str]) -> str:
        """Show recursive VFS size in bytes."""
        clean = [arg for arg in args if not arg.startswith("-")]
        if len(clean) > 1:
            raise CommandError("du принимает не более одного пути")
        path = clean[0] if clean else self.cwd
        return f"{self.vfs.size(self.vfs.normalize(path, self.cwd))}"

    def cmd_uniq(self, args: List[str]) -> str:
        """Remove adjacent duplicate lines from text or VFS file."""
        if len(args) != 1:
            raise CommandError("uniq принимает один путь к файлу")
        content = self.vfs.read_file(self.vfs.normalize(args[0], self.cwd))
        text = content.decode("utf-8")
        lines = text.splitlines()
        unique = []
        previous: Optional[str] = None
        for line in lines:
            if line != previous:
                unique.append(line)
            previous = line
        return "\n".join(unique)

    def cmd_mkdir(self, args: List[str]) -> str:
        """Create a directory in the in-memory VFS."""
        if len(args) != 1:
            raise CommandError("mkdir принимает один путь")
        self.vfs.make_dir(self.vfs.normalize(args[0], self.cwd))
        return ""

    def cmd_touch(self, args: List[str]) -> str:
        """Create an empty file in the in-memory VFS."""
        if len(args) != 1:
            raise CommandError("touch принимает один путь")
        self.vfs.make_file(self.vfs.normalize(args[0], self.cwd))
        return ""

    def cmd_vfs_load(self, args: List[str]) -> str:
        """Load another JSON VFS into memory."""
        if len(args) != 1:
            raise CommandError("vfs-load принимает один путь")
        self.vfs = Vfs.from_json_file(args[0])
        self.cwd = "/"
        return f"VFS загружена: {os.path.abspath(args[0])}"

    def cmd_exit(self, args: List[str]) -> str:
        """Stop the emulator session."""
        if args:
            raise CommandError("exit не принимает аргументы")
        self.running = False
        return "Выход."

    def _parent_path(self, path: str) -> str:
        normalized = self.vfs.normalize(path)
        if normalized == "/":
            return "/"
        parts = normalized.rstrip("/").split("/")
        return "/".join(parts[:-1]) or "/"
