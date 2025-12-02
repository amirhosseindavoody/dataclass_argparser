#!/usr/bin/env bash

# Script to update version in pyproject.toml and pixi.toml based on current date
# Can be used standalone or as part of a pre-commit hook
#
# Usage:
#   ./scripts/update_version.sh           # Update to today's date (increments micro if same day)
#   ./scripts/update_version.sh --check   # Check if version matches today's date (exit 1 if not)
#
# CalVer format: YYYY.M.D.N (e.g., 2025.12.2.0, 2025.12.2.1 for multiple releases per day)

set -euo pipefail

# Get the project root directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
PYPROJECT_FILE="$PROJECT_ROOT/pyproject.toml"
PIXI_FILE="$PROJECT_ROOT/pixi.toml"

# Generate date-based version prefix (CalVer format: YYYY.M.D)
DATE_PREFIX="$(date +%Y.%-m.%-d)"

# Get current version from pyproject.toml
CURRENT_VERSION=$(grep '^version = ' "$PYPROJECT_FILE" | sed 's/version = "\(.*\)"/\1/')

# Extract the date part and micro version from current version
# Expected format: YYYY.M.D.N or YYYY.M.D (legacy, treated as .0)
if [[ "$CURRENT_VERSION" =~ ^([0-9]+\.[0-9]+\.[0-9]+)\.([0-9]+)$ ]]; then
    CURRENT_DATE_PREFIX="${BASH_REMATCH[1]}"
    CURRENT_MICRO="${BASH_REMATCH[2]}"
elif [[ "$CURRENT_VERSION" =~ ^([0-9]+\.[0-9]+\.[0-9]+)$ ]]; then
    CURRENT_DATE_PREFIX="${BASH_REMATCH[1]}"
    CURRENT_MICRO="-1" # Will become 0 when incremented
else
    # Non-CalVer format (e.g., 1.0.0), start fresh
    CURRENT_DATE_PREFIX=""
    CURRENT_MICRO="-1"
fi

# Determine new version
if [[ "$CURRENT_DATE_PREFIX" == "$DATE_PREFIX" ]]; then
    # Same day, increment micro version
    NEW_MICRO=$((CURRENT_MICRO + 1))
    NEW_VERSION="${DATE_PREFIX}.${NEW_MICRO}"
else
    # New day, start at .0
    NEW_VERSION="${DATE_PREFIX}.0"
fi

if [[ "${1:-}" == "--check" ]]; then
    # Check mode: verify version is from today
    if [[ "$CURRENT_DATE_PREFIX" == "$DATE_PREFIX" ]]; then
        echo "Version is up to date: $CURRENT_VERSION"
        exit 0
    else
        echo "Version mismatch: current=$CURRENT_VERSION, expected date prefix=$DATE_PREFIX"
        exit 1
    fi
fi

# Update mode
if [[ "$CURRENT_VERSION" == "$NEW_VERSION" ]]; then
    echo "Version already up to date: $CURRENT_VERSION"
    exit 0
fi

echo "Updating version: $CURRENT_VERSION -> $NEW_VERSION"

# Update version in pyproject.toml
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    sed -i '' "s/^version = \".*\"/version = \"$NEW_VERSION\"/" "$PYPROJECT_FILE"
    # Update version in pixi.toml [package] section (after the [package] header)
    sed -i '' "/^\[package\]$/,/^\[.*\]$/{s/^version = \".*\"/version = \"$NEW_VERSION\"/;}" "$PIXI_FILE"
else
    # Linux
    sed -i "s/^version = \".*\"/version = \"$NEW_VERSION\"/" "$PYPROJECT_FILE"
    # Update version in pixi.toml [package] section (after the [package] header)
    sed -i "/^\[package\]$/,/^\[.*\]$/{s/^version = \".*\"/version = \"$NEW_VERSION\"/;}" "$PIXI_FILE"
fi

# Install the latest version of the package to reflect changes in the pixi.lock file.
pixi install

echo "Updated pyproject.toml version to $NEW_VERSION"
echo "Updated pixi.toml [package] version to $NEW_VERSION"
