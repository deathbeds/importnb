from nox import session


@session(reuse_venv=True)
def test_ipython(session):
    session.install("nbconvert", "ipython", "-e.[test]")
    session.run("pytest", "tests", *session.posargs)


@session(reuse_venv=True)
def test_python(session):
    session.install("-e.[test]")
    session.run("pytest", "tests", *session.posargs)
