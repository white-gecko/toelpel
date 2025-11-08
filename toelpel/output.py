from rich.console import Console
from rich.table import Table


def print_table(git_repos):

    console = Console()
    table = Table(show_header=True, header_style="bold")

    table.add_column("Status")
    table.add_column("Repository", ratio=2)
    table.add_column("Branches", ratio=1)

    for repo in git_repos:
        status = []
        branches = []
        status_count = 0
        if not repo.is_repo:
            table.add_row("[bold]not a repo[/bold]", f"[bold]{repo}[/bold]", "")
            continue
        if repo.dirty:
            status_count += 1
            status.append("[bold blue]?[/bold blue]")
        else:
            status.append("-")
        if repo.ignorred_dirt:
            status_count += 1
            status.append("[bold bright_black]?[/bold bright_black]")
        else:
            status.append("-")
        if repo.stashes:
            status_count += 1
            status.append("[bold yellow]*[/bold yellow]")
        else:
            status.append("-")
        if not repo.remotes:
            status_count += 1
            branches.append("[bold red]no remote[/bold red]")
        elif repo.local_branches:
            status_count += 1
            branches.append("[red]local branches[/red]")
        for branch, remote in repo.branches.items():
            if remote:
                behind = repo.behind(branch)
                ahead = repo.ahead(branch)
                status_count += 1 if (behind or ahead) else 0
                div = ""
                if behind or ahead:
                    div = f": -{behind}/+{ahead}"
                fg = "red" if div else "green"
                branches.append(f"[{fg}]\\[{branch}" + div + f"][/{fg}]")
            else:
                # branch has no remote
                status_count += 1
                branches.append(f"[bold red]\\[{branch}: ×][/bold red]")

        repo_line = f"[bold]{repo}[/bold]" if status_count else f"{repo}"
        table.add_row(" ".join(status), repo_line, " ".join(branches))
    console.print(table)
