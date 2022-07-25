from nox import session
from os import environ

CI = bool(environ.get("CI"))
E = ("-e", "")[CI]


@session(reuse_venv=True)
def test_ipython(session):
    session.install("nbconvert", "ipython", E + ".[test]")
    session.run("pytest", "tests", *session.posargs)


@session(reuse_venv=True)
def test_python(session):
    session.install(E + ".[test]")
    session.run("pytest", "tests", *session.posargs)
