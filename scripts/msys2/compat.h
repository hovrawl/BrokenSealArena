/* Windows (MinGW) shims for upstream's host tools, force-included with
   -include: the POSIX behaviour they rely on. */
#ifdef _WIN32
#include <direct.h>
#include <io.h>
#include <stdio.h>
#include <sys/stat.h>
/* From windows.h, which is not included: it defines names (byte) the tools use. */
__declspec(dllimport) int __stdcall MoveFileExA(const char *, const char *, unsigned long);
/* mkdir takes no mode. */
#define mkdir(path, mode) _mkdir(path)
/* rename replaces an existing file, as POSIX rename does (the tools write a
   temporary sibling, then rename it over the output). */
static int bsa_rename(const char *from, const char *to) {
  return MoveFileExA(from, to, 1 /* MOVEFILE_REPLACE_EXISTING */) ? 0 : -1;
}
#define rename(from, to) bsa_rename(from, to)
#endif
