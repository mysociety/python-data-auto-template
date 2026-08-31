from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

# Resolve the original auto-template checkout in the same way as the pre-hook;
# this is where the nested template's real Git directory is stored.
template_dir_value = r"{{ cookiecutter._template }}"
if any(prefix in template_dir_value for prefix in ("https:", "gh:")):
    template_name = template_dir_value.rstrip("/").split("/")[-1]
    template_dir = Path.home() / ".cookiecutters" / template_name
else:
    template_dir = Path(template_dir_value)

placeholder = "{" + "{ cookiecutter.repo_name }" + "}"
source_repository = template_dir / placeholder


def run_git(arguments: list[str], cwd: Path | None = None) -> None:
    """
    Run Git and fail the conversion if the command is unsuccessful.
    """
    subprocess.run(["git", *arguments], check=True, cwd=cwd)


def copy_repository_metadata() -> None:
    """
    Turn the copied template submodule into a standalone Git repository.

    Cookiecutter copies the submodule's `.git` pointer, which still refers to
    metadata in the auto-template checkout. Copying that metadata preserves the
    template commit and its pinned `src/data_common` gitlink.
    """
    result = subprocess.run(
        ["git", "rev-parse", "--absolute-git-dir"],
        check=True,
        cwd=source_repository,
        capture_output=True,
        text=True,
    )
    source_git_dir = Path(result.stdout.strip())
    generated_git = Path(".git")
    if generated_git.is_dir():
        shutil.rmtree(generated_git)
    else:
        generated_git.unlink(missing_ok=True)
    shutil.copytree(source_git_dir, generated_git)

    # The copied config still points its worktree at the placeholder directory
    # inside the auto-template. Removing that setting makes Git use this new
    # repository directory. Use --file from outside the generated repository so
    # Git does not try to follow the stale worktree while changing the config.
    generated_git = generated_git.resolve()
    run_git(
        [
            "config",
            "--file",
            str(generated_git / "config"),
            "--unset-all",
            "core.worktree",
        ],
        cwd=template_dir,
    )
    data_common_git_dir = Path(".git/modules/src/data_common")
    if data_common_git_dir.exists():
        # Keep the helper as a real submodule and redirect its copied metadata to
        # the generated repository's src/data_common working tree.
        data_common_config = data_common_git_dir.resolve() / "config"
        run_git(
            [
                "config",
                "--file",
                str(data_common_config),
                "core.worktree",
                "../../../../src/data_common",
            ],
            cwd=template_dir,
        )
    Path("src/data_common/.git").write_text(
        "gitdir: ../../.git/modules/src/data_common\n"
    )


copy_repository_metadata()
# Local development expects .env, while .env-example remains the committed
# reference file.
shutil.copyfile(Path(".env-example"), Path(".env"))

packages_setup = Path("src/data_common/bin/packages_setup.bash")
if packages_setup.exists():
    # A Windows checkout can introduce CRLF endings that prevent this Bash
    # script from running inside the Linux development container.
    packages_setup.write_bytes(packages_setup.read_bytes().replace(b"\r\n", b"\n"))

# This workflow tests the auto-template and must not ship in projects created
# from it. Project workflows under workflows-templates remain available.
template_workflow = Path(".github/workflows/template_meta_test.yaml")
template_workflow.unlink(missing_ok=True)

# Detach the generated repository from the upstream template remote and capture
# all rendered changes in the standalone repository's initial conversion commit.
# Supply an identity for this mechanical commit because fresh CI runners and
# local machines are not guaranteed to have user.name and user.email configured.
run_git(["remote", "remove", "origin"])
run_git(["add", "--all"])
run_git(
    [
        "-c",
        "user.name=Cookie Cutter",
        "-c",
        "user.email=cookiecutter@localhost",
        "commit",
        "-m",
        "Post-templating commit",
    ]
)
