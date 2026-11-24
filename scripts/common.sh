# Shared helpers for the platform scripts. Sourced, not run.
set -euo pipefail

PLATFORM_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PLATFORM_DIR"

if [ ! -f .env ]; then
  echo "No .env found in $PLATFORM_DIR. Run ./scripts/install.sh first." >&2
  exit 1
fi
set -a; . ./.env; set +a

PLANS="economic basic comprehensive"

# </dev/null: "docker compose exec" would otherwise swallow the script's own stdin.
dc() { docker compose --project-name grace --env-file .env -f compose.yaml "$@" </dev/null; }
bench() { dc exec -T backend bench "$@"; }

# "acme" -> "acme.<PLATFORM_DOMAIN>"; a name with a dot is used as-is (custom domain).
site_name() {
  case "$1" in
    *.*) echo "$1" ;;
    *)   echo "$1.${PLATFORM_DOMAIN:?Set PLATFORM_DOMAIN in .env}" ;;
  esac
}

list_sites() {
  dc exec -T backend bash -c 'for d in sites/*/; do if [ -f "$d/site_config.json" ]; then basename "$d"; fi; done'
}

site_exists() { dc exec -T backend test -f "sites/$1/site_config.json"; }

valid_plan() { case " $PLANS " in *" $1 "*) return 0 ;; *) return 1 ;; esac; }

# Traefik route for one site. Traefik watches this folder, so no restart is needed.
write_route() {
  local site="$1" file="traefik/dynamic/site-${1}.yml" id="${1//./-}"
  if [ "${TLS:-true}" = "true" ]; then
    cat > "$file" <<YAML
http:
  routers:
    ${id}:
      rule: "Host(\`${site}\`)"
      entryPoints: [https]
      service: grace-frontend
      tls:
        certResolver: le
    ${id}-http:
      rule: "Host(\`${site}\`)"
      entryPoints: [http]
      service: grace-frontend
      middlewares: [redirect-https]
YAML
  else
    cat > "$file" <<YAML
http:
  routers:
    ${id}:
      rule: "Host(\`${site}\`)"
      entryPoints: [http]
      service: grace-frontend
YAML
  fi
}

remove_route() { rm -f "traefik/dynamic/site-${1}.yml"; }

random_password() {
  python3 -c 'import secrets,string,sys; a=string.ascii_letters+string.digits; print("".join(secrets.choice(a) for _ in range(int(sys.argv[1]))))' "${1:-20}"
}
