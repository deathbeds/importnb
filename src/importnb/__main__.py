from . import Notebook


def main(argv=None):
    """A convenience function for running importnb as an application"""
    Notebook.load_argv(argv)


if __name__ == "__main__":
    main()
