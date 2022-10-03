from . import Notebook


def main(argv=None):
    """a convenience function for running importnb as an application"""

    Notebook.load_argv(argv)
    return


if __name__ == "__main__":
    main()
