---
name: Pixi-agent
description: uses pixi for dependency management
---

# Pixi agent

This agent uses pixi package manager for managing the python environment.

The relevant github action is prefix-dev/setup-pixi.

Alternatively we can install pixi using `curl -fsSL https://pixi.sh/install.sh | sh` command.

The environment needs to be activated using `pixi shell` before running further commands.

Alternatively, it can prepend any command with `pixi run` to execute the command inside the pixi environment.
