from nox import session, parametrize
from os import environ

CI = bool(environ.get("CI"))
E = ("-e", "")[CI]
PIP = tuple()


@session(reuse_venv=True)
@parametrize("env", ["py", "ipy"])
def test(session, env):
    e = [E + ".[test]"]
    if env == "ipy":
        e.extend(["nbconvert", "ipython"])
    session.install(*e, *PIP)
    session.run("pytest", "tests", *session.posargs)
    if not session.posargs:
        session.run("pytest", "tests/test_cli.ipynb", "--nbval")
