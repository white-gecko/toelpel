from os import walk
from pathlib import Path
from subprocess import DEVNULL, run
from sys import stderr

import click
from loguru import logger
from rich.console import Console
from rich.table import Table

from .git import git
from .store import WatchStore, discover_index


@click.group()
def cli():
    """Git🗼Watchtower

    Get an overview on your git repositories and manage them from one place.
    """
    loglevel = "DEBUG"
    logfile = None
    logfilelevel = "DEBUG"
    logger.remove()
    logger.add(stderr, level=loglevel)
    if logfile:
        logger.add(logfile, level=logfilelevel)


@cli.command()
@click.argument("rootdir", type=click.Path(exists=True))
@click.option("-i", "--index", type=click.File("bw+"))
@click.option("-c", "--cache", type=click.File("bw+"), default=None)
def index(rootdir, index, cache):
    """Scan all sub-directories starting from the rootdir for all git repositories and write the result to the index."""
    git_repos = []
    for subdir, dirs, files in walk(rootdir, topdown=True):
        subdir_path = Path(subdir)
        for dir in dirs.copy():
            dir_path = Path(dir)
            relative_path = subdir_path / dir_path
            result = run(["git", "-C", relative_path, "rev-parse"], stderr=DEVNULL)
            logger.debug(f"path: {subdir_path / dir_path}, result: {result.returncode}")
            repo = git(subdir_path / dir_path)
            if repo.isRepo:
                git_repos.append(repo)
                dirs.remove(dir)
                logger.debug("DEL")

    store = WatchStore(index, rootdir)
    store.list_to_graph(git_repos)


@cli.command()
@click.argument("rootdir", type=click.Path(exists=True))
@click.option("-i", "--index", type=click.File("br+"))
def scan(rootdir, index):
    """Scan the repositories in an index and update the index."""

    store = WatchStore(index, rootdir)
    git_repos = store.graph_to_list()
    store.list_to_graph(git_repos)


@cli.command("list")
@click.argument("rootdir", type=click.Path(exists=True))
@click.option("-i", "--index", type=click.File("r"))
def list_repos(rootdir, index):
    """List all repositories in an index with their respective status."""

    console = Console()
    table = Table(show_header=True, header_style="bold")

    store = WatchStore(index, rootdir)
    git_repos = store.graph_to_list()

    table.add_column("Status")
    table.add_column("Repository", ratio=2)
    table.add_column("Branches", ratio=1)

    for repo in git_repos:
        status = []
        branches = []
        status_count = 0
        if not repo.isRepo:
            table.add_row("[bold]not a repo[/bold]", f"[bold]{repo}[/bold]", "")
            continue
        if repo.dirty:
            status_count += 1
            status.append("[bold blue]?[/bold blue]")
        else:
            status.append("-")
        if repo.ignorred_dirt:
            status_count += 1
            status.append("[bold bright_black]?[/bold bright_black]")
        else:
            status.append("-")
        if repo.stashes:
            status_count += 1
            status.append("[bold yellow]*[/bold yellow]")
        else:
            status.append("-")
        if not repo.remotes:
            status_count += 1
            branches.append("[bold red]no remote[/bold red]")
        elif repo.local_branches:
            status_count += 1
            branches.append("[red]local branches[/red]")
        for branch, remote in repo.branches.items():
            if remote:
                behind = repo.behind(branch)
                ahead = repo.ahead(branch)
                status_count += 1 if (behind or ahead) else 0
                div = ""
                if behind or ahead:
                    div = f": -{behind}/+{ahead}"
                fg = "red" if div else "green"
                branches.append(f"[{fg}]\\[{branch}" + div + f"][/{fg}]")
            else:
                # branch has no remote
                status_count += 1
                branches.append(f"[bold red]\\[{branch}: ×][/bold red]")

        repo_line = f"[bold]{repo}[/bold]" if status_count else f"{repo}"
        table.add_row(" ".join(status), repo_line, " ".join(branches))
    console.print(table)


def complete_repository(ctx, param, incomplete):
    index = discover_index()
    store = WatchStore(index, index.parent)

    current_list = [
        k.path.relative_to(Path.cwd())
        for k in store.graph_to_list()
        if k.path.is_relative_to(Path.cwd())
    ]
    return [str(k) for k in current_list if str(k).startswith(incomplete)]


@cli.command()
@click.argument("repository", required=False, shell_complete=complete_repository)
@click.option("--all", default=False, help="Clone all repositories")
@click.option("-r", "--rootdir", default=None, type=click.Path(exists=True))
@click.option("-i", "--index", default=None, type=click.File("r"))
def clone(rootdir, index, all, repository):
    """Clone repositories from an index.
    If rootdir is given, the are cloned relative to the given root directory."""

    logger.debug(f"repository: {repository}")

    if not all and repository is None:
        logger.error(
            "You need to specify a repository or explicitely set --all if you realy want to initialize all repositories."
        )
        return False

    if index is None:
        index = discover_index(rootdir)
    if rootdir is None:
        rootdir = index.parent
    logger.debug(f"index: {index}")
    logger.debug(f"rootdir: {rootdir}")

    store = WatchStore(index, rootdir)
    git_repos = store.graph_to_list()

    repository = Path.cwd() / repository

    git_repos = [repo for repo in git_repos if repo.path == repository]

    for repo in git_repos:
        repo.path.mkdir(parents=True, exist_ok=True)
        repo.remotes = store.get_remotes(repo)
        repo.clone()
        repo.setup()


if __name__ == "__main__":
    cli(obj={})
