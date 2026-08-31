from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
from cookiecutter.main import cookiecutter

template_dir = Path(__file__).parent.parent


def run(
    command: list[str], cwd: Path, *, capture_output: bool = False
) -> subprocess.CompletedProcess[str]:
    """
    Run a command in the generated project and require it to succeed.
    """
    return subprocess.run(
        command,
        check=True,
        cwd=cwd,
        capture_output=capture_output,
        text=True,
    )


@pytest.fixture(scope="session")
def project_folder(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """
    Generate one project used by the meta-test suite.
    """
    output_dir = tmp_path_factory.mktemp("cookie")
    context = {
        "repo_name": "test-project",
        "description": "Demonstration of a working cloned repo",
    }
    cookiecutter(
        str(template_dir),
        no_input=True,
        extra_context=context,
        output_dir=output_dir,
    )
    return output_dir / "test-project"


@pytest.fixture(scope="session")
def synced_project(project_folder: Path) -> Path:
    """
    Install the generated project's Python 3.11 environment with uv.
    """
    run(["uv", "sync", "--python", "3.11"], project_folder)
    return project_folder


def test_project_generation(project_folder: Path) -> None:
    """
    Check the generated layout, substitutions, and pinned submodule.
    """
    assert project_folder.is_dir()
    assert not (project_folder / "docs").exists()
    assert not (project_folder / "docs/theme").exists()
    assert (project_folder / "data/packages/_published").is_dir()
    assert "uv run dataset site serve" in (project_folder / "script/server").read_text()

    gitmodules = (project_folder / ".gitmodules").read_text()
    assert "src/data_common" in gitmodules
    assert "docs/theme" not in gitmodules
    assert not (project_folder / ".github/workflows/template_meta_test.yaml").exists()

    pyproject = (project_folder / "pyproject.toml").read_text()
    assert 'name = "test_project"' in pyproject
    assert 'title = "Test Project"' in pyproject
    assert "template_data_repo" not in pyproject
    assert "pages.mysociety.org/test-project" in pyproject
    assert "github.com/mysociety/test-project" in pyproject
    assert (
        'publish_url = "https://pages.mysociety.org/test-project/datasets/"'
        in pyproject
    )
    assert 'base_url = "/test-project"' in pyproject
    assert 'canonical_url = "https://pages.mysociety.org/test-project"' in pyproject
    assert 'source_url = "https://github.com/mysociety/test-project"' in pyproject
    assert "Demonstration of a working cloned repo" in pyproject

    dockerfile = (project_folder / "Dockerfile").read_text()
    docker_compose = (project_folder / "docker-compose.yml").read_text()
    devcontainer = (project_folder / ".devcontainer/devcontainer.json").read_text()
    assert "WORKSPACE_NAME=test-project" in dockerfile
    assert "mysociety/test-project:${TAG:-latest}" in docker_compose
    assert "/workspaces/test-project" in docker_compose
    assert '"workspaceFolder": "/workspaces/test-project"' in devcontainer

    source_commit = run(
        ["git", "ls-tree", "HEAD", "src/data_common"],
        template_dir / "{{ cookiecutter.repo_name }}",
        capture_output=True,
    ).stdout.split()[2]
    generated_commit = run(
        ["git", "-C", "src/data_common", "rev-parse", "HEAD"],
        project_folder,
        capture_output=True,
    ).stdout.strip()
    assert generated_commit == source_commit


def test_internal_pytest(synced_project: Path) -> None:
    """
    Run the generated project's tests.
    """
    run(["uv", "run", "pytest"], synced_project)


def test_ruff_check(synced_project: Path) -> None:
    """
    Run Ruff's lint checks in the generated project.
    """
    run(["uv", "run", "ruff", "check", "."], synced_project)


def test_ruff_format(synced_project: Path) -> None:
    """
    Check Ruff formatting in the generated project.
    """
    run(["uv", "run", "ruff", "format", ".", "--check"], synced_project)


def test_pyright(synced_project: Path) -> None:
    """
    Run Pyright in the generated project.
    """
    run(["uv", "run", "pyright"], synced_project)


def test_site_is_current_and_valid(synced_project: Path) -> None:
    """
    Check that the empty generated repository already uses the current site layout.
    """
    migration = run(
        ["uv", "run", "dataset", "site", "migrate"],
        synced_project,
        capture_output=True,
    )
    assert "already migrated" in (migration.stdout + migration.stderr).lower()
    run(["uv", "run", "dataset", "site", "check"], synced_project)
