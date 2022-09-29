from platform import python_implementation
from nox import session, parametrize
from os import environ

CI = bool(environ.get("CI"))
E = ("-e", "")[CI]
PIP = tuple()
PYPY = python_implementation() == "PyPy"

sessions = ["py"]
if not PYPY:
    sessions += ["ipy"]


@session(reuse_venv=True)
@parametrize("env", sessions)
def test(session, env):
    e = [E + ".[test]"]
    if env == "ipy":
        e.extend(["nbconvert", "ipython"])
    session.install(*e, *PIP)
    session.run("pytest", "tests", *session.posargs)
    