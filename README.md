# Tölpel

Is a tool to keep an overview on your Git repositories to facilitate the management of multiple Git repositories.

It provides four sub-commands:
- `list`: List all repositories in an index with their respective status.
  - *should be*: List all repositories *below a given directory (root dir)* with their respective status. It also creates an index of the repositories.
- `clone`: Clone all repositories from an index relative to the given root directory.
- `index`: Scan all sub-directories starting from the rootdir for all git repositories and write the result to the index.
  - *should be*: one command with `scan`
- `scan`: Scan the repositories in an index and update the index.
- `scan-remote`: For each git repository it checks its synchronicity with its configured upstreams.

It also provides a permanent monitoring service, that watches your git repositories.

- periodically performs a `scan`? for the beginning
  - later it could also set filesystem watchers and only scan the directories in which changes happen

## TODO and Ideas

- Detect repositories that are not part of the index.
- Provide ids for each workspace.
- Also index remote services, e.g. gitolite, github, and gitlab.
- A default remote service, that allows to create new repositories in this service and configure them as remote.

## The Name?

*Tölpel* (English *gannet*) are birds that look out from high above the see for fish and then hut by diving into the see. Also they breeding in colonies. The German word *Tölpel* can be translated as *git*.
