from rdflib import Graph, URIRef
from .git import git
from rdflib.namespace import Namespace, RDF
from loguru import logger
from click import File
from pathlib import Path

GW = Namespace("https://git-watch/")
RELPATH = "urn:relpath:"

class WatchStore():
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
        logger.debug(f"write triple for {repo}: {repo.path}: {repo.path.resolve()}: {self.get_relpath(repo.path)}")
        repo_resource = self.get_relpath(repo.path)
        self.graph.add((repo_resource, RDF.type, GW["repo"]))
        for remote, remote_dict in repo.remotes.items():
            repo_resource_remote = URIRef(repo_resource + f"#remote:{remote}")
            self.graph.add((repo_resource, GW["remote"], repo_resource_remote))
            for url, direction in remote_dict.items():
                self.graph.add((repo_resource_remote, GW[direction], URIRef(url)))
