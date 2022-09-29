def rm_pytester_prefix(out):
    return "".join(out.splitlines(True)[2:])

def test_usage(capsys, pytester):
    """\
usage: a command line interface for executing notebooks as scripts.

positional arguments:
  {install,uninstall,run}
    install             install the importnb extension
    uninstall           uninstall the importnb extension
    run                 run files and modules as scripts

optional arguments:
  -h, --help            show this help message and exit
"""
    pytester.run("importnb")
    cap = capsys.readouterr()
    out, err = cap.out, cap.err
    out = rm_pytester_prefix(out)
    assert  out == test_usage.__doc__