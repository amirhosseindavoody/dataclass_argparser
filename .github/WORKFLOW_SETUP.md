# GitHub Actions Workflow Setup

This repository uses [pixi](https://prefix.dev/docs/pixi/overview) for dependency management and the official [setup-pixi](https://github.com/marketplace/actions/setup-pixi) GitHub Action for CI/CD.

## Workflow Overview

The CI workflow (`.github/workflows/ci.yml`) consists of three main jobs:

### 1. Test Job
- **Platforms**: Ubuntu, macOS, and Windows (via matrix strategy)
- **Actions**:
  - Runs the full test suite with `pixi run test-verbose`
  - Generates test coverage on Ubuntu only
  - Uploads coverage to Codecov (requires `CODECOV_TOKEN` secret)
- **Caching**: Pixi cache is enabled for faster dependency installation

### 2. Build Job
- **Platform**: Ubuntu only
- **Actions**:
  - Builds the package using pixi-build: `pixi run build`
  - Builds PyPI package: `pixi run build-pypi`
  - Uploads both build artifacts for download
- **Dependencies**: Runs only after tests pass

### 3. Examples Job
- **Platform**: Ubuntu only
- **Actions**:
  - Runs all example scripts to ensure they work: `pixi run test-all`
- **Dependencies**: Runs only after tests pass

## Setup Details

### Pixi Action Configuration
```yaml
- name: Setup Pixi
  uses: prefix-dev/setup-pixi@v0.8.1
  with:
    pixi-version: v0.34.0
    cache: true
```

Key features:
- **Version pinning**: Uses pixi v0.34.0 for consistency
- **Caching**: Enabled to speed up dependency installation across runs
- **Cross-platform**: Works on Ubuntu, macOS, and Windows

### Triggers
The workflow runs on:
- Push to `main` branch
- Pull requests to `main` branch
- Manual dispatch via GitHub UI

## GitHub Copilot Agent Configuration

The repository includes `.github/copilot-agents.yml` which configures the Copilot coding agent environment:

- Automatically installs pixi when the agent starts working
- Installs project dependencies with `pixi install`
- Validates the environment by running tests

This ensures that Copilot agents have a properly configured development environment.

## Required Secrets

### Optional Secrets
- `CODECOV_TOKEN`: Required only if you want to upload coverage reports to Codecov
  - Set this in your repository settings: Settings → Secrets and variables → Actions
  - Get your token from https://codecov.io/

### Not Required
- No authentication tokens needed for pixi setup on public repositories
- The `PREFIX_DEV_TOKEN` is only needed for private repositories or authenticated access

## Customization

### Adding More Test Platforms
To test on additional platforms, modify the matrix in `.github/workflows/ci.yml`:
```yaml
matrix:
  os: [ubuntu-latest, macos-latest, windows-latest, macos-13]
```

### Changing Pixi Version
Update the `pixi-version` in the workflow file:
```yaml
with:
  pixi-version: v0.35.0  # Update to desired version
```

### Adding More Jobs
Follow the pattern of existing jobs and add a new job section:
```yaml
my-new-job:
  name: My New Job
  runs-on: ubuntu-latest
  needs: test  # Run after tests pass
  steps:
    - uses: actions/checkout@v4
    - uses: prefix-dev/setup-pixi@v0.8.1
      with:
        pixi-version: v0.34.0
        cache: true
    - run: pixi run my-task
```

## Resources

- [Pixi Documentation](https://prefix.dev/docs/pixi/overview)
- [setup-pixi Action](https://github.com/marketplace/actions/setup-pixi)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Customizing Copilot Agent Environment](https://docs.github.com/en/copilot/how-tos/use-copilot-agents/coding-agent/customize-the-agent-environment)
