"""Which models this machine uses, and where its other programs live. The choices live in `models.local.json`
beside the code, which is never tracked; the code itself names no model, no model's code and no folder of this
machine. Copy `models.example.json` to `models.local.json` and fill it in.
An environment variable MINDSTREAM_<KEY> (upper case) overrides the file.

Licence: vid_gen.py, which is under the GNU General Public License, uses this file; so this file may be used under
either that licence (version 3 or later) or the repository's own (LICENSE)."""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, "models.local.json")


def _load():
    try:
        with open(PATH, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


_CHOICES = _load()


def pick(key, default="", env=None):
    """The value chosen for `key` on this machine ('' if none): a file name, a path, a model tag or a code name.
    `env` names an older environment variable that is still honoured as well as MINDSTREAM_<KEY>."""
    value = (os.environ.get("MINDSTREAM_" + key.upper()) or (os.environ.get(env) if env else "")
             or _CHOICES.get(key) or default)
    return os.path.expandvars(os.path.expanduser(str(value))) if value else ""


def need(key, what, env=None):
    """Like pick, but stops with a plain message when nothing has been chosen."""
    value = pick(key, env=env)
    if not value:
        raise SystemExit(f"no {what} chosen: set \"{key}\" in {PATH} (see models.example.json)")
    return value


def _venv_python(folder):
    return os.path.join(folder, "venv", "Scripts", "python.exe") if folder else ""


def forge_python():
    """The Python of the Forge environment the picture generator runs in ('' if none chosen): "forge_python", or
    the venv inside "forge_dir". MINDSTREAM_PYTHON, the older name, still works."""
    return pick("forge_python", env="MINDSTREAM_PYTHON") or _venv_python(pick("forge_dir", env="MINDSTREAM_FORGE"))


def comfy_python():
    """The Python of the ComfyUI environment the film generator runs in ('' if none chosen): "comfy_python"
    (MINDSTREAM_COMFY_PYTHON), or the venv inside "comfy_dir"."""
    return pick("comfy_python") or _venv_python(pick("comfy_dir", env="MINDSTREAM_COMFY"))


def code(key, what):
    """A class, function or module that the chosen model needs, named in models.local.json rather than here:
    "package.module:Name" for something inside a module, or "package.module" for the module itself.
    Imported when asked for; stops with a plain message when nothing is chosen or the name cannot be found."""
    import importlib
    name = need(key, what)
    module, _, attr = name.partition(":")
    try:
        found = importlib.import_module(module)
        return getattr(found, attr) if attr else found
    except (ImportError, AttributeError) as e:
        raise SystemExit(f"the {what} named by \"{key}\" in {PATH} ({name}) cannot be loaded here: {e}") from None


if __name__ == "__main__":
    # for the launchers: `python local.py forge_python` prints the chosen value (nothing if none)
    import sys
    for key in sys.argv[1:]:
        value = {"forge_python": forge_python, "comfy_python": comfy_python}.get(key, lambda: pick(key))()
        if value:
            print(value)
