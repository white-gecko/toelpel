# Tölpel

Is a tool to keep an overview on your Git repositories to facilitate the management of multiple Git repositories.

It provides three sub-commands:
- `scan`: Scan the repositories in an index and update the index.
  - `--discover` Add new repositories that are not contained in the index
- `list`: List all repositories in an index with their respective status.
  - *should be*: List all repositories from the index *below a given directory (base dir)* with their respective status.
    - currently `toelpel list .` does not work in a subdirectory of the worspace root
  - *should be*: an option of `list`, e.g. `--remote`, to checks for each git repository its synchronicity with its configured upstreams.
- `clone`: Clone all repositories from an index relative to the given root directory.

*should be*: It also provides a permanent monitoring service, that watches your git repositories.

- Periodically performs a `scan`? for the beginning
  - later it could also set file system watchers and only scan the directories in which changes happen

## Usage

Choose a directory that should be the base of your workspace.


## TODO and Ideas

- Detect repositories that are not part of the index.
- Provide IDs for each workspace.
- Also index the personal account on remote services, e.g. gitolite, github, and gitlab.
- A default remote service, that allows to create new repositories in this service and configure them as remote.

## The Name?

*Tölpel* (English *gannet*) are birds that look out from high above the see for fish and then hut by diving into the see. Also they breeding in colonies. The German word *Tölpel* can be translated as *git*.
