import click
from sys import stderr
from os import walk
from subprocess import run, DEVNULL
from pathlib import Path
from loguru import logger
from rich.console import Console
from rich.table import Table
from .git import git
from .store import WatchStore

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

@cli.command()
@click.argument("rootdir", type=click.Path(exists=True))
@click.option("-i", "--index", type=click.File("r"))
def list(rootdir, index):
    """List all repositories in an index with their respective status."""

    console = Console()
    table = Table(show_header=True, header_style="bold")

    store = WatchStore(index, rootdir)
    git_repos = store.graph_to_list()

    table.add_column("Status")
    table.add_column("Branches")
    table.add_column("Repository")

    for repo in git_repos:
        status = []
        branches = []
        status_count = 0
        if not repo.isRepo:
            table.add_row(
                "[bold]not a repo[/bold]", "", f"[bold]{repo}[/bold]"
            )
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
                if (behind or ahead):
                    div = f": -{behind}/+{ahead}"
                fg = "red" if div else "green"
                branches.append(f"[{fg}]\\[{branch}" + div + f"][/{fg}]")
            else:
                # branch has no remote
                status_count += 1
                branches.append(f"[bold red]\\[{branch}: ×][/bold red]")

        repo_line = f"[bold]{repo}[/bold]" if status_count else f"{repo}"
        table.add_row(
            " ".join(status), " ".join(branches), repo_line
        )
    console.print(table)

@cli.command()
@click.argument("rootdir", type=click.Path(exists=True))
@click.option("-i", "--index", type=click.File("r"))
def clone(rootdir, index):
    """Clone all repositories from an index relative to the given root directory."""

    store = WatchStore(index, rootdir)
    git_repos = store.graph_to_list()

    logger.debug(git_repos)
    for repo in git_repos:
        repo.path.mkdir(parents=True, exist_ok=True)
        repo.clone()
        repo.setup()


if __name__ == "__main__":
    cli(obj={})
