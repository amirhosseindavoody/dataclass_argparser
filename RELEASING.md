# Releasing dataclass-argparser

This project publishes to **PyPI** (automated) and **conda-forge** (manual feedstock PR).

## Prerequisites

- `main` is green in CI
- [pixi](https://pixi.sh/) installed
- [GitHub CLI](https://cli.github.com/) (`gh`) authenticated
- Push access to `main` and permission to create releases

## Quick release

From `main` with a clean working tree:

```bash
./release.sh
```

Or step by step:

```bash
pixi run update-version
git add pyproject.toml pixi.toml pixi.lock
git commit -m "Bump version to X.Y.Z.N"
git push origin main
git tag -a vX.Y.Z.N -m "Release vX.Y.Z.N"
git push origin vX.Y.Z.N
gh release create vX.Y.Z.N --title "Release vX.Y.Z.N" --notes "..."
```

`./release.sh` runs the version bump, commit, tag, and GitHub Release creation for you.

Options:

```bash
./release.sh --dry-run              # preview actions
./release.sh --notes CHANGELOG.md   # custom release notes
```

## What happens automatically

| Step | How |
| --- | --- |
| Version bump | `scripts/update_version.sh` (CalVer `YYYY.M.D.N`) |
| PyPI upload | `.github/workflows/publish.yml` when a GitHub Release is **published** |
| conda-forge | **Not automatic** — you open a feedstock PR after PyPI |

PyPI uses [trusted publishing](https://docs.pypi.org/trusted-publishers/) (OIDC). No API token is stored in the repo.

## Release checklist

```text
[ ] CI is green on main
[ ] ./release.sh  (or manual steps above)
[ ] "Publish to PyPI" workflow succeeded
[ ] New version visible on https://pypi.org/project/dataclass-argparser/
[ ] Feedstock PR merged on conda-forge/dataclass-argparser-feedstock
[ ] conda install -c conda-forge dataclass-argparser picks up the version
```

## conda-forge (after every PyPI release)

The feedstock downloads the **sdist from PyPI**, so PyPI must finish first.

1. Get the sdist sha256:

   ```bash
   VERSION=2026.6.30.0
   curl -sL "https://pypi.org/pypi/dataclass-argparser/${VERSION}/json" \
     | python -c "import json,sys; v=sys.argv[1]; r=json.load(sys.stdin)['releases'][v]; print(next(x['digests']['sha256'] for x in r if x['packagetype']=='sdist'))" "$VERSION"
   ```

2. Open a PR on [conda-forge/dataclass-argparser-feedstock](https://github.com/conda-forge/dataclass-argparser-feedstock) updating `recipe/recipe.yaml`:

   - `context.version` → new version (no `v` prefix)
   - `source.sha256` → hash from step 1
   - `build.number` → `0` for a new upstream version

3. Merge when CI passes; packages appear on conda-forge after the feedstock build completes.

## Version format

CalVer: `YYYY.M.D.N`

- `YYYY.M.D` — release date
- `N` — same-day release counter (`.0`, `.1`, …)

Git tags use a `v` prefix: `v2026.6.30.0`.

PyPI versions are immutable. To ship a fix the same day, bump with `pixi run update-version` again (increments `N`).

## Can the whole process run in GitHub Actions?

**Partially — and that is usually the right split.**

| Part | Automate in CI? | Recommendation |
| --- | --- | --- |
| Tests on every push/PR | Yes | Already done (`.github/workflows/ci.yml`) |
| Build + upload to PyPI on release | Yes | Already done (`.github/workflows/publish.yml`) |
| Version bump + tag + GitHub Release | Possible (`workflow_dispatch`) | Optional; many teams keep this manual or semi-manual |
| conda-forge feedstock update | Possible but uncommon | Keep manual unless you invest in bot/automation |

### What works well as GitHub Actions

- **Publish on GitHub Release** (current setup) — standard, reliable, auditable.
- **Optional `workflow_dispatch` release workflow** — a button in Actions that bumps version, opens a PR, or creates a draft release. Useful for solo maintainers who want one click without a local script.

### What is usually a bad idea to fully automate

- **One workflow that bumps version, pushes to `main`, tags, publishes PyPI, and merges conda-forge** — too many moving parts, hard to roll back, and conda-forge expects human review on the feedstock anyway.
- **Auto-bump on every merge to `main`** — you lose control over when users see a new release.
- **Deleting or moving tags** (legacy `release.sh` behavior) — tags should be immutable release markers.

### Practical recommendation for this repo

1. **Keep PyPI publish in CI** (already set up).
2. **Keep `./release.sh` (or manual steps) for the human gate** — you decide when to release.
3. **Keep conda-forge as a short manual follow-up** — one feedstock PR per release; later you can rely on [regro-cd](https://github.com/regro/regro-cd) if the bot starts opening PRs when it detects new PyPI versions.
4. **Optional later improvement:** add a `workflow_dispatch` job that only runs tests + builds artifacts as a pre-release smoke check, without changing version or pushing tags.

## Troubleshooting

**PyPI workflow did not run**

- Confirm the GitHub Release was **published** (not left as a draft).
- Check Actions → "Publish to PyPI".

**PyPI upload failed**

- Version may already exist on PyPI; bump `N` and release again.
- Verify trusted publishing is configured for this repo on pypi.org.

**Tag already exists**

- Do not reuse tags. Bump the version and create a new tag.

**conda-forge build failed**

- Confirm the sdist sha256 matches PyPI.
- Check dependency or Python version constraints in the feedstock recipe.
