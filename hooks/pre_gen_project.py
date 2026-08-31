from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

# Cookiecutter supplies either the local checkout path or the original remote
# template reference. Remote templates are cached under this conventional path.
template_dir_value = r"{{ cookiecutter._template }}"
if any(prefix in template_dir_value for prefix in ("https:", "gh:")):
    template_name = template_dir_value.rstrip("/").split("/")[-1]
    template_dir = Path.home() / ".cookiecutters" / template_name
else:
    template_dir = Path(template_dir_value)
    if not template_dir.is_absolute():
        raise ValueError("A local template directory must be an absolute path")


def run_git(arguments: list[str], cwd: Path) -> None:
    """
    Run Git and fail the conversion if the command is unsuccessful.
    """
    subprocess.run(["git", *arguments], check=True, cwd=cwd)


def amend_file(filepath: Path, replacements: list[tuple[str, str]]) -> None:
    """
    Apply the template's literal placeholder replacements to a text file.
    """
    content = filepath.read_text()
    for old, new in replacements:
        content = content.replace(old, new)
    filepath.write_text(content)

    filename = filepath.name
    for old, new in replacements:
        filename = filename.replace(old, new)
    if filename != filepath.name:
        filepath.rename(filepath.with_name(filename))


# Build these strings in pieces so Cookiecutter leaves them in the template
# source now and renders them only when it copies the generated repository.
placeholder = "{" + "{ cookiecutter.repo_name }" + "}"
underscored = "{" + "{ cookiecutter.underscored }" + "}"
project_name = "{" + "{ cookiecutter.project_name }" + "}"
description = "{" + "{ cookiecutter.description }" + "}"
repo_dir = template_dir / placeholder

template_repo = "https://github.com/mysociety/template_data_repo"

if os.environ.get("UPDATE_TO_LATEST", "true").lower() == "true":
    print("Updating template_data_repo to its current main branch")
    # The nested template is itself a submodule of this auto-template. Update
    # that repository first, then initialize data_common at the exact gitlink
    # selected by template_data_repo. In particular, do not pull its main branch.
    run_git(["submodule", "update", "--init", "--", placeholder], template_dir)
    run_git(["reset", "--hard"], repo_dir)
    run_git(["remote", "set-url", "origin", template_repo], repo_dir)
    run_git(["fetch", "origin", "main"], repo_dir)
    run_git(["checkout", "-B", "main", "origin/main"], repo_dir)
    run_git(["submodule", "sync", "--recursive"], repo_dir)
    run_git(["submodule", "update", "--init", "--recursive"], repo_dir)
else:
    print("UPDATE_TO_LATEST disabled")

source_readme = template_dir / "cookie-readme.md"
dest_readme = repo_dir / "readme.md"
print(f"Copying {source_readme} to {dest_readme}")
# The upstream readme explains the template itself; generated repositories need
# the project-facing readme maintained by this auto-template instead.
shutil.copyfile(source_readme, dest_readme)

common_replacements = [
    ("Standardised template for mysociety data repositories", description),
]
package_replacements = [
    *common_replacements,
    (
        "https://pages.mysociety.org/template_data_repo",
        f"https://pages.mysociety.org/{placeholder}",
    ),
    (
        "https://github.com/mysociety/template_data_repo",
        f"https://github.com/mysociety/{placeholder}",
    ),
    ('base_url = "/template_data_repo"', f'base_url = "/{placeholder}"'),
    ('title = "template_data_repo"', f'title = "{project_name}"'),
    ("template_data_repo", underscored),
]
# Python import/package names use underscores, while Docker names and workspace
# paths should retain the user's repository spelling (including hyphens).
repository_replacements = [
    *common_replacements,
    ("template_data_repo", placeholder),
]

for relative_path in (
    Path(".devcontainer/devcontainer.json"),
    Path("docker-compose.yml"),
    Path("Dockerfile"),
):
    amend_file(repo_dir / relative_path, repository_replacements)

amend_file(repo_dir / "pyproject.toml", package_replacements)
amend_file(repo_dir / "tests/test_template_data_repo.py", package_replacements)

package_dir = repo_dir / "src/template_data_repo"
package_dir.rename(repo_dir / f"src/{underscored}")

# Older template revisions contained this workflow. Keeping the guarded removal
# lets conversions from those revisions work without assuming it still exists.
for relative_path in (Path(".github/workflows/docker-image.yml"),):
    path = repo_dir / relative_path
    if path.exists():
        path.unlink()
