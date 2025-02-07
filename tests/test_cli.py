from git_watchtower.cli import cli
from git_watchtower.store import WatchStore, discover_index
from click.testing import CliRunner
from pathlib import Path
import os
from shutil import copyfile
from subprocess import DEVNULL, run
from rdflib import Graph

test_directory = Path(os.path.dirname(__file__))


def test_index(tmp_path):
    """Test for a directory with git repositories, if an index is correctly created."""
    repo_a_path = tmp_path / "repo_a"
    repo_b_path = tmp_path / "repo_b"
    index = tmp_path / "workspace.ttl"
    remote_b = "https://example.org/repo_a.git"

    run(["git", "init", repo_a_path], stderr=DEVNULL)
    run(["git", "init", repo_b_path], stderr=DEVNULL)
    run(["git", "-C", repo_b_path, "remote", "add", "origin", remote_b], stderr=DEVNULL)

    runner = CliRunner()
    result = runner.invoke(cli, ["index", str(tmp_path), "--index", str(index)])
    print(result.stdout)
    assert result.exit_code == 0
    assert index.is_file()

    g = Graph().parse(format='turtle', source=index)
    assert g.query("""
        PREFIX gw: <https://git-watch/>

        ask {
            ?repo a gw:repo .
        }
        """)
    assert g.query("""
        PREFIX gw: <https://git-watch/>

        ask {
            ?repo a gw:repo ;
                gw:remote ?remote .
            ?remote gw:push ?url .
        }
        """)
    assert g.query("""
        PREFIX gw: <https://git-watch/>

        ask {
            ?repo a gw:repo ;
                gw:remote ?remote .
            ?remote gw:push <""" + remote_b + """> .
        }
        """)
    assert g.query("""
        PREFIX gw: <https://git-watch/>

        ask {
            <urn:relpath:repo_a> a gw:repo .
            <urn:relpath:repo_b> a gw:repo .
        }
        """)
