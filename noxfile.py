from nox import session, parametrize
from os import environ

CI = bool(environ.get("CI"))
E = ("-e", "")[CI]


@session(reuse_venv=True)
@parametrize("env", ["py", "ipy"])
def test(session, env):
    e = [E + ".[test]"]
    if env == "ipy":
        e.extend(["nbconvert", "ipython"])
    session.install(*e)
    session.run("pytest", "tests", *session.posargs)
