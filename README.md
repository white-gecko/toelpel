# Git🗼Overview

This tool should facilitate the management of multiple Git repositories by providing an overview.

It provides four sub-commands:
- `index`: Scan all sub-directories starting from the rootdir for all git repositories and write the result to the index.
- `scan`: Scan the repositories in an index and update the index.
- `list`: List all repositories in an index with their respective status.
- `clone`: Clone all repositories from an index relative to the given root directory.

For each git repositories it checks its synchronicity with its configured upstreams.
