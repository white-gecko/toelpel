from subprocess import run, DEVNULL
from pathlib import Path
from collections import defaultdict

class git():
    def __init__(self, repo: Path):
        self.path = repo
        self._remotes = None

    def __repr__(self) -> str:
        return self.path

    def __str__(self) -> str:
        return f"<git repo at {self.path}>"

    @property
    def isRepo(self) -> bool:
        return run(["git", "-C", self.path, "rev-parse"], stderr=DEVNULL).returncode == 0

    @property
    def remotes(self):
        """A dictionary of the configured remotes of the repository.

        """
        if not self._remotes:
            result = run(["git", "-C", self.path, "remote", "-v"], encoding="utf-8", capture_output=True)
            self._remotes = defaultdict(dict)
            for line in result.stdout.splitlines():
                values = line.split()
                self._remotes[values[0]][values[1]] = values[2][1:-1]
        return self._remotes

    @property
    def branches(self):
        result = run(["git", "-C", self.path, "branch", "--format", "%(refname:short) %(upstream)"], encoding="utf-8", capture_output=True)
        def gen():
            for line in result.stdout.splitlines():
                branch_remote = line.split()
                branch = branch_remote[0]
                remote = branch_remote[1] if len(branch_remote) > 1 else None
                yield branch, remote
        return dict(gen())

    @property
    def stashes(self):
        result = run(["git", "-C", self.path, "stash", "list"], encoding="utf-8", capture_output=True)
        def gen():
            for line in result.stdout.splitlines():
                yield line
        return list(gen())

    @property
    def dirty(self):
        result = run(["git", "-C", self.path, "status", "--porcelain"], encoding="utf-8", capture_output=True)
        return result.stdout

    @property
    def ignorred_dirt(self):
        result = run(["git", "-C", self.path, "status", "--ignored", "--porcelain"], encoding="utf-8", capture_output=True)
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
        result = run(["git", "-C", self.path, "rev-list", "--count", f"{branch}..{remote}"], encoding="utf-8", capture_output=True)
        return int(result.stdout) if len(result.stdout) else 0

    def ahead(self, branch):
        remote = self.branches[branch]
        result = run(["git", "-C", self.path, "rev-list", "--count", f"{remote}..{branch}"], encoding="utf-8", capture_output=True)
        return int(result.stdout) if len(result.stdout) else 0

    def fetch(self):
        run(["git", "-C", self.path, "fetch", "--all"], encoding="utf-8", capture_output=True)

    def clone(self):
        # TODO make sure the origin is setup as fetch
        origin = self.remotes["origin"].keys()[0]
        run(["git", "-C", self.path, "clone", origin, "."], encoding="utf-8", capture_output=True)

    def setup(self):
        for remote, remote_dict in self.remotes["origin"].items():
            if remote == "origin":
                continue
            for url, direction in remote_dict.items():
                run(["git", "-C", self.path, "remote", "add", remote, url], encoding="utf-8", capture_output=True)
