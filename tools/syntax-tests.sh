#!/usr/bin/env bash
# Run Sublime Text syntax tests locally. The syntax_tests binary is x64
# Linux only, so it runs in a container (emulated on Apple silicon).
set -euo pipefail

BUILD="${ST_BUILD:-4215}"
IMAGE="debian:stable-slim@sha256:5bc3287b25407c965a30f38e32603dc253a3869e1b12a21ac09bfc27fd8b13ce"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CACHE="$HOME/.cache/st-syntax-tests-$BUILD"

if [ ! -x "$CACHE/syntax_tests" ]; then
    mkdir -p "$CACHE"
    curl -fsSL "https://download.sublimetext.com/st_syntax_tests_build_${BUILD}_x64.tar.xz" \
        | tar -xJ -C "$CACHE" --strip-components=1
fi

PKG="$CACHE/Data/Packages/iRules"
rm -rf "$PKG"
mkdir -p "$PKG"
cp "$ROOT"/iRule.sublime-syntax "$ROOT"/*.tmPreferences "$PKG"/
cp "$ROOT"/tests/syntax/syntax_test_* "$PKG"/

docker run --rm --platform linux/amd64 -v "$CACHE":/st -w /st "$IMAGE" ./syntax_tests
