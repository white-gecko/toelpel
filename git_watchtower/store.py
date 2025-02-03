from pathlib import Path

from click import File
from loguru import logger
from rdflib import Graph, URIRef
from rdflib.namespace import RDF, Namespace

from .git import git

GW = Namespace("https://git-watch/")
RELPATH = "urn:relpath:"
INDEX_DEFAULT_NAME = "workspaces.ttl"


def discover_index(rootdir: Path | None = None):
    """Discover an index file `workspaces.ttl` in the provided rootdir or the current directory or its closesed parent."""
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


class WatchStore:
    def __init__(self, index: File, base: Path):
        self.index = index
        self.base = base
        self.graph = Graph()
        self.graph.parse(self.index, format="turtle")

    def get_relpath(self, path: Path) -> URIRef:
        relpath = path.relative_to(self.base)
        return URIRef(RELPATH + str(relpath))

    def get_abspath(self, relpath: URIRef) -> Path:
        return self.base / Path(str(relpath)[12:])

    def list_to_graph(self, repos: list) -> Graph:
        list(map(self.add_repo_to_graph, repos))
        self.graph.serialize(self.index, format="turtle")
        return self.graph

    def graph_to_list(self) -> list:
        for repo, _, _ in self.graph.triples((None, RDF.type, GW["repo"])):
            yield git(self.get_abspath(repo))

    def add_repo_to_graph(self, repo: git):
        logger.debug(
            f"write triple for {repo}: {repo.path}: {repo.path.resolve()}: {self.get_relpath(repo.path)}"
        )
        repo_resource = self.get_relpath(repo.path)
        self.graph.add((repo_resource, RDF.type, GW["repo"]))
        for remote, remote_dict in repo.remotes.items():
            repo_resource_remote = URIRef(repo_resource + f"#remote:{remote}")
            self.graph.add((repo_resource, GW["remote"], repo_resource_remote))
            for url, direction in remote_dict.items():
                self.graph.add((repo_resource_remote, GW[direction], URIRef(url)))

    def get_remotes(self, repo: git):
        for _, _, remote in self.graph.triples(
            (self.get_relpath(repo.path), GW["remote"], None)
        ):
            for _, _, push_url in self.graph.triples((remote, GW["push"], None)):
                remote_name = str(remote).rsplit(":", 1)[1]
                yield remote_name, {push_url: "push"}
