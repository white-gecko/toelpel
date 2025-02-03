from git_watchtower.store import WatchStore, discover_index
from pathlib import Path
import os
from shutil import copyfile

test_directory = Path(os.path.dirname(__file__))


def test_discover_index_rootdir_exists(tmp_path):
    p = tmp_path / "workspaces.ttl"
    copyfile(test_directory / "assets" / "example_index.ttl", p)
    index = discover_index(tmp_path)

    assert index == p


def test_discover_index_rootdir_missing(tmp_path):
    p = tmp_path / "workspaces.ttl"

    index = discover_index(tmp_path)

    assert index == None


def test_watch_store(tmp_path):
    p = tmp_path / "workspaces.ttl"
    copyfile(test_directory / "assets" / "example_index.ttl", p)
    ws = WatchStore(index=p, base=tmp_path)
    lst = ws.graph_to_list()
    assert len(list(lst)) == 1
