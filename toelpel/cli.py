import json
from os import walk
from pathlib import Path
from shutil import copyfile
from subprocess import DEVNULL, run
from sys import stderr

import click
from loguru import logger

from .colony import Colony, find_index
from .git import git
from .output import print_table


@click.group()
def cli():
    """Tölpel

    Get an overview on your git repositories and manage them from one place.
    """
    loglevel = "DEBUG"
    logfile = None
    logfilelevel = "DEBUG"
    logger.remove()
    logger.add(stderr, level=loglevel)
    if logfile:
        logger.add(logfile, level=logfilelevel)


def locate_root_and_index(rootdir: Path | None = None, index: Path | None = None, working_dir: Path | None = None):
    if isinstance(rootdir, str):
        rootdir = Path(rootdir)
    if isinstance(index, str):
        index = Path(index)
    if isinstance(working_dir, str):
        working_dir = Path(working_dir)
    if index is None:
        index = find_index(rootdir, working_dir)
    if rootdir is None:
        rootdir = index.parent
    logger.debug(f"index: {index}")
    logger.debug(f"rootdir: {rootdir}")
    return rootdir, index


@cli.command()
@click.argument("working_dir", type=click.Path(exists=True))
@click.option("-r", "--rootdir", type=click.Path(exists=True))
@click.option("-i", "--index", type=click.Path(exists=False))
@click.option("-d", "--discover", flag_value=True)
def scan(working_dir, rootdir, index, discover):
    """Scan the repositories in an index and update the index."""

    rootdir, index = locate_root_and_index(rootdir, index, working_dir)

    store = Colony(index, rootdir)
    if discover:
        logger.info("Start discover")
        git_repos = []
        for subdir, dirs, files in walk(rootdir, topdown=True):
            subdir_path = Path(subdir)
            for dir in dirs.copy():
                dir_path = Path(dir)
                relative_path = subdir_path / dir_path
                result = run(["git", "-C", relative_path, "rev-parse"], stderr=DEVNULL)
                logger.debug(
                    f"path: {subdir_path / dir_path}, result: {result.returncode}"
                )
                repo = git(subdir_path / dir_path)
                if repo.is_repo:
                    git_repos.append(repo)
                    # prevent walk from further descending into this directory
                    dirs.remove(dir)
                    logger.debug("DEL")
    else:
        git_repos = store.to_list()
    store.update_from_list(git_repos)


@cli.command("list")
@click.argument("working_dir", type=click.Path(exists=False), default=None)
@click.option(
    "-r", "--rootdir", default=None, type=click.Path(exists=True, path_type=Path)
)
@click.option("-i", "--index", type=click.Path(exists=False))
@click.option("-f", "--format", default="console")
def list_repos(working_dir, rootdir, index, format):
    """List all repositories in an index with their respective status.

    format is "console" per default, but could also be "plain" or "json" or things like
    that.
    """

    rootdir, index = locate_root_and_index(rootdir, index, working_dir)

    store = Colony(index, rootdir)

    if format == "console":
        print_table(store.to_list())
    elif format == "json":
        print(json.dumps(list(store.to_list(plain=True))))


def complete_repository(ctx, param, incomplete):
    index = find_index()
    store = Colony(index, index.parent)

    current_list = [
        k.path.relative_to(Path.cwd())
        for k in store.to_list()
        if k.path.is_relative_to(Path.cwd())
    ]
    return [str(k) for k in current_list if str(k).startswith(incomplete)]


@cli.command()
@click.argument(
    "repository",
    required=False,
    shell_complete=complete_repository,
)
@click.option("--all", is_flag=True, default=False, help="Clone all repositories")
@click.option(
    "-w", "--workingdir", "working_dir", default=None, type=click.Path(exists=True, path_type=Path)
)
@click.option(
    "-r", "--rootdir", default=None, type=click.Path(exists=True, path_type=Path)
)
@click.option(
    "-i", "--index", default=None, type=click.Path(exists=True, path_type=Path)
)
def clone(working_dir, rootdir, index, all, repository):
    """Clone repositories from an index.
    If the optional argument REPOSITORY is given as a relative path only this explicity
    repository is cloned.
    If rootdir is given, they are cloned relative to the given root directory."""

    logger.debug(f"repository: {repository}")

    if not all and repository is None:
        logger.error(
            "You need to specify a repository or explicitely set --all if you really "
            "want to initialize all repositories."
        )
        return False

    rootdir, index = locate_root_and_index(rootdir, index, working_dir)

    if index.parent != rootdir:
        copyfile(index, rootdir / "workspace.ttl")
        index = rootdir / "workspace.ttl"

    store = Colony(index, rootdir)
    git_repos = store.to_list()

    if repository is not None:
        repository_path = Path.cwd() / repository
        git_repos = [repo for repo in git_repos if repo.path == repository_path]

    for repo in git_repos:
        logger.debug(f"Cloning {repo} at {repo.path} …")
        repo.path.mkdir(parents=True, exist_ok=True)
        repo.remotes = store.get_remotes(repo)
        repo.clone()
        repo.setup()


if __name__ == "__main__":
    cli(obj={})
