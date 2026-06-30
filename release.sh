#!/usr/bin/env bash
#
# Bump CalVer, commit, tag, and publish a GitHub Release.
# Publishing the release triggers .github/workflows/publish.yml (PyPI upload).
#
# Usage:
#   ./release.sh
#   ./release.sh --notes CHANGELOG.md
#   ./release.sh --dry-run
#
# After PyPI finishes, update the conda-forge feedstock (see RELEASING.md).

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYPROJECT="$ROOT/pyproject.toml"
NOTES=""
DRY_RUN=0

usage() {
    sed -n '2,12p' "$0" | sed 's/^# \?//'
}

log() {
    echo "==> $*"
}

run() {
    if [[ "$DRY_RUN" -eq 1 ]]; then
        echo "[dry-run] $*"
    else
        "$@"
    fi
}

die() {
    echo "error: $*" >&2
    exit 1
}

require_command() {
    command -v "$1" >/dev/null 2>&1 || die "missing required command: $1"
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --dry-run)
            DRY_RUN=1
            shift
            ;;
        --notes)
            [[ $# -ge 2 ]] || die "--notes requires a file path"
            NOTES="$2"
            [[ -f "$NOTES" ]] || die "release notes file not found: $NOTES"
            shift 2
            ;;
        -h | --help)
            usage
            exit 0
            ;;
        *)
            die "unknown option: $1 (try --help)"
            ;;
    esac
done

require_command git
require_command gh

if [[ "$DRY_RUN" -eq 0 ]]; then
    require_command pixi
fi

cd "$ROOT"

if ! git diff --quiet || ! git diff --cached --quiet; then
    die "working tree is not clean; commit or stash changes before releasing"
fi

BRANCH="$(git rev-parse --abbrev-ref HEAD)"
if [[ "$BRANCH" != "main" ]]; then
    die "releases must be cut from main (current branch: $BRANCH)"
fi

log "Bumping CalVer version"
run "$ROOT/scripts/update_version.sh"

VERSION="$(grep '^version = ' "$PYPROJECT" | sed 's/version = "\(.*\)"/\1/')"
TAG="v${VERSION}"

if git rev-parse "$TAG" >/dev/null 2>&1; then
    die "tag $TAG already exists locally; pick a new version or delete the tag manually"
fi

if [[ "$DRY_RUN" -eq 0 ]] && git ls-remote --exit-code --tags origin "refs/tags/${TAG}" >/dev/null 2>&1; then
    die "tag $TAG already exists on origin"
fi

if git status --porcelain -- pyproject.toml pixi.toml pixi.lock | grep -q .; then
    log "Committing version bump"
    run git add pyproject.toml pixi.toml pixi.lock
    run git commit -m "Bump version to ${VERSION}"
    run git push origin main
else
    log "Version files unchanged; using existing version ${VERSION}"
fi

log "Creating tag ${TAG}"
run git tag -a "$TAG" -m "Release ${TAG}"
run git push origin "$TAG"

RELEASE_NOTES="${NOTES:-Release ${TAG} ($(date +%Y-%m-%d))}"

log "Creating GitHub release ${TAG}"
if [[ -n "$NOTES" ]]; then
    run gh release create "$TAG" --title "Release ${TAG}" --notes-file "$NOTES"
else
    run gh release create "$TAG" --title "Release ${TAG}" --notes "$RELEASE_NOTES"
fi

cat <<EOF

Release started: ${TAG}

Next steps:
  1. Wait for the "Publish to PyPI" workflow to finish on GitHub Actions.
  2. Confirm the sdist on https://pypi.org/project/dataclass-argparser/${VERSION}/
  3. Open a PR on https://github.com/conda-forge/dataclass-argparser-feedstock
     with the new version and sdist sha256 (see RELEASING.md).

EOF
