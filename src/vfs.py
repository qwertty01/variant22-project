"""In-memory virtual file system loaded from JSON."""

import base64
import json
from dataclasses import dataclass, field
from typing import Dict, Optional, Union


@dataclass
class VfsNode:
    """A file or directory stored only in emulator memory."""

    name: str
    is_dir: bool
    data: bytes = b""
    children: Dict[str, "VfsNode"] = field(default_factory=dict)


class VfsError(Exception):
    """Raised for invalid VFS operations."""


class Vfs:
    """Provides navigation and in-memory modification of a VFS."""

    def __init__(self, root: VfsNode):
        self.root = root

    @classmethod
    def from_json_file(cls, path: str) -> "Vfs":
        """Load a JSON VFS into memory."""
        with open(path, "r", encoding="utf-8") as file:
            return cls.from_dict(json.load(file))

    @classmethod
    def from_dict(cls, data: dict) -> "Vfs":
        """Build a VFS from its JSON-compatible dictionary."""
        root = cls._node_from_dict(data, "/")
        if not root.is_dir:
            raise VfsError("Корень VFS должен быть каталогом")
        return cls(root)

    @classmethod
    def _node_from_dict(cls, data: dict, name: str) -> VfsNode:
        node_type = data.get("type")
        if node_type == "dir":
            node = VfsNode(name=name, is_dir=True)
            for child in data.get("children", []):
                child_name = child.get("name", "")
                if not child_name or "/" in child_name:
                    raise VfsError("Некорректное имя элемента VFS")
                node.children[child_name] = cls._node_from_dict(
                    child, child_name
                )
            return node
        if node_type == "file":
            encoded = data.get("data", "")
            try:
                content = base64.b64decode(encoded)
            except (ValueError, TypeError) as exc:
                raise VfsError("Некорректные base64-данные") from exc
            return VfsNode(name=name, is_dir=False, data=content)
        raise VfsError("Тип VFS должен быть dir или file")

    def resolve(self, path: str, cwd: str = "/") -> VfsNode:
        """Resolve an absolute or relative path in the VFS."""
        parts = self._parts(path, cwd)
        node = self.root
        for part in parts:
            if not node.is_dir or part not in node.children:
                raise VfsError(f"Путь не найден: {path}")
            node = node.children[part]
        return node

    def normalize(self, path: str, cwd: str = "/") -> str:
        """Return a normalized absolute VFS path."""
        return "/" + "/".join(self._parts(path, cwd))

    def list_dir(self, path: str) -> list[VfsNode]:
        """Return children of a directory."""
        node = self.resolve(path)
        if not node.is_dir:
            raise VfsError(f"Не каталог: {path}")
        return sorted(node.children.values(), key=lambda item: item.name)

    def make_dir(self, path: str) -> None:
        """Create a directory in memory."""
        parent, name = self._parent(path)
        self._ensure_new_name(parent, name)
        parent.children[name] = VfsNode(name=name, is_dir=True)

    def make_file(self, path: str) -> None:
        """Create an empty file in memory."""
        parent, name = self._parent(path)
        self._ensure_new_name(parent, name)
        parent.children[name] = VfsNode(name=name, is_dir=False)

    def size(self, path: str) -> int:
        """Return recursive byte size of a node."""
        node = self.resolve(path)
        if not node.is_dir:
            return len(node.data)
        return sum(self.size_node(child) for child in node.children.values())

    def size_node(self, node: VfsNode) -> int:
        """Return recursive byte size from an already resolved node."""
        if not node.is_dir:
            return len(node.data)
        return sum(self.size_node(child) for child in node.children.values())

    def read_file(self, path: str) -> bytes:
        """Read file content from memory."""
        node = self.resolve(path)
        if node.is_dir:
            raise VfsError(f"Это каталог: {path}")
        return node.data

    def _parent(self, path: str) -> tuple[VfsNode, str]:
        normalized = self.normalize(path)
        if normalized == "/":
            raise VfsError("Нельзя создать объект /")
        parts = normalized.strip("/").split("/")
        name = parts.pop()
        parent_path = "/" + "/".join(parts)
        return self.resolve(parent_path or "/"), name

    @staticmethod
    def _ensure_new_name(parent: VfsNode, name: str) -> None:
        if not parent.is_dir:
            raise VfsError("Родитель не является каталогом")
        if not name or name in parent.children:
            raise VfsError(f"Объект уже существует: {name}")

    @staticmethod
    def _parts(path: str, cwd: str) -> list[str]:
        if not path:
            raise VfsError("Пустой путь")
        raw = path if path.startswith("/") else f"{cwd}/{path}"
        result = []
        for part in raw.split("/"):
            if part in ("", "."):
                continue
            if part == "..":
                if result:
                    result.pop()
                continue
            result.append(part)
        return result
