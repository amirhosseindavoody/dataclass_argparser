#!/usr/bin/env bash

set -euo pipefail

# Get the project root directory (where this script is located)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYPROJECT_FILE="$SCRIPT_DIR/pyproject.toml"

# Update version using shared script
"$SCRIPT_DIR/scripts/update_version.sh"

# Get the new version for tagging
NEW_VERSION=$(grep '^version = ' "$PYPROJECT_FILE" | sed 's/version = "\(.*\)"/\1/')
TAG_NAME="v$NEW_VERSION"

# Commit the version change
git add "$PYPROJECT_FILE" "$SCRIPT_DIR/pixi.toml" "$SCRIPT_DIR/pixi.lock"
git commit -m "Bump version to $NEW_VERSION" || echo "No changes to commit (version already up to date)"

echo "Creating release tag: $TAG_NAME"

# Check if tag exists and delete it if it does
if git tag -l "$TAG_NAME" | grep -q "$TAG_NAME"; then
    echo "Tag $TAG_NAME already exists. Removing it..."
    git tag -d "$TAG_NAME"
    # Also delete from remote if it exists
    git push origin ":refs/tags/$TAG_NAME" 2>/dev/null || true
fi

# Create and push the new tag
git tag "$TAG_NAME"
git push origin "$TAG_NAME"

# Create/update the 'latest' tag to point to this release
echo "Creating/updating 'latest' tag..."
# Remove existing 'latest' tag if it exists
if git tag -l "latest" | grep -q "latest"; then
    git tag -d "latest"
    git push origin ":refs/tags/latest" 2>/dev/null || true
fi

# Create new 'latest' tag pointing to the same commit as the dated tag
git tag "latest"
git push origin "latest"

# Create GitHub release using gh CLI
echo "Creating GitHub release..."
gh release create "$TAG_NAME" \
    --title "Release $TAG_NAME" \
    --notes "Automated release for $(date +%Y-%m-%d)" \
    --latest

echo "Release $TAG_NAME created successfully!"
echo "Tag 'latest' now points to $TAG_NAME"

# Run local release script if it exists
LOCAL_RELEASE_SCRIPT="$SCRIPT_DIR/release_local.sh"
if [[ -f "$LOCAL_RELEASE_SCRIPT" ]]; then
    echo "Running local release script..."
    "$LOCAL_RELEASE_SCRIPT"
fi
