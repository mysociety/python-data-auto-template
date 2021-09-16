import shutil
import os
from pathlib import Path

template_dir = r"{{ cookiecutter._template }}"
if any(x in template_dir for x in ["https:", "gh:"]):
    repo_name = template_dir.split("/")[-1]
    template_dir = Path.home() / ".cookiecutters" / repo_name
else:
    template_dir = Path(template_dir)

repo_dir = template_dir / ("{" + "{ cookiecutter.repo_name }" + "}")

template_repo = "https://github.com/mysociety/template_notebook"
template_branch = "main"

helper_repo = "https://github.com/mysociety/notebook_helper"
helper_branch = "main"

os.system(f"cd {template_dir} && git submodule update --init --recursive")

# update to latest version
os.system(f'cd "{repo_dir}" && git reset --hard')
os.system(f'cd "{repo_dir}" && git remote rm origin')
os.system(f'cd "{repo_dir}" && git remote add origin "{template_repo}" && git fetch origin && git pull origin main && git checkout main')

os.system(f'cd "{repo_dir}" && cd notebook_helper && git remote rm origin')
os.system(f'cd "{repo_dir}" && cd notebook_helper && git remote add origin "{helper_repo}" && git fetch origin && git pull origin main && git checkout main')

source_readme = Path(template_dir, "cookie-readme.md")
dest_readme = Path(repo_dir, "readme.md")
general_readme = Path(repo_dir, "notebooks-readme.md")

print(f"Copying {dest_readme} to {general_readme}")
shutil.copyfile(dest_readme, general_readme)

print(f"Copying {source_readme} to {dest_readme}")
shutil.copyfile(source_readme, dest_readme)
