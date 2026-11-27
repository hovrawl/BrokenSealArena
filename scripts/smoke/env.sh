# Shared by the smoke runners (run.sh, link.sh, link-run.sh).
# T: where the smoke scripts' absolute /tmp paths (shot /tmp/shots/NAME.png,
# save /tmp/...) land. On Linux that is /tmp. Under MSYS2 (Windows) the
# drivers are Windows programs, for which /tmp/shots means \tmp\shots on the
# current drive: C:\tmp, which MSYS2 calls /c/tmp.
# SMOKE_CC: the compiler for the drivers (libmgba and libpng); PYTHON: one
# with Pillow, for the contact sheets.
T=/tmp
SMOKE_CC=gcc
PYTHON=python3
case "$(uname -s)" in
  MINGW*|MSYS*|UCRT*|CLANG*)
    T=/c/tmp
    export PATH="/ucrt64/bin:$PATH"
    SMOKE_CC=/ucrt64/bin/gcc
    PYTHON=/ucrt64/bin/python3 ;;
esac

# Windows looks for a program's DLLs in its own folder, then in System32, and
# only then on PATH. A DLL that some other program installed into System32
# under the same name as a UCRT64 one (seen: libcrypto-4-x64.dll, an older
# OpenSSL) wins and the driver will not start (entry point not found). Copy
# such DLLs beside the driver, where they are found first.
smoke_own_dlls() {
  case "$(uname -s)" in MINGW*|MSYS*|UCRT*|CLANG*) ;; *) return 0 ;; esac
  local exe="$1" dll
  for dll in $(ldd "$exe" 2>/dev/null | awk '{print $1}'); do
    if [ -f "/ucrt64/bin/$dll" ] && [ -f "/c/Windows/System32/$dll" ]; then
      cp -u "/ucrt64/bin/$dll" "$(dirname "$exe")/"
    fi
  done
}
