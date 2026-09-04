#!/bin/bash
# Build manylinux wheels for hunspell versions 1.7.0 through 1.7.3.
# The hunspell version is embedded in the package version, so it appears in
# the wheel filename, e.g.:
#   cyhunspell-2.0.6.172-cp310-cp310-manylinux_2_28_x86_64.whl
#                    ^^^
#                    hunspell 1.7.2 (dots removed)
#
# Usage:
#   ./build_all_hunspell_versions.sh              # Linux (default)
#   ./build_all_hunspell_versions.sh macos        # macOS
#   ./build_all_hunspell_versions.sh linux x86_64 # specific arch
#
# Control the version format (see setup.py's version() for why this exists -
# some package feeds, e.g. Azure Artifacts, don't reliably serve PEP 440
# local versions):
#   HUNSPELL_VERSION_FORMAT=local ./build_all_hunspell_versions.sh

set -euo pipefail

if ! python -c "import cibuildwheel" >/dev/null 2>&1; then
    echo "error: cibuildwheel is not importable by 'python' ($(command -v python || echo 'not found'))." >&2
    echo "Activate your virtualenv and install it first, e.g.:" >&2
    echo "  python -m venv .venv && source .venv/bin/activate && pip install cibuildwheel" >&2
    exit 1
fi

PLATFORM="${1:-linux}"
ARCHS="${2:-}"

HUNSPELL_VERSIONS="1.7.0 1.7.1 1.7.2 1.7.3"
HUNSPELL_VERSION_FORMAT="${HUNSPELL_VERSION_FORMAT:-release}"

for VERSION in $HUNSPELL_VERSIONS; do
    echo ""
    echo "========================================"
    echo "  Building with hunspell $VERSION"
    echo "========================================"

    ARCH_ARG=""
    if [ -n "$ARCHS" ]; then
        ARCH_ARG="--archs $ARCHS"
    fi

    # Pass HUNSPELL_VERSION and HUNSPELL_VERSION_FORMAT explicitly into the
    # cibuildwheel build environment. CIBW_ENVIRONMENT_LINUX/MACOS overrides
    # the pyproject.toml environment section, so CC and CXX are repeated
    # here for Linux.
    if [ "$PLATFORM" = "linux" ]; then
        export CIBW_ENVIRONMENT_LINUX="CC=/usr/bin/gcc CXX=/usr/bin/g++ HUNSPELL_VERSION=$VERSION HUNSPELL_VERSION_FORMAT=$HUNSPELL_VERSION_FORMAT"
    elif [ "$PLATFORM" = "macos" ]; then
        export CIBW_ENVIRONMENT_MACOS="HUNSPELL_VERSION=$VERSION HUNSPELL_VERSION_FORMAT=$HUNSPELL_VERSION_FORMAT"
    fi

    HUNSPELL_VERSION=$VERSION HUNSPELL_VERSION_FORMAT=$HUNSPELL_VERSION_FORMAT python -m cibuildwheel --platform "$PLATFORM" $ARCH_ARG
done

unset CIBW_ENVIRONMENT_LINUX CIBW_ENVIRONMENT_MACOS 2>/dev/null || true

echo ""
echo "All versions built. Wheels are in wheelhouse/:"
ls wheelhouse/*.whl 2>/dev/null | sort || echo "(none found)"
