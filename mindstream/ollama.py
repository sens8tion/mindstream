"""Ollama on llama, reached through an SSH tunnel. Standard library only; writes nothing to disk.

The tunnel carries only API traffic (no remote shell). On close, models used are unloaded and
the Ollama service is restarted so the conversation does not linger in its memory.
"""
import json
import socket
import subprocess
import time
import urllib.error
import urllib.request


class ApiError(Exception):
    pass


class Ollama:
    def __init__(self, host="llama", log=None):
        self.host = host
        self.log = log or (lambda msg: None)
        self.used = set()
        with socket.socket() as s:
            s.bind(("127.0.0.1", 0))
            self.port = s.getsockname()[1]
        self.base = f"http://127.0.0.1:{self.port}"
        self.tunnel = None
        self.connect()

    def connect(self):
        self.tunnel = subprocess.Popen(
            ["ssh", "-N", "-o", "BatchMode=yes", "-o", "ExitOnForwardFailure=yes", "-o", "ServerAliveInterval=30",
             "-L", f"{self.port}:127.0.0.1:11434", self.host], stdin=subprocess.DEVNULL)
        deadline = time.time() + 20
        while time.time() < deadline:
            if self.tunnel.poll() is not None:
                raise ApiError(f"ssh tunnel to {self.host} failed (exit {self.tunnel.returncode})")
            try:
                socket.create_connection(("127.0.0.1", self.port), timeout=1).close()
                return
            except OSError:
                time.sleep(0.3)
        self.tunnel.terminate()
        raise ApiError(f"ssh tunnel to {self.host} did not come up")

    def request(self, path, body=None, method=None, timeout=600):
        if self.tunnel.poll() is not None:
            self.log("connection to llama had dropped - reconnecting")
            self.connect()
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(self.base + path, data=data, method=method,
                                     headers={"Content-Type": "application/json"})
        try:
            return urllib.request.urlopen(req, timeout=timeout)
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", "replace")
            try:
                detail = json.loads(detail).get("error", detail)
            except ValueError:
                pass
            raise ApiError(detail or f"HTTP {e.code}") from None
        except OSError as e:
            raise ApiError(str(e)) from None

    def capabilities(self, model):
        with self.request("/api/show", {"model": model}) as r:
            return set(json.load(r).get("capabilities", []))

    def chat(self, model, messages, think=None, options=None, on_text=None):
        """One reply, streamed. Returns the full text; on_text(piece) is called as it arrives."""
        body = {"model": model, "messages": messages, "stream": True}
        if think is not None:
            body["think"] = think
        if options:
            body["options"] = options
        self.used.add(model)
        parts = []
        self.last = {"thinking": 0}     # how the reply ended, for explaining an empty one (counts only, no text)
        with self.request("/api/chat", body) as resp:
            for raw in resp:
                chunk = json.loads(raw)
                if "error" in chunk:
                    raise ApiError(chunk["error"])
                self.last["thinking"] += len(chunk.get("message", {}).get("thinking") or "")
                if chunk.get("done"):
                    self.last.update(reason=chunk.get("done_reason"), tokens=chunk.get("eval_count"))
                piece = chunk.get("message", {}).get("content", "")
                if piece:
                    parts.append(piece)
                    if on_text:
                        on_text(piece)
        return "".join(parts).strip()

    def clear(self, what="all"):
        """Remove what a session leaves on the remote host. "all": restart Ollama, whose memory holds the last
        story, and empty the system log (kept in RAM there), which records when the host was used. "log": the
        log only. Uses the host's own narrow command if it has one, else only restarts Ollama. True if it worked."""
        for command in (f"sudo -n /usr/local/sbin/mindstream-clear {what}",
                        "sudo -n /usr/bin/systemctl restart ollama.service" if what == "all" else None):
            if command is None:
                continue
            try:
                r = subprocess.run(["ssh", "-o", "BatchMode=yes", self.host, command],
                                   stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=90)
            except (OSError, subprocess.TimeoutExpired):
                continue
            if r.returncode == 0:
                return True
        return False

    def close(self, keep_loaded=False, restart=True):
        """Unload what we used, restart Ollama to clear its memory (unless another session is active)."""
        try:
            if not keep_loaded:
                for model in list(self.used):
                    try:
                        self.request("/api/generate", {"model": model, "keep_alive": 0}, timeout=30).close()
                    except ApiError:
                        pass
                if restart and self.used:
                    try:
                        with self.request("/api/ps", timeout=10) as r:
                            others = [m["name"] for m in json.load(r).get("models", [])]
                    except ApiError:
                        others = []
                    if others:
                        self.log(f"another session has {', '.join(others)} loaded - Ollama not restarted")
                    else:
                        self.log("Ollama restarted on llama and its log emptied - nothing of the story is left there"
                                 if self.clear("all") else "could not clear llama (see the README, Remote host)")
        finally:
            self.tunnel.terminate()
            try:
                self.tunnel.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.tunnel.kill()
