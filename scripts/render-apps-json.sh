#!/usr/bin/env bash
# Write the apps.json the image build uses to <output file>. Apps marked "private": true
# (e.g. a private app repository) are cloned with GRACE_REPO_TOKEN, a GitHub token
# that can read them: from .env on the server, or the repository secret on GitHub.
# The token is only used to clone during the build. frappe_docker deletes every app's .git
# folder before the final image is made, so it never ends up in the image. Never commit it.
#   ./scripts/render-apps-json.sh /tmp/apps.json
set -euo pipefail
cd "$(dirname "$0")/.."
OUT="${1:?usage: render-apps-json.sh <output file>}"
python3 - "$OUT" <<'PY'
import json, os, sys

apps = json.load(open("apps.json"))
token = os.environ.get("GRACE_REPO_TOKEN", "").strip()
for app in apps:
    # bench names an app after its repository and cuts the name at the first dot
    # ("G.R.A.C.E" becomes "G"), then can't find the clone. Stop here with a clear message.
    repo = app["url"].rstrip("/").rsplit("/", 1)[-1].removesuffix(".git")
    if "." in repo:
        sys.exit(f"{app['url']}: bench can't install a repository whose name contains a dot. Rename the repository (e.g. to its app name) and update apps.json.")
    if app.pop("private", False):
        if not token:
            sys.exit(
                f"{app['url']} is a private repository. Set GRACE_REPO_TOKEN (a GitHub token that can "
                "read it) in .env, or as the GRACE_REPO_TOKEN secret of this repository for the GitHub build."
            )
        app["url"] = app["url"].replace("https://", f"https://x-access-token:{token}@", 1)
fd = os.open(sys.argv[1], os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
with os.fdopen(fd, "w") as f:
    json.dump(apps, f)
PY
