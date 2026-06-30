# Releasing dataclass-argparser

This project publishes to **PyPI** (automated on GitHub Release) and **conda-forge** (bot PR from PyPI, with manual fallback).

## Prerequisites

- `main` is green in CI
- [pixi](https://pixi.sh/) installed
- [GitHub CLI](https://cli.github.com/) (`gh`) authenticated
- Push access to `main` and permission to create releases
- [Trusted publishing](https://docs.pypi.org/trusted-publishers/) configured on PyPI for this repo and the `pypi` GitHub environment

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
| PyPI upload | `.github/workflows/publish.yml` when a GitHub Release is **published** (checks out the release tag and verifies it matches `pyproject.toml`) |
| conda-forge | `@regro-cf-autotick-bot` opens a feedstock PR after PyPI; merge when CI passes |

PyPI uses [trusted publishing](https://docs.pypi.org/trusted-publishers/) (OIDC). No API token is stored in the repo.

The publish workflow runs **only** on published GitHub Releases — not on tag push alone and not via manual dispatch.

## Release checklist

```text
[ ] CI is green on main
[ ] ./release.sh  (or manual steps above)
[ ] "Publish to PyPI" workflow succeeded
[ ] New version visible on https://pypi.org/project/dataclass-argparser/
[ ] @regro-cf-autotick-bot feedstock PR merged (or manual feedstock PR if bot is slow)
[ ] conda install -c conda-forge dataclass-argparser picks up the version
```

## conda-forge (after PyPI)

The feedstock at [conda-forge/dataclass-argparser-feedstock](https://github.com/conda-forge/dataclass-argparser-feedstock) uses a **PyPI source URL**, so `@regro-cf-autotick-bot` polls PyPI and should open a version-bump PR automatically after each new release.

What to do after PyPI finishes:

1. Watch the feedstock for a bot PR titled like `dataclass-argparser v2026.6.30.0`.
2. Merge it when CI is green (`bot.automerge: version` is enabled on the feedstock).
3. If no bot PR appears after several hours, open a manual feedstock PR (fallback below).

### Feedstock bot configuration

The feedstock is already set up correctly for PyPI detection:

- `recipe/recipe.yaml` uses a PyPI sdist URL (`pypi.org/packages/source/...`)
- `conda_build_tool: rattler-build` with v1 `recipe.yaml` (supported by `@regro-cf-autotick-bot`)

No extra bot config is required for the bot to **detect** new PyPI versions. To reduce manual work, add this to the feedstock’s `conda-forge.yml` and merge via PR on the feedstock repo:

```yaml
bot:
  automerge: version
  inspection: hint-grayskull
```

That keeps automatic version PRs and merges them when CI passes. You (as feedstock maintainer) need to open that PR on [conda-forge/dataclass-argparser-feedstock](https://github.com/conda-forge/dataclass-argparser-feedstock) — it cannot be changed from this source repo.

### Manual feedstock PR (fallback)

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
| Build + upload to PyPI on GitHub Release | Yes | Done in `.github/workflows/publish.yml` |
| Version bump + tag + GitHub Release | Local `./release.sh` | Human gate for when to release |
| conda-forge feedstock update | Bot PR from PyPI | Enabled on feedstock; merge bot PRs |

### What works well as GitHub Actions

- **Publish on GitHub Release** (current setup) — standard, reliable, auditable.
- **Optional `workflow_dispatch` release workflow** — a button in Actions that bumps version, opens a PR, or creates a draft release. Useful for solo maintainers who want one click without a local script.

### What is usually a bad idea to fully automate

- **One workflow that bumps version, pushes to `main`, tags, publishes PyPI, and merges conda-forge** — too many moving parts, hard to roll back, and conda-forge expects human review on the feedstock anyway.
- **Auto-bump on every merge to `main`** — you lose control over when users see a new release.
- **Deleting or moving tags** (legacy `release.sh` behavior) — tags should be immutable release markers.

### Practical recommendation for this repo

1. **PyPI publish on GitHub Release** — automated in CI.
2. **`./release.sh` for the human gate** — you decide when to release.
3. **conda-forge via bot PR** — merge `@regro-cf-autotick-bot` PRs; use manual feedstock PR only as fallback.

## Troubleshooting

**PyPI workflow did not run**

- Confirm the GitHub Release was **published** (not left as a draft).
- Check Actions → "Publish to PyPI".

**PyPI upload failed**

- Version may already exist on PyPI; bump `N` and release again.
- Verify trusted publishing is configured for this repo on pypi.org.

**Tag already exists**

- Do not reuse tags. Bump the version and create a new tag.

**No conda-forge bot PR**

- Confirm the new version is on PyPI first.
- Check open PRs on [conda-forge/dataclass-argparser-feedstock](https://github.com/conda-forge/dataclass-argparser-feedstock).
- If the bot is stuck, open a manual feedstock PR (see fallback above).

**conda-forge build failed**

- Confirm the sdist sha256 matches PyPI.
- Check dependency or Python version constraints in the feedstock recipe.
