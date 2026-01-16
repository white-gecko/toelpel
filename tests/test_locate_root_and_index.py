
import os

from toelpel.cli import locate_root_and_index


def test_locate_root_and_index_current_dir_dot(tmp_path):
    # prepare paths
    index = tmp_path / "workspaces.ttl"
    index.touch()
    os.chdir(tmp_path)

    root_dir, index_found, _ = locate_root_and_index(".")

    # verify the results
    assert index_found.is_file()
    assert index_found.absolute() == index.absolute()
    assert root_dir.is_dir()
    assert root_dir.absolute() == tmp_path.absolute()


def test_locate_root_and_index_current_dir(tmp_path):
    # prepare paths
    index = tmp_path / "workspaces.ttl"
    index.touch()
    os.chdir(tmp_path)

    root_dir, index_found, _ = locate_root_and_index()

    # verify the results
    assert index_found.is_file()
    assert index_found.absolute() == index.absolute()
    assert root_dir.is_dir()
    assert root_dir.absolute() == tmp_path.absolute()


def test_locate_root_and_index_parent_dir(tmp_path):
    # prepare paths
    child = tmp_path / "repo"
    index = tmp_path / "workspaces.ttl"
    index.touch()
    child.mkdir()
    os.chdir(child)

    root_dir, index_found, _ = locate_root_and_index()

    # verify the results
    assert index_found.is_file()
    assert index_found.absolute() == index.absolute()
    assert root_dir.is_dir()
    assert root_dir.absolute() == tmp_path.absolute()


def test_locate_root_and_index_from_other_dir(tmp_path):
    # prepare paths
    index = tmp_path / "workspaces.ttl"
    index.touch()

    root_dir, index_found, _ = locate_root_and_index(tmp_path)

    # verify the results
    assert index_found.is_file()
    assert index_found.absolute() == index.absolute()
    assert root_dir.is_dir()
    assert root_dir.absolute() == tmp_path.absolute()

def test_locate_root_and_index_from_other_dir_given_index(tmp_path):
    # prepare paths
    index = tmp_path / "workspaces.ttl"
    index.touch()

    root_dir, index_found, _ = locate_root_and_index(tmp_path, index)

    # verify the results
    assert index_found.is_file()
    assert index_found.absolute() == index.absolute()
    assert root_dir.is_dir()
    assert root_dir.absolute() == tmp_path.absolute()


def test_locate_root_and_index_from_other_dir_given_index_different_name(tmp_path):
    # prepare paths
    index = tmp_path / "my_repos.ttl"
    index.touch()

    root_dir, index_found, _ = locate_root_and_index(tmp_path, index)

    # verify the results
    assert index_found.is_file()
    assert index_found.absolute() == index.absolute()
    assert root_dir.is_dir()
    assert root_dir.absolute() == tmp_path.absolute()


def test_locate_root_and_index_from_other_dir_given_index_in_other_dir(tmp_path):
    """In this scenario, the workspaces.ttl file is not in the root directory and not
    below it. It should demonstrate a situation, where e.g. an entire workspace is
    initialized on a new machine wile the index file is read from a backup."""
    # prepare paths
    workspaces = tmp_path / "workspaces"
    backup = tmp_path / "backup"
    index = backup / "workspaces.ttl"
    workspaces.mkdir()
    backup.mkdir()
    index.touch()

    root_dir, index_found, _ = locate_root_and_index(workspaces, index)

    # verify the results
    assert index_found.is_file()
    assert index_found.absolute() == index.absolute()
    assert root_dir.is_dir()
    assert root_dir.absolute() == workspaces.absolute()


def test_locate_root_and_index_other_dir_given_index_different_name(tmp_path):
    """In this scenario, the workspaces.ttl file is not in the root directory and not
    below it. It should demonstrate a situation, where e.g. an entire workspace is
    initialized on a new machine wile the index file is read from a backup."""
    # prepare paths
    workspaces = tmp_path / "workspaces"
    backup = tmp_path / "backup"
    index = backup / "all_of_my_work.ttl"
    workspaces.mkdir()
    backup.mkdir()
    index.touch()

    root_dir, index_found, _ = locate_root_and_index(workspaces, index)

    # verify the results
    assert index_found.is_file()
    assert index_found.absolute() == index.absolute()
    assert root_dir.is_dir()
    assert root_dir.absolute() == workspaces.absolute()
