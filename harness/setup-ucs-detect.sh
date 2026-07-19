#!/usr/bin/env bash
# Fetch ucs-detect at a pinned commit, apply this repository's patches, and install it
# into a private virtualenv.
#
# The measurement tool is pinned rather than tracked, because a comparison is only
# meaningful if every terminal is measured by the same oracle.  Upstream changing an
# expected width between two runs would silently reshuffle the table.
#
# The patch in patches/ corrects the VS15 expectation; see that file and README.md.
set -euo pipefail

UPSTREAM="https://github.com/jquast/ucs-detect.git"
PINNED_COMMIT="ea4510a4bc6e99df2af500d454ac34f66c0245b3"

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CHECKOUT="$REPO_ROOT/.ucs-detect"
VENV="$CHECKOUT/.venv"

if [ ! -d "$CHECKOUT/.git" ]; then
    echo ">>> cloning ucs-detect"
    git clone --quiet "$UPSTREAM" "$CHECKOUT"
fi

echo ">>> checking out pinned commit $PINNED_COMMIT"
git -C "$CHECKOUT" fetch --quiet origin
git -C "$CHECKOUT" checkout --quiet --detach "$PINNED_COMMIT"

echo ">>> applying patches"
for patch in "$REPO_ROOT"/patches/*.patch; do
    [ -e "$patch" ] || continue
    echo "    $(basename "$patch")"
    git -C "$CHECKOUT" apply --3way "$patch"
done

echo ">>> installing into $VENV"
python3 -m venv "$VENV"
"$VENV/bin/pip" install --quiet --upgrade pip
"$VENV/bin/pip" install --quiet -e "$CHECKOUT"

echo ">>> ready: $VENV/bin/ucs-detect"
"$VENV/bin/ucs-detect" --help > /dev/null && echo ">>> smoke test passed"
