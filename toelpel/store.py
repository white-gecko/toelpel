from pathlib import Path

from loguru import logger
from rdflib import Graph, URIRef
from rdflib.namespace import RDF, Namespace

from .git import git

TOEL = Namespace("https://toelpel/")
RELPATH = "path:"
INDEX_DEFAULT_NAME = "workspaces.ttl"


def find_index(rootdir: Path | None = None):
    """Discover an index file `workspaces.ttl` in the provided rootdir or the current
    directory or its closest parent."""
    if rootdir is not None:
        index = rootdir / INDEX_DEFAULT_NAME
        return index if index.exists() else None

    for path in [Path.cwd(), *Path.cwd().parents]:
        index = path / INDEX_DEFAULT_NAME
        if index.exists():
            return index
        path = path.parent
    logger.error("Reached root, but found no index.")
    return None


def uri_to_path(uri):
    if isinstance(uri, URIRef):
        uri_str = str(uri)
        if uri_str[0:12] == "urn:relpath:":
            return uri_str[12:]
        elif uri_str[0:5] == "path:":
            return uri_str[5:]
    return uri


class WatchStore:
    """A WatchStore is adatastructure layered on the directory tree of the collection of
    git projects that allows to interact with each repository."""

    def __init__(self, index: str | Path, base: str | Path):
        """The index file is a `workspaces.ttl` file. The base is the base path relative
        to which the workspeaces.ttl should be interpreted.

        For a already set-up space, the base path is the parent directory of the
        `workspaces.ttl` file.
        If the space is not yet initialized, the base path is the location, where the
        space should be initialized.

        A common usage of this class is:
        ```
        index = find_index()
        store = WatchStore(index, index.parent)
        ```
        """
        self.index = Path(index)
        self.base = Path(base)
        self.graph = Graph()
        if self.index.exists():
            self.graph.parse(self.index, format="turtle")

    def get_relpath(self, path: Path) -> URIRef:
        relpath = path.relative_to(self.base)
        return URIRef(RELPATH + str(relpath))

    def get_abspath(self, relpath: URIRef) -> Path:
        return self.base / Path(uri_to_path(relpath))

    def list_to_graph(self, repos: list) -> Graph:
        list(map(self.add_repo_to_graph, repos))
        self.graph.serialize(self.index, format="turtle")
        return self.graph

    def graph_to_list(self) -> list:
        for repo, _, _ in self.graph.triples((None, RDF.type, TOEL["repo"])):
            yield git(self.get_abspath(repo), Path(uri_to_path(repo)))

    def add_repo_to_graph(self, repo: git):
        logger.debug(
            f"write triple for {repo}: {repo.path}: {repo.path.resolve()}: {self.get_relpath(repo.path)}"
        )
        repo_resource = self.get_relpath(repo.path)
        self.graph.add((repo_resource, RDF.type, TOEL["repo"]))
        for remote, remote_dict in repo.remotes.items():
            repo_resource_remote = URIRef(repo_resource + f"#remote:{remote}")
            self.graph.add((repo_resource, TOEL["remote"], repo_resource_remote))
            for mirror, url in remote_dict.items():
                self.graph.add((repo_resource_remote, TOEL[mirror], URIRef(url)))

    def get_remotes(self, repo: git):
        for _, _, remote in self.graph.triples(
            (self.get_relpath(repo.path), TOEL["remote"], None)
        ):
            remote_name = str(remote).rsplit(":", 1)[1]
            fetch_url = self.graph.value(remote, TOEL["fetch"])
            push_url = self.graph.value(remote, TOEL["push"]) or fetch_url
            if fetch_url is None:
                fetch_url = push_url
            logger.debug(push_url)
            logger.debug(fetch_url)
            push_url = uri_to_path(push_url)
            fetch_url = uri_to_path(fetch_url)
            logger.debug(fetch_url)
            logger.debug(push_url)
            yield remote_name, {"fetch": push_url, "push": push_url}
