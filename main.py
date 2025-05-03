import sys
import threading
import subprocess
from pathlib import Path
import os
import tkinter as tk
from tkinter import ttk, messagebox
import locale

# Windows-specific: hide subprocess windows
CREATE_NO_WINDOW = 0x08000000

# Localization resources
lang, _ = locale.getdefaultlocale()
if lang and lang.startswith('uk'):
    from lang.uk import STRINGS as T
else:
    from lang.en import STRINGS as T

class NetshFirewall:
    """
    Wrapper for Windows netsh advfirewall commands: enumerate, add, delete rules.
    """
    def __init__(self, creationflags=0):
        self.creationflags = creationflags

    def _run(self, args, check=True):
        cmd = ["netsh"] + args
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            creationflags=self.creationflags
        )
        if check and result.returncode != 0:
            # provide detailed error info
            error_msg = (
                f"command: {cmd}\n\n"
                f"retcode: {result.returncode}\n\n"
                f"stdout: {result.stdout.strip()}\n\n"
                f"stderr: {result.stderr.strip()}"
            )
            raise RuntimeError(error_msg)
        return result.stdout

    def list_rules(self, prefix=None):
        output = self._run([
            "advfirewall", "firewall", "show", "rule", "name=all"
        ], check=True)
        rules = []
        for line in output.splitlines():
            if line.startswith("Rule Name:"):
                name = line.split(':', 1)[1].strip()
                if not prefix or name.startswith(prefix):
                    rules.append(name)
        return rules

    def delete_rule(self, name):
        try:
            self._run([
                "advfirewall", "firewall", "delete", "rule", f"name={name}"
            ], check=False)
        except RuntimeError:
            pass

    def add_rule(self, name, program, description="", direction="out", action="block", profile="any", remoteip="any", enable="yes"):
        args = [
            "advfirewall", "firewall", "add", "rule",
            f"name={name}",
            f"description={description}",
            f"dir={direction}",
            f"program={program}",
            f"action={action}",
            f"profile={profile}",
            f"remoteip={remoteip}",
            f"enable={enable}",
        ]
        self._run(args)

class AdobeBlockerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(T['app_title'])
        self.firewall = NetshFirewall(creationflags=CREATE_NO_WINDOW)
        self._make_window_draggable()
        self._create_widgets()

    def _make_window_draggable(self):
        def on_press(event):
            self._drag_start_x = event.x
            self._drag_start_y = event.y

        def on_drag(event):
            x = self.winfo_x() + event.x - self._drag_start_x
            y = self.winfo_y() + event.y - self._drag_start_y
            self.geometry(f"+{x}+{y}")

        self.bind("<Button-1>", on_press)
        self.bind("<B1-Motion>", on_drag)

    def _create_widgets(self):
        frame = ttk.Frame(self, padding=10)
        frame.pack()

        ttk.Button(frame, text=T['btn_block'], command=self._block_adobe).pack(fill="x", pady=5)
        ttk.Button(frame, text=T['btn_unblock'], command=self._unblock_adobe).pack(fill="x", pady=5)

    def _block_adobe(self):
        executables = self._find_executables()
        if not executables:
            messagebox.showinfo(T['block_title'], T['info_no_exes'])
            self._exit_app()
            return

        self._start_progress_window(
            title=T['block_title'],
            items=executables,
            worker=self._perform_block
        )

    def _unblock_adobe(self):
        rules = self.firewall.list_rules(prefix="Block Adobe:")
        total = len(rules)
        if total == 0:
            messagebox.showinfo(T['unblock_title'], T['info_no_rules'])
            self._exit_app()
            return

        if not messagebox.askokcancel(
            T['unblock_title'], T['confirm_unblock'].format(count=total)
        ):
            return

        self._start_progress_window(
            title=T['unblock_title'],
            items=rules,
            worker=self._perform_unblock
        )

    def _start_progress_window(self, title, items, worker):
        self.withdraw()
        self.progress_window = tk.Toplevel(self)
        self.progress_window.title(title)

        self.progress = ttk.Progressbar(
            self.progress_window,
            orient='horizontal',
            length=300,
            mode='determinate',
            maximum=len(items)
        )
        self.progress.pack(padx=20, pady=20)

        threading.Thread(target=worker, args=(items,), daemon=True).start()

    def _perform_block(self, executables):
        for idx, exe in enumerate(executables, start=1):
            name = f"Block Adobe: {exe}"
            self.firewall.delete_rule(name)
            try:
                self.firewall.add_rule(
                    name=name,
                    program=str(exe),
                    description="Block Adobe from network"
                )
            except RuntimeError as e:
                self._show_error_and_exit(T['error_block'].format(item=exe, error=e))
                return
            self._update_progress(idx)
        self._finish(T['done_message'])

    def _perform_unblock(self, rules):
        for idx, name in enumerate(rules, start=1):
            try:
                self.firewall.delete_rule(name)
            except RuntimeError as e:
                self._show_error_and_exit(T['error_unblock'].format(item=name, error=e))
                return
            self._update_progress(idx)
        self._finish(T['done_message'])

    def _find_executables(self):
        base_dirs = [
            Path(os.environ.get("ProgramFiles(x86)", "")) / "Adobe",
            Path(os.environ.get("ProgramFiles", "")) / "Adobe",
            Path(os.environ.get("CommonProgramFiles(x86)", "")) / "Adobe",
            Path(os.environ.get("CommonProgramFiles", "")) / "Adobe",
        ]
        exes = []
        for base in base_dirs:
            if base.exists():
                exes.extend(base.rglob("*.exe"))
        return exes

    def _update_progress(self, value):
        self.progress_window.after(0, lambda v=value: self.progress.config(value=v))

    def _finish(self, message):
        def done():
            messagebox.showinfo(T['done_title'], message)
            self._exit_app()
        self.progress_window.after(0, done)

    def _show_error_and_exit(self, msg):
        def show():
            messagebox.showerror(T['error_title'], msg)
            self._exit_app()
        self.progress_window.after(0, show)

    def _exit_app(self):
        self.destroy()
        sys.exit(0)

if __name__ == "__main__":
    app = AdobeBlockerApp()
    app.mainloop()
