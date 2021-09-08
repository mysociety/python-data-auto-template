import shutil
import os
from pathlib import Path

template_dir = r"{{ cookiecutter._template }}"
if "https:" in template_dir:
    repo_name = template_dir.split("/")[-1]
    template_dir = Path.home() / ".cookiecutters" / repo_name
else:
    template_dir = Path(template_dir)

template_repo = "https://github.com/mysociety/template_notebook"
template_branch = "main"

helper_repo = "https://github.com/mysociety/notebook_helper"
helper_branch = "main"

# this was all a submodule in the template, now it stands alone. Need to copy across the git info.
Path(".git").unlink()
real_git_folder = Path(template_dir) / ".git" / "modules" / ("{" + "{ cookiecutter.repo_name }" + "}")
shutil.copytree(real_git_folder, ".git")
git_config = Path(".git", "config")
notebook_git_config = Path(".git","modules", "notebook_helper", "config")

# remove reference to the work tree above
with open(git_config, "r") as f:
    lines = f.readlines()
with open(git_config, "w") as f:
    for line in lines:
        if "cookiecutter.repo_name" not in line:
            f.write(line)

# remove reference to the work tree above
with open(notebook_git_config, "r") as f:
    lines = f.readlines()
with open(notebook_git_config, "w") as f:
    for line in lines:
        if "cookiecutter.repo_name" not in line:
            f.write(line)
        else:
            f.write("	worktree = ../../../notebook_helper\n")

# adjust the git directory for the notebook helper
with open(Path("notebook_helper",".git"), "w") as file:
    file.write("gitdir: ../.git/modules/notebook_helper")

#copy example env to env
shutil.copyfile(Path(".env-example"),
                Path(".env"))

# when doing this on windows, sometimes clones bad line endings. 
# This fixes the bash file docker uses. 
# replacement strings
WINDOWS_LINE_ENDING = b'\r\n'
UNIX_LINE_ENDING = b'\n'

# relative or absolute file path, e.g.:
file_path = Path("notebook_helper", "packages_setup.bash")

with open(file_path, 'rb') as open_file:
    content = open_file.read()
    
content = content.replace(WINDOWS_LINE_ENDING, UNIX_LINE_ENDING)

with open(file_path, 'wb') as open_file:
    open_file.write(content)

# remove, we don't want this project to have a default origin of the template library
os.system(f'git remote rm origin')

# package all up in a little box
os.system("git add --all")
os.system('git commit -m "Post-templating commit"')