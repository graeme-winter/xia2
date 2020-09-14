# A file containing the version number of the current xia2. Generally useful.

import os


def get_git_revision(fallback):
    """Try to obtain the current git revision number
    and store a copy in .gitversion"""
    version = None
    try:
        xia2_path = os.path.split(os.path.realpath(__file__))[0]
        version_file = os.path.join(xia2_path, ".gitversion")

        # 1. Try to access information in .git directory
        #    Regenerate .gitversion if possible
        if os.path.exists(os.path.join(xia2_path, ".git")):
            try:
                import subprocess

                process = subprocess.run(
                    ("git", "describe", "--long"),
                    cwd=xia2_path,
                    encoding="latin-1",
                    stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL,
                )
                version = process.stdout.rstrip()
                if version[0] == "v":
                    version = version[1:].replace(".0-", ".")
                try:
                    process = subprocess.run(
                        ("git", "describe", "--contains", "--all", "HEAD"),
                        cwd=xia2_path,
                        encoding="latin-1",
                        stdout=subprocess.PIPE,
                        stderr=subprocess.DEVNULL,
                    )
                    branch = process.stdout.rstrip()
                    if (
                        branch != ""
                        and branch != "master"
                        and not branch.endswith("/master")
                    ):
                        version = version + "-" + branch
                except Exception:
                    pass
                with open(version_file, "w") as gv:
                    gv.write(version)
            except Exception:
                pass

        # 2. If .git directory or git executable missing, read .gitversion
        if not version and os.path.exists(version_file):
            with open(version_file) as gv:
                version = gv.read().rstrip()
    except Exception:
        pass

    return str(version or fallback)


VersionNumber = get_git_revision("0.7.0")
Version = f"XIA2 {VersionNumber}"
