"""GUI application for the Variant 22 shell emulator."""

import argparse
import getpass
import os
import platform
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox

from .commands import Shell
from .vfs import Vfs, VfsError


DEFAULT_VFS = Path(__file__).resolve().parent.parent / "vfs" / "sample.json"


def parse_args() -> argparse.Namespace:
    """Parse physical VFS and startup script paths."""
    parser = argparse.ArgumentParser(description="UNIX-like VFS emulator")
    parser.add_argument("--vfs", required=True, help="путь к JSON VFS")
    parser.add_argument("--script", help="путь к стартовому скрипту")
    return parser.parse_args()


def window_title() -> str:
    """Build the required title from real OS user and host data."""
    user = getpass.getuser()
    host = platform.node() or "localhost"
    return f"Эмулятор - [{user}@{host}]"


def load_script(path: str) -> list[str]:
    """Read a startup script and return executable non-comment lines."""
    text = Path(path).read_text(encoding="utf-8")
    lines = text.splitlines()
    return [
        line for line in lines
        if line.strip() and not line.lstrip().startswith("#")
    ]


class EmulatorGui:
    """Tkinter window that imitates an interactive UNIX terminal."""

    def __init__(self, root: tk.Tk, shell: Shell, script: str | None):
        self.root = root
        self.shell = shell
        self.root.title(window_title())
        self.root.geometry("820x560")
        self.output = tk.Text(root, state="disabled", wrap="word")
        self.output.pack(fill="both", expand=True, padx=10, pady=10)
        self.entry = tk.Entry(root)
        self.entry.pack(fill="x", padx=10, pady=(0, 10))
        self.entry.bind("<Return>", self.on_enter)
        self.entry.focus_set()
        self.write("Эмулятор Variant 22\n")
        self.write(f"VFS: {shell.vfs.root.name}\n")
        if script:
            self.run_script(script)

    def write(self, text: str) -> None:
        """Append text to the terminal area."""
        self.output.configure(state="normal")
        self.output.insert("end", text)
        self.output.see("end")
        self.output.configure(state="disabled")

    def prompt(self) -> str:
        """Return the visible shell prompt."""
        return f"user@host:{self.shell.cwd}$ "

    def on_enter(self, _event=None) -> None:
        """Execute the command entered by the user."""
        line = self.entry.get()
        self.entry.delete(0, "end")
        self.run_line(line)

    def run_line(self, line: str) -> None:
        """Display input and output for one command."""
        self.write(self.prompt() + line + "\n")
        result = self.shell.execute(line)
        if result:
            self.write(result + "\n")
        if not self.shell.running:
            self.entry.configure(state="disabled")

    def run_script(self, path: str) -> None:
        """Execute startup commands as an interactive transcript."""
        try:
            lines = load_script(path)
        except OSError as exc:
            self.write(f"Ошибка стартового скрипта: {exc}\n")
            return
        for line in lines:
            self.run_line(line)
            if not self.shell.running:
                break


def create_shell(vfs_path: str) -> Shell:
    """Load the initial VFS and create shell state."""
    return Shell(Vfs.from_json_file(vfs_path))


def main() -> None:
    """Start the GUI emulator."""
    args = parse_args()
    try:
        shell = create_shell(args.vfs)
    except (OSError, VfsError) as exc:
        messagebox.showerror("Ошибка запуска", str(exc))
        return
    root = tk.Tk()
    EmulatorGui(root, shell, args.script)
    root.mainloop()


if __name__ == "__main__":
    main()
