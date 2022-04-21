import shutil
import os
from pathlib import Path

template_dir = r"{{ cookiecutter._template }}"
if any(x in template_dir for x in ["https:", "gh:"]):
    repo_name = template_dir.split("/")[-1]
    template_dir = Path.home() / ".cookiecutters" / repo_name
else:
    template_dir = Path(template_dir)


def amend_file(filepath: Path, replace: dict):
    """
    amend a file to use cookiecutter basics
    """
    with open(filepath, "r") as f:
        txt = f.read()
    for key, value in replace.items():
        txt = txt.replace(key, value)
    with open(filepath, "w") as f:
        f.write(txt)

    filename = str(filepath)
    for key, value in replace.items():
        filename = filename.replace(key, value)
    if str(filepath) != filename:
        filepath.rename(filename)


repo_dir = template_dir / ("{" + "{ cookiecutter.repo_name }" + "}")

template_repo = "https://github.com/mysociety/template_data_repo"
template_branch = "main"

helper_repo = "https://github.com/mysociety/data_common"
helper_branch = "main"

os.system(f"cd {template_dir} && git submodule update --init --recursive")

# update to latest version
os.system(f'cd "{repo_dir}" && git reset --hard')
os.system(f'cd "{repo_dir}" && git remote rm origin')
os.system(f'cd "{repo_dir}" && git remote add origin "{template_repo}" && git fetch origin && git pull origin main && git checkout main')

os.system(f'cd "{repo_dir}" && cd src/data_common && git remote rm origin')
os.system(f'cd "{repo_dir}" && cd src/data_common && git remote add origin "{helper_repo}" && git fetch origin && git pull origin main && git checkout main')

source_readme = Path(template_dir, "cookie-readme.md")
dest_readme = Path(repo_dir, "readme.md")
general_readme = Path(repo_dir, "notebooks-readme.md")

print(f"Copying {source_readme} to {dest_readme}")
shutil.copyfile(source_readme, dest_readme)

# Amend files that have a direct reference to the original name

replace = {"template_data_repo": "{" + "{ cookiecutter.repo_name }" + "}",
           "description": "{" + "{ cookiecutter.description }" + "}"}

amend_file(Path(repo_dir, "pyproject.toml"), replace)
amend_file(Path(repo_dir, "docker-compose.yml"), replace)
amend_file(Path(repo_dir, "Dockerfile.dev"), replace)
amend_file(Path(repo_dir, "Dockerfile"), replace)
amend_file(Path(repo_dir, "tests", "test_template_data_repo.py"), replace)

to_delete = [Path(repo_dir, ".github", "workflows", "docker-image.yml")]

package_dir = Path(repo_dir, "src", "template_data_repo")
package_dir.rename(
    Path(repo_dir, "src", "{" + "{ cookiecutter.repo_name }" + "}"))

for f in to_delete:
    f.unlink()
