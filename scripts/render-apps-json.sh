#!/usr/bin/env bash
# Write the apps.json the image build uses to <output file>. Apps marked "private": true
# (the GraceERP Travel repo, G.R.A.C.E) are cloned with GRACE_REPO_TOKEN, a GitHub token
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
