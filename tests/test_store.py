from git_watchtower.store import WatchStore, discover_index

CONTENT = """
@prefix gwa: <https://git-watch/> .

<urn:relpath:space/simpsons> a gwa:repo ;
    gwa:remote <urn:relpath:space/simpsons#remote:origin> .

<urn:relpath:space/simpsons#remote:origin> gwa:push <git@github.com:white-gecko/simpsons.git> .
"""


def test_discover_index_rootdir_exists(tmp_path):
    p = tmp_path / "workspaces.ttl"
    p.write_text(CONTENT, encoding="utf-8")

    index = discover_index(tmp_path)

    assert index == p


def test_discover_index_rootdir_missing(tmp_path):
    p = tmp_path / "workspaces.ttl"

    index = discover_index(tmp_path)

    assert index == None


def test_watch_store(tmp_path):
    p = tmp_path / "workspaces.ttl"
    p.write_text(CONTENT, encoding="utf-8")
    ws = WatchStore(index=p, base=tmp_path)
    lst = ws.graph_to_list()
    assert len(list(lst)) == 1
