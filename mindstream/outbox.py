"""Lines to another process, written by a thread of their own, so that whoever sends them never waits.

The parts of mindstream are separate processes joined by pipes: the launcher, the viewer, the two panels, the story
feed. A pipe holds only a few thousand bytes. Written to directly, a pipe whose reader is busy fills, and the writer
stops dead until it drains; the writer is then not reading its own pipes, so those fill in turn, and one slow part
freezes all the others. An Outbox breaks that chain: `put` only queues the line and returns at once, and a thread
of the outbox's own does the writing, waiting on the pipe so that no one else has to.

How things stand is sent again and again ("state" twice a second). Lines given a `latest` key replace an unsent
line with the same key, so a reader that falls behind gets the newest, not a backlog. If the queue still grows past
`most` (a reader that has stopped altogether), the oldest lines are let go.

Nothing here needs anything but the standard library.
"""
import collections
import threading


class Outbox:
    def __init__(self, write, flush=None, close=None, most=400, name="outbox"):
        self.write, self.flush, self.closer, self.most = write, flush, close, most
        self.lines, self.ready, self.dropped, self.alive = collections.deque(), threading.Condition(), 0, True
        threading.Thread(target=self.run, name=name, daemon=True).start()

    def put(self, data, latest=None):
        """Queue `data` to be written. With `latest`, an unsent line put with the same key is replaced by this one."""
        with self.ready:
            if not self.alive:
                return False
            if latest is not None:
                for at, (key, _) in enumerate(self.lines):
                    if key == latest:
                        del self.lines[at]
                        break
            self.lines.append((latest, data))
            while len(self.lines) > self.most:             # a reader that has stopped: the oldest go
                self.lines.popleft()
                self.dropped += 1
            self.ready.notify()
        return True

    def close(self):
        """Write what is queued, then close the pipe."""
        with self.ready:
            self.lines.append(("close", None))
            self.ready.notify()

    def run(self):
        while True:
            with self.ready:
                while not self.lines:
                    self.ready.wait()
                key, data = self.lines.popleft()
            try:
                if key == "close" and data is None:
                    if self.closer is not None:
                        self.closer()
                    break
                self.write(data)
                if self.flush is not None:
                    self.flush()
            except (OSError, ValueError, AttributeError):  # the other end has gone: nothing more can be written
                break
        with self.ready:
            self.alive = False
            self.lines.clear()
