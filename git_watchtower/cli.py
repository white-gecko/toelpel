import click
from sys import stderr
from os import walk
from subprocess import run, DEVNULL
from pathlib import Path
from loguru import logger
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
    """Scan the repositories in an index and update the index"""

    store = WatchStore(index, rootdir)
    git_repos = store.graph_to_list()
    store.list_to_graph(git_repos)

@cli.command()
@click.argument("rootdir", type=click.Path(exists=True))
@click.option("-i", "--index", type=click.File("r"))
def list(rootdir, index):

    store = WatchStore(index, rootdir)
    git_repos = store.graph_to_list()

    # git_repos = yaml.safe_load(index)
    # git_repos = []
    logger.debug(git_repos)
    for repo in git_repos:
        status = []
        status_count = 0
        if not repo.isRepo:
            click.echo("not a repo\t" + click.style(f"{repo}", bold=True))
            continue
        if repo.dirty:
            status_count += 1
            status.append(click.style("?", fg='blue', bold=True))
        else:
            status.append("-")
        if repo.ignorred_dirt:
            status_count += 1
            status.append(click.style("?", fg='bright_black', bold=True))
        else:
            status.append("-")
        if repo.stashes:
            status_count += 1
            status.append(click.style("*", fg='yellow', bold=True))
        else:
            status.append("-")
        if not repo.remotes:
            status_count += 1
            status.append(click.style("no remote", fg='red', bold=True))
        elif repo.local_branches:
            status_count += 1
            status.append(click.style("local branches", fg='red', bold=True))
        for branch, remote in repo.branches.items():
            if remote:
                behind = repo.behind(branch)
                ahead = repo.ahead(branch)
                status_count += 1 if (behind or ahead) else 0
                div = ""
                if (behind or ahead):
                    div = f": -{behind}/+{ahead}"
                status.append(click.style(f"[{branch}" + div + "]", fg="red" if div else "green"))
            else:
                # branch has no remote
                status_count += 1
                status.append(click.style(f"[{branch}: ×]", fg='red', bold=True))

        click.echo(" ".join(status) + "\t" + click.style(f"{repo}", bold=True if status_count else False))

@cli.command()
@click.argument("rootdir", type=click.Path(exists=True))
@click.option("-i", "--index", type=click.File("r"))
def clone(rootdir, index):

    store = WatchStore(index, rootdir)
    git_repos = store.graph_to_list()

    logger.debug(git_repos)
    for repo in git_repos:
        repo.path.mkdir(parents=True, exist_ok=True)
        repo.clone()
        repo.setup()


if __name__ == "__main__":
    cli(obj={})
