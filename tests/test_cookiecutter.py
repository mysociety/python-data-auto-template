import pytest
from cookiecutter.main import cookiecutter
from pathlib import Path
import subprocess

template_dir = Path(__file__).parent / ".."

@pytest.fixture(scope="session")
def cookie_folder(tmp_path_factory) -> Path:
    """
    Create folder to test new template in in
    """
    fn = tmp_path_factory.mktemp("cookie")
    return fn


@pytest.fixture(scope="session")
def project_folder(cookie_folder):
    """
    Create a cookiecutter project
    """
    context = {"repo_name":"test-project",
               "description": "Demonstration of a working cloned repo"}

    cookiecutter(str(template_dir),
                 no_input=True,
                 extra_context=context,
                 output_dir=cookie_folder)

    return cookie_folder / "test-project"


@pytest.fixture(scope="session")
def activated_project(project_folder: Path):
    """
    Activate venv inside project
    """
    subprocess.run("python -m poetry install".split(" "), check=True, cwd=project_folder)
    return project_folder

def test_project_generation(project_folder: Path):
    """
    Generate a project and check for cookiecutter errors
    """

    assert project_folder.exists() is True

def test_internal_pytest(activated_project: Path):
    """
    Within clone of project, try and run the internal meta tests
    This will check basic stuff like the python library paths being valid.
    """
    subprocess.run("python -m poetry run pytest".split(" "), check=True, cwd=activated_project)


def test_black(activated_project: Path):
    """
    Within clone of project, try and run black
    """
    subprocess.run("python -m poetry run black .".split(" "), check=True, cwd=activated_project)


def test_pyright(activated_project: Path):
    """
    Within clone of project, try and run pyright
    """
    subprocess.run("python -m poetry run pyright".split(" "), check=True, cwd=activated_project)