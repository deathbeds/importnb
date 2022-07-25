def task_gen_parser():
    """generate the standlone pidgy json parser"""
    return dict(
        actions=["python -m lark.tools.standalone --propagate_positions src/nb.g > src/importnb/_json_parser.py"],
        file_dep=["dodo.py", "src/nb.g"],
        targets=["src/importnb/_json_parser.py"]
    )