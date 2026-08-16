#!/usr/bin/env bash
set -euo pipefail

# Build upstream llama.cpp with AMD HIP/ROCm support for Radeon GPUs.
# Defaults target RX 6900 XT / RDNA2 (gfx1030). Override AMDGPU_TARGETS
# for RDNA3/RDNA4 cards, for example gfx1100 or gfx1201 when your ROCm
# toolchain supports it.

LLAMA_CPP_DIR="${LLAMA_CPP_DIR:-$HOME/llama.cpp}"
LLAMA_CPP_REPO="${LLAMA_CPP_REPO:-https://github.com/ggml-org/llama.cpp.git}"
# Leave this unset to follow the upstream repository's advertised default
# branch. llama.cpp currently uses master, but hard-coding that would recreate
# the same failure if the upstream default changes again.
LLAMA_CPP_REF="${LLAMA_CPP_REF:-}"
AMDGPU_TARGETS="${AMDGPU_TARGETS:-gfx1030}"
ROCM_PATH="${ROCM_PATH:-/opt/rocm}"
INSTALL_PREFIX="${INSTALL_PREFIX:-}"
JOBS="${JOBS:-12}"
FRESH=0

need() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "Missing required command: $1" >&2
    exit 1
  }
}

usage() {
  cat <<'USAGE'
Usage: scripts/update-llama.sh [--fresh] [--ref <git-ref>] [--dir <path>] [--install-prefix <path>] [--amdgpu-targets <list>]

Environment overrides:
  LLAMA_CPP_DIR     source/build directory, default ~/llama.cpp
  LLAMA_CPP_REPO    llama.cpp remote, default ggml-org/llama.cpp
  LLAMA_CPP_REF     commit/ref to checkout; defaults to the upstream default branch
  AMDGPU_TARGETS    HIP targets, default gfx1030 for RX 6900 XT
  ROCM_PATH         ROCm root, default /opt/rocm
  JOBS              build jobs, default 12
  INSTALL_PREFIX    optional directory for binary symlinks

Examples:
  AMDGPU_TARGETS=gfx1030 scripts/update-llama.sh
  AMDGPU_TARGETS=gfx1201 scripts/update-llama.sh --ref main
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --fresh)
      FRESH=1
      shift
      ;;
    --ref)
      LLAMA_CPP_REF="$2"
      shift 2
      ;;
    --dir)
      LLAMA_CPP_DIR="$2"
      shift 2
      ;;
    --install-prefix)
      INSTALL_PREFIX="$2"
      shift 2
      ;;
    --amdgpu-targets)
      AMDGPU_TARGETS="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

need git
need cmake

export PATH="$ROCM_PATH/bin:$ROCM_PATH/llvm/bin:$PATH"

if [[ "$FRESH" -eq 1 && -d "$LLAMA_CPP_DIR" ]]; then
  trash_parent="${LLAMA_CPP_DIR%/*}/.trash"
  mkdir -p "$trash_parent"
  mv "$LLAMA_CPP_DIR" "$trash_parent/llama.cpp.$(date +%Y%m%d-%H%M%S)"
fi

if [[ ! -d "$LLAMA_CPP_DIR/.git" ]]; then
  git clone "$LLAMA_CPP_REPO" "$LLAMA_CPP_DIR"
else
  git -C "$LLAMA_CPP_DIR" remote set-url origin "$LLAMA_CPP_REPO"
fi

git -C "$LLAMA_CPP_DIR" fetch --tags origin

if [[ -z "$LLAMA_CPP_REF" ]]; then
  LLAMA_CPP_REF="$(git -C "$LLAMA_CPP_DIR" symbolic-ref --quiet --short refs/remotes/origin/HEAD || true)"
  if [[ -z "$LLAMA_CPP_REF" ]]; then
    echo "Could not determine the default branch from origin/HEAD; pass --ref explicitly." >&2
    exit 1
  fi
fi

git -C "$LLAMA_CPP_DIR" checkout --detach "$LLAMA_CPP_REF"

echo "Building llama.cpp with GGML_HIP=ON AMDGPU_TARGETS=$AMDGPU_TARGETS"

cmake -S "$LLAMA_CPP_DIR" -B "$LLAMA_CPP_DIR/build" \
  -DGGML_HIP=ON \
  -DGGML_VULKAN=OFF \
  -DGGML_HIP_NO_VMM=ON \
  -DAMDGPU_TARGETS="$AMDGPU_TARGETS" \
  -DCMAKE_BUILD_TYPE=Release \
  -DLLAMA_CURL=OFF

cmake --build "$LLAMA_CPP_DIR/build" --config Release --clean-first -j "$JOBS" \
  --target llama-server \
  --target llama-fit-params

if [[ -n "$INSTALL_PREFIX" ]]; then
  mkdir -p "$INSTALL_PREFIX"
  ln -sf "$LLAMA_CPP_DIR/build/bin/llama-server" "$INSTALL_PREFIX/llama-server"
  ln -sf "$LLAMA_CPP_DIR/build/bin/llama-fit-params" "$INSTALL_PREFIX/llama-fit-params"
fi

"$LLAMA_CPP_DIR/build/bin/llama-server" --version 2>&1 | head -1
"$LLAMA_CPP_DIR/build/bin/llama-fit-params" --version 2>&1 | head -1
