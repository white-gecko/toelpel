from itertools import chain
from pathlib import Path

from loguru import logger
from rdflib import Graph, URIRef
from rdflib.namespace import RDF, Namespace

from .git import git

TOEL = Namespace("https://toelpel/")
RELPATH = "path:"
URN_RELPATH = "urn:relpath:"
INDEX_DEFAULT_NAME = "workspaces.ttl"


def find_index(rootdir: Path | None = None, working_dir: Path | None = None):
    """Discover an index file `workspaces.ttl` in the provided rootdir or the current
    directory or its closest parent."""
    if rootdir is not None:
        index = rootdir / INDEX_DEFAULT_NAME
        return index if index.exists() else None

    if working_dir and not working_dir.is_absolute():
        working_dir = working_dir.absolute()

    for path in [working_dir, *working_dir.parents]:
        index = path / INDEX_DEFAULT_NAME
        if index.exists():
            return index
        path = path.parent
    logger.error("Reached root, but found no index.")
    return None


def uri_to_path(uri):
    if isinstance(uri, URIRef):
        uri_str = str(uri)
        if uri_str[0:12] == URN_RELPATH:
            return uri_str[12:]
        elif uri_str[0:5] == RELPATH:
            return uri_str[5:]
    return uri


class Colony:
    """A Colony is a datastructure layered on the directory tree of the collection of
    git projects (nests) that allows to interact with each repository.

    cf. https://en.wikipedia.org/w/index.php?title=Sulidae&oldid=1315640675#Reproduction
    """

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
        store = Colony(index, index.parent)
        ```
        """
        self.index = Path(index)
        self.base = Path(base)
        self.graph = Graph()
        if self.index.exists():
            self.graph.parse(self.index, format="turtle")

    def get_abspath(self, relpath: URIRef) -> Path:
        return self.base / Path(uri_to_path(relpath))

    def get_relpath(self, path: Path) -> Path:
        return path.relative_to(self.base)

    def get_relpath_iri(self, path: Path, urn: bool = False) -> URIRef:
        if urn:
            return URIRef(URN_RELPATH + str(self.get_relpath(path)))
        return URIRef(RELPATH + str(self.get_relpath(path)))

    def update_from_list(self, repos: list) -> Graph:
        list(map(self.add_repo_to_graph, repos))
        self.graph.serialize(self.index, format="turtle")
        return self.graph

    def to_list(self, working_dir: Path | None = None, plain=False) -> list:
        for repo, _, _ in self.graph.triples((None, RDF.type, TOEL["repo"])):
            repo_abspath = self.get_abspath(repo)
            if working_dir and not repo_abspath.is_relative_to(working_dir):
                continue
            if plain:
                yield str(git(repo_abspath, self.base).path)
            else:
                yield git(repo_abspath, self.base)

    def add_repo_to_graph(self, repo: git):
        logger.debug(
            f"write triple for {repo}: {repo.path}: {repo.path.resolve()}: {self.get_relpath_iri(repo.path)}"
        )
        repo_resource = self.get_relpath_iri(repo.path)
        self.graph.add((repo_resource, RDF.type, TOEL["repo"]))
        for remote, remote_dict in repo.remotes.items():
            repo_resource_remote = URIRef(repo_resource + f"#remote:{remote}")
            self.graph.add((repo_resource, TOEL["remote"], repo_resource_remote))
            for mirror, url in remote_dict.items():
                self.graph.add((repo_resource_remote, TOEL[mirror], URIRef(url)))

    def get_remotes(self, repo: git):
        for _, _, remote in chain(
            self.graph.triples((self.get_relpath_iri(repo.path), TOEL["remote"], None)),
            self.graph.triples(
                (self.get_relpath_iri(repo.path, urn=True), TOEL["remote"], None)
            ),
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
