from toelpel.cli import cli
from toelpel.store import WatchStore, discover_index
from click.testing import CliRunner
from pathlib import Path
import os
from shutil import copyfile, copytree

from subprocess import DEVNULL, run
from rdflib import Graph

test_path = Path(os.path.dirname(__file__))
examples_path = test_path / "assets" / "examples"


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

    g = Graph().parse(format="turtle", source=index)
    assert g.query(
        """
        PREFIX toel: <https://toelpel/>

        ask {
            ?repo a toel:repo .
        }
        """
    )
    assert g.query(
        """
        PREFIX toel: <https://toelpel/>

        ask {
            ?repo a toel:repo ;
                toel:remote ?remote .
            ?remote toel:push ?url .
        }
        """
    )
    assert g.query(
        """
        PREFIX toel: <https://toelpel/>

        ask {
            ?repo a toel:repo ;
                toel:remote ?remote .
            ?remote toel:push <"""
        + remote_b
        + """> .
        }
        """
    )
    assert g.query(
        """
        PREFIX toel: <https://toelpel/>

        ask {
            <urn:relpath:repo_a> a toel:repo .
            <urn:relpath:repo_b> a toel:repo .
        }
        """
    )


def test_clone(tmp_path):
    """Test for an index and a given target root directory that all repositories from the index are correctly created and cloned."""
    remotes_path = tmp_path / "remotes"
    simpsons_path = remotes_path / "simpsons"
    workspace = tmp_path / "workspace"
    index = workspace / "workspace.ttl"

    workspace.mkdir()
    run(["git", "init", simpsons_path], stderr=DEVNULL)
    copytree(examples_path / "repo_content", simpsons_path, dirs_exist_ok=True)
    copyfile(examples_path / "index_local.ttl", index)

    runner = CliRunner()
    result = runner.invoke(cli, ["clone", "--all", "--index", str(index)])
    print(result.stdout)

    assert result.exit_code == 0
    assert (workspace / "space" / "simpsons").is_dir()
    assert (workspace / "space" / "simpsons" / ".git").is_dir()
    assert (workspace / "space" / "simpsons" / "README.md").is_file()
