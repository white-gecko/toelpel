import os
from pathlib import Path
from shutil import copyfile

from toelpel.store import WatchStore, find_index

test_path = Path(os.path.dirname(__file__))
examples_path = test_path / "assets" / "examples"


def test_find_index_rootdir_exists(tmp_path):
    p = tmp_path / "workspaces.ttl"
    copyfile(examples_path / "index_online.ttl", p)
    index = find_index(tmp_path)

    assert index == p


def test_find_index_rootdir_missing(tmp_path):
    p = tmp_path / "workspaces.ttl"

    index = find_index(tmp_path)

    assert index is None


def test_watch_store(tmp_path):
    p = tmp_path / "workspaces.ttl"
    copyfile(examples_path / "index_online.ttl", p)
    ws = WatchStore(index=p, base=tmp_path)
    lst = ws.graph_to_list()
    assert len(list(lst)) == 1
