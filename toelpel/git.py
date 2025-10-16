from collections import defaultdict
from pathlib import Path
from subprocess import DEVNULL, run

from loguru import logger


class git:
    def __init__(self, repo: Path):
        self.path = repo
        self._remotes = None

    def __repr__(self) -> str:
        return f"<git repo at {self.path}>"

    def __str__(self) -> str:
        return str(self.path)

    @property
    def is_repo(self) -> bool:
        return (
            run(["git", "-C", self.path, "rev-parse"], stderr=DEVNULL).returncode == 0
        )

    @property
    def remotes(self):
        """A dictionary of the configured remotes of the repository.

        In the `git remotes -v` output the structure is e.g.:

        ```
        origin	git@github.com:white-gecko/toelpel.git (fetch)
        origin	git@github.com:white-gecko/toelpel.git (push)
        ```

        This structure of the internal remotes dict is:

        ```
        {
            "origin": {
                "fetch": "git@github.com:white-gecko/toelpel.git",
                "push": "git@github.com:white-gecko/toelpel.git",
            },
        }
        ```

        I no remotes were set explicitely, the remotes are initialized from the
        git repository and then stored in `self._remotes`.
        """
        if not self._remotes:
            result = run(
                ["git", "-C", self.path, "remote", "-v"],
                encoding="utf-8",
                capture_output=True,
            )
            self._remotes = defaultdict(dict)
            for line in result.stdout.splitlines():
                values = line.split()
                self._remotes[values[0]][values[2][1:-1]] = values[1]
        return self._remotes

    @remotes.setter
    def remotes(self, remotes_dict):
        """Set remotes.

        See the getter method (`@property`) for the dict structure.
        """
        self._remotes = dict(remotes_dict)

    @property
    def branches(self):
        result = run(
            [
                "git",
                "-C",
                self.path,
                "branch",
                "--format",
                "%(refname:short) %(upstream)",
            ],
            encoding="utf-8",
            capture_output=True,
        )

        def gen():
            for line in result.stdout.splitlines():
                branch_remote = line.split()
                branch = branch_remote[0]
                remote = branch_remote[1] if len(branch_remote) > 1 else None
                yield branch, remote

        return dict(gen())

    @property
    def stashes(self):
        result = run(
            ["git", "-C", self.path, "stash", "list"],
            encoding="utf-8",
            capture_output=True,
        )

        def gen():
            for line in result.stdout.splitlines():
                yield line

        return list(gen())

    @property
    def dirty(self):
        result = run(
            ["git", "-C", self.path, "status", "--porcelain"],
            encoding="utf-8",
            capture_output=True,
        )
        return result.stdout

    @property
    def ignorred_dirt(self):
        """Get existing files that are ignored."""
        result = run(
            ["git", "-C", self.path, "status", "--ignored", "--porcelain"],
            encoding="utf-8",
            capture_output=True,
        )
        return result.stdout

    @property
    def synchronous(self):
        """TODO"""
        pass

    @property
    def detached(self):
        """TODO"""
        pass

    @property
    def local_branches(self):
        return [branch for branch, remote in self.branches.items() if remote is None]

    def behind(self, branch):
        remote = self.branches[branch]
        result = run(
            ["git", "-C", self.path, "rev-list", "--count", f"{branch}..{remote}"],
            encoding="utf-8",
            capture_output=True,
        )
        return int(result.stdout) if len(result.stdout) else 0

    def ahead(self, branch):
        remote = self.branches[branch]
        result = run(
            ["git", "-C", self.path, "rev-list", "--count", f"{remote}..{branch}"],
            encoding="utf-8",
            capture_output=True,
        )
        return int(result.stdout) if len(result.stdout) else 0

    def fetch(self):
        run(
            ["git", "-C", self.path, "fetch", "--all"],
            encoding="utf-8",
            capture_output=True,
        )

    def clone(self, remotes=None):
        if self.remotes.keys():
            origin = self.remotes["origin"]["fetch"]
            res = run(
                ["git", "-C", self.path, "clone", origin, "."],
                encoding="utf-8",
                capture_output=True,
            )
            logger.debug(res)

    def setup(self):
        def set_remote(*args):
            run(
                ["git", "-C", self.path, "remote", "add", *args],
                encoding="utf-8",
                capture_output=True,
            )

        for remote, remote_dict in self.remotes.items():
            if remote_dict["push"] == remote_dict["fetch"]:
                set_remote(remote, remote_dict["push"])
            else:
                for mirror, url in remote_dict.items():
                    set_remote("--mirror", mirror, remote, url)
