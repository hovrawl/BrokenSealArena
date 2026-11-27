# Building on Windows with MSYS2 (no WSL). Sourced by scripts/build.sh and
# scripts/build-native.sh when they run in an MSYS2 shell. See docs/BUILDING.md.
#
# Upstream's build is written for Linux and macOS. Under MSYS2 three kinds of
# program are built, each with the compiler that suits it:
#   * upstream's host tools (tools/ags-*): UCRT64 GCC, a native Windows
#     compiler, with compat.h force-included for the POSIX calls they make and
#     binary-mode stdio (binmode.o), as on Linux;
#   * the matched compilers (make bootstrap: GCC 2.95, GAS 2.10, libgcc): the
#     MSYS GCC, whose POSIX layer their 2000-era sources need, with
#     include/stab.h and two libiberty switches;
#   * the native port (port/Makefile): MINGW32 GCC, 32-bit Windows.
# Upstream's files are not changed: everything is make variables and PATH.

BSA_MSYS2="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

bsa_is_msys2() {
  case "$(uname -s)" in MINGW*|MSYS*|UCRT*|CLANG*) return 0 ;; esac
  return 1
}

# Git: no CRLF. Symbolic links (upstream's compiler sources have two) must be
# real Windows links, which need Developer Mode or an administrator shell, and
# a target that already exists: so the clone writes them as text files, and
# bsa_msys2_links makes them links afterwards.
export MSYS="winsymlinks:nativestrict${MSYS:+ $MSYS}"
BSA_GIT_CONFIG=(-c core.symlinks=false -c core.autocrlf=false)

# Re-checks out every symbolic link of a repository (DIR) as a real link.
bsa_msys2_links() {
  local dir="$1" link
  git -C "$dir" config core.symlinks true
  git -C "$dir" ls-files -s | awk '$1 == "120000" {print $4}' | while read -r link; do
    rm -f "$dir/$link"
    git -C "$dir" checkout -- "$link"
  done
  [ -z "$(git -C "$dir" ls-files -s | awk '$1 == "120000"' | head -n 1)" ] ||
    [ -L "$dir/$(git -C "$dir" ls-files -s | awk '$1 == "120000" {print $4; exit}')" ] || {
      echo "Could not make symbolic links in $dir: turn on Windows Developer Mode (docs/BUILDING.md)." >&2; return 1; }
}

# bin/sha256sum first (upstream's source pins hash the Linux listing format),
# then the MSYS tools (make, the POSIX cc), then UCRT64's (arm-none-eabi
# binutils, libpng-config).
export PATH="$BSA_MSYS2/bin:/usr/bin:/ucrt64/bin:$PATH"
PYTHON=/ucrt64/bin/python3   # has Pillow, for the sprite generators

# For upstream's tools/Makefile only: the compiler build (alchemy-gcc) reads
# HOST_CC and HOST_CFLAGS too, as its own, so these must not reach it.
BSA_TOOLS_VARS=(
  HOST_CC=/ucrt64/bin/gcc
  "HOST_CFLAGS=-O2 -include $BSA_MSYS2/compat.h"
  HOST_LDFLAGS=/ucrt64/lib/binmode.o
  LIBPNG_CONFIG=/ucrt64/bin/libpng-config
)
# For everything else (make bootstrap, make tbs-en): the POSIX cc. The tools
# are built first by bsa_msys2_tools, so these makes find them up to date.
BSA_MAKE_VARS=(
  "CC=cc -DHAVE_SYS_ERRLIST -DHAVE_SYS_NERR -idirafter $BSA_MSYS2/include"
)

# make looks for tools/out/ags-graphics; MinGW GCC writes ags-graphics.exe.
# A copy under the plain name (made by a Windows program: the MSYS layer
# would say the plain name already exists) lets make see the tool.
bsa_msys2_tool_names() {
  "$PYTHON" - "$1/tools/out" <<'PY'
import glob, os, shutil, sys
for exe in glob.glob(os.path.join(sys.argv[1], 'ags-*.exe')):
    plain = exe[:-4]
    if not os.path.exists(plain) or os.path.getmtime(plain) < os.path.getmtime(exe):
        shutil.copy2(exe, plain)
PY
}

# Upstream's host tools, before anything asks for them.
bsa_msys2_tools() {
  make -C "$1" -j"$2" -f tools/Makefile "${BSA_TOOLS_VARS[@]}"
  bsa_msys2_tool_names "$1"
}
