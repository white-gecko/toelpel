import os
from pathlib import Path
from shutil import copyfile, copytree
from subprocess import DEVNULL, run
from textwrap import dedent

from click.testing import CliRunner
from loguru import logger
from query_collection import TemplateQueryCollection
from rdflib import Graph, URIRef

from toelpel.cli import cli

test_path = Path(os.path.dirname(__file__))
examples_path = test_path / "assets" / "examples"


def git(repo_path, *args):
    """Run a git command.
    Set the repo_path to None, since the directory does not exist already.
    """
    cmd = ["git"]
    if repo_path:
        cmd += ["-C", repo_path]
    cmd += ["-c", 'user.name="Your Name"', "-c", 'user.email="you@example.com"', *args]
    logger.debug(cmd)
    return run(cmd, stderr=DEVNULL)


def init_repo_with_dir(repo_path, source_dir=None):
    """Initialize a repository with the contents of a given diectory."""
    git(None, "init", repo_path)
    copytree(source_dir, repo_path, dirs_exist_ok=True)
    git(repo_path, "add", ".")
    git(repo_path, "commit", "-m", "init")


def test_index(tmp_path):
    """Test for a directory with git repositories, if an index is correctly created."""
    # prepare paths
    repo_a_path = tmp_path / "repo_a"
    repo_b_path = tmp_path / "repo_b"
    index = tmp_path / "workspace.ttl"
    remote_b = "https://example.org/repo_a.git"

    # prepare queries
    tqc = TemplateQueryCollection()
    tqc.loadFromDirectory("tests/assets/queries")

    # init repos
    git(None, "init", repo_a_path)
    git(None, "init", repo_b_path)
    git(repo_b_path, "remote", "add", "origin", remote_b)

    # execute index command
    runner = CliRunner()
    result = runner.invoke(cli, ["index", str(tmp_path), "--index", str(index)])
    print(result.stdout)
    assert result.exit_code == 0
    assert index.is_file()

    g = Graph().parse(format="turtle", source=index)
    assert g.query(**tqc.get("index_repos_exist").p())
    assert g.query(**tqc.get("index_repos_have_remote").p())
    assert g.query(**tqc.get("index_verify_repo_remote").p(remote_b=URIRef(remote_b)))
    assert g.query(**tqc.get("index_repo_a_and_b_exist").p())


def test_clone(tmp_path):
    """Given an index and a target root directory, test that all repositories from the
    index are correctly created and cloned."""
    # prepare paths
    remotes_path = tmp_path / "remotes"
    simpsons_path = remotes_path / "simpsons"
    workspace = tmp_path / "workspace"
    index = workspace / "workspace.ttl"

    # init remote repository
    init_repo_with_dir(simpsons_path, examples_path / "repo_content")

    # init empty workspace, with just an index
    workspace.mkdir()
    # TODO inject git_repo.uri as remote into the index
    copyfile(examples_path / "index_local.ttl", index)

    # execute clone command
    runner = CliRunner()
    result = runner.invoke(cli, ["clone", "--all", "--index", str(index)])

    # verify the results
    assert result.exit_code == 0
    assert (workspace / "space" / "simpsons").is_dir()
    assert (workspace / "space" / "simpsons" / ".git").is_dir()
    assert (workspace / "space" / "simpsons" / "README.md").is_file()


def test_clone_fixture(tmp_path, git_repo):
    """Given an index and a target root directory, test that all repositories from the
    index are correctly created and cloned."""

    path = git_repo.workspace
    file = path / "README.md"
    file.write_text("hello world!")
    git_repo.run("git add README.md")
    git_repo.api.index.commit("Initial commit")

    workspace = tmp_path / "workspace"
    index = workspace / "workspace.ttl"

    workspace.mkdir()
    logger.debug(index)
    # TODO inject git_repo.uri as remote into the index

    with open(index, mode="w") as index_file:
        index_file.write(
            dedent(f"""
            @prefix toel: <https://toelpel/> .

            <urn:relpath:space/simpsons> a toel:repo ;
                toel:remote <urn:relpath:space/simpsons#remote:origin> .

            <urn:relpath:space/simpsons#remote:origin> toel:push <path:{git_repo.uri}> .
            """)
        )

    # execute clone command
    runner = CliRunner()
    result = runner.invoke(cli, ["clone", "--all", "--index", str(index)])
    print(result.stdout)

    # verify the results
    assert result.exit_code == 0
    assert (workspace / "space" / "simpsons").is_dir()
    assert (workspace / "space" / "simpsons" / ".git").is_dir()
    assert (workspace / "space" / "simpsons" / "README.md").is_file()
