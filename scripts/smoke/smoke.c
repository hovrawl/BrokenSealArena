/* Headless smoke test driver for the romhack, on libmgba.
 *
 *   smoke ROM.gba SCRIPT [SAVEDIR]
 *
 * SCRIPT is one command a line (# starts a comment):
 *   wait N            run N frames
 *   press KEYS N      hold KEYS for N frames, then release them
 *                     (A B S=select T=start R=right L=left U=up D=down
 *                      r=R shoulder l=L shoulder, e.g. "press AD 3")
 *   tap KEYS          press KEYS for 4 frames, then 20 frames of nothing
 *   shot FILE.png     write the screen, 240x160 scaled up 3 times
 *   peek HEXADDR N    print N bytes (1, 2 or 4) at the address, as a number
 *   poke HEXADDR N V  write V (decimal) as N bytes
 *   save FILE         write a savestate
 *   load FILE         load a savestate
 *
 * The ROM is copied to SAVEDIR (default: the script's directory) before it
 * runs, so the cartridge save (<rom>.sav) lands there, not next to the ROM.
 */
#include <mgba/core/core.h>
#include <mgba/core/config.h>
#include <mgba/core/serialize.h>
#include <mgba/gba/core.h>
#include <mgba-util/vfs.h>
#include <png.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define SCALE 3

static struct mCore *core;
static uint32_t *pixels;
static unsigned width, height;

static void runFrames(int n, uint32_t keys) {
  int i;
  core->setKeys(core, keys);
  for (i = 0; i < n; i++)
    core->runFrame(core);
}

static uint32_t parseKeys(const char *s) {
  uint32_t keys = 0;
  for (; *s && *s != '\n' && *s != ' '; s++) {
    switch (*s) {
    case 'A': keys |= 1 << 0; break;
    case 'B': keys |= 1 << 1; break;
    case 'S': keys |= 1 << 2; break;
    case 'T': keys |= 1 << 3; break;
    case 'R': keys |= 1 << 4; break;
    case 'L': keys |= 1 << 5; break;
    case 'U': keys |= 1 << 6; break;
    case 'D': keys |= 1 << 7; break;
    case 'r': keys |= 1 << 8; break;
    case 'l': keys |= 1 << 9; break;
    }
  }
  return keys;
}

static int writePng(const char *path) {
  FILE *f = fopen(path, "wb");
  png_structp png;
  png_infop info;
  unsigned x, y, sx, sy;
  png_bytep row;

  if (!f)
    return -1;
  png = png_create_write_struct(PNG_LIBPNG_VER_STRING, NULL, NULL, NULL);
  info = png_create_info_struct(png);
  if (setjmp(png_jmpbuf(png))) {
    fclose(f);
    return -1;
  }
  png_init_io(png, f);
  png_set_IHDR(png, info, width * SCALE, height * SCALE, 8, PNG_COLOR_TYPE_RGB,
               PNG_INTERLACE_NONE, PNG_COMPRESSION_TYPE_DEFAULT,
               PNG_FILTER_TYPE_DEFAULT);
  png_write_info(png, info);
  row = malloc(width * SCALE * 3);
  for (y = 0; y < height; y++) {
    for (x = 0; x < width; x++) {
      uint32_t c = pixels[y * width + x];
      for (sx = 0; sx < SCALE; sx++) {
        row[(x * SCALE + sx) * 3 + 0] = c & 0xff;
        row[(x * SCALE + sx) * 3 + 1] = (c >> 8) & 0xff;
        row[(x * SCALE + sx) * 3 + 2] = (c >> 16) & 0xff;
      }
    }
    for (sy = 0; sy < SCALE; sy++)
      png_write_row(png, row);
  }
  free(row);
  png_write_end(png, NULL);
  png_destroy_write_struct(&png, &info);
  fclose(f);
  return 0;
}

static int copyFile(const char *from, const char *to) {
  FILE *a = fopen(from, "rb");
  FILE *b = fopen(to, "wb");
  char buf[65536];
  size_t n;

  if (!a || !b)
    return -1;
  while ((n = fread(buf, 1, sizeof buf, a)) > 0)
    fwrite(buf, 1, n, b);
  fclose(a);
  fclose(b);
  return 0;
}

static void runScript(const char *path, const char *dir) {
  char line[1024];
  FILE *script = fopen(path, "r");

  if (!script) {
    fprintf(stderr, "cannot read %s\n", path);
    exit(2);
  }
  while (fgets(line, sizeof line, script)) {
    char cmd[32] = "";
    char arg[900] = "";
    unsigned a, b;
    int n;

    if (line[0] == '#' || line[0] == '\n')
      continue;
    sscanf(line, "%31s %899s", cmd, arg);
    if (!strcmp(cmd, "include")) {
      char sub[1200];
      snprintf(sub, sizeof sub, "%s/%s", dir, arg);
      runScript(sub, dir);
    } else if (!strcmp(cmd, "wait")) {
      runFrames(atoi(arg), 0);
    } else if (!strcmp(cmd, "press")) {
      uint32_t keys = parseKeys(arg);
      const char *p = strchr(line + strlen(cmd) + 1, ' ');
      runFrames(p ? atoi(p) : 4, keys);
      runFrames(1, 0);
    } else if (!strcmp(cmd, "mash")) {
      /* mash KEYS N: tap the keys N times, 4 frames down and 20 up */
      const char *p = strchr(line + strlen(cmd) + 1, ' ');
      int times = p ? atoi(p) : 1;
      int k;

      for (k = 0; k < times; k++) {
        runFrames(4, parseKeys(arg));
        runFrames(20, 0);
      }
    } else if (!strcmp(cmd, "tap")) {
      runFrames(4, parseKeys(arg));
      runFrames(20, 0);
    } else if (!strcmp(cmd, "shot")) {
      if (writePng(arg) != 0)
        fprintf(stderr, "cannot write %s\n", arg);
    } else if (!strcmp(cmd, "peek")) {
      n = 0;
      sscanf(line, "%*s %x %d", &a, &n);
      if (n == 4)
        printf("%08x: %u\n", a, core->busRead32(core, a));
      else if (n == 2)
        printf("%08x: %u\n", a, core->busRead16(core, a));
      else
        printf("%08x: %u\n", a, core->busRead8(core, a));
    } else if (!strcmp(cmd, "poke")) {
      sscanf(line, "%*s %x %d %u", &a, &n, &b);
      if (n == 4)
        core->busWrite32(core, a, b);
      else if (n == 2)
        core->busWrite16(core, a, b);
      else
        core->busWrite8(core, a, b);
    } else if (!strcmp(cmd, "save")) {
      struct VFile *vf = VFileOpen(arg, O_CREAT | O_TRUNC | O_RDWR);
      if (vf) {
        mCoreSaveStateNamed(core, vf, SAVESTATE_SAVEDATA | SAVESTATE_SCREENSHOT);
        vf->close(vf);
      }
    } else if (!strcmp(cmd, "load")) {
      struct VFile *vf = VFileOpen(arg, O_RDONLY);
      if (vf) {
        mCoreLoadStateNamed(core, vf, SAVESTATE_SAVEDATA);
        vf->close(vf);
      }
    } else {
      fprintf(stderr, "unknown command: %s", line);
    }
    fflush(stdout);
  }
  fclose(script);
}

int main(int argc, char **argv) {
  char romCopy[1024];
  const char *saveDir;

  if (argc < 3) {
    fprintf(stderr, "usage: smoke ROM SCRIPT [SAVEDIR]\n");
    return 2;
  }
  saveDir = argc > 3 ? argv[3] : ".";
  snprintf(romCopy, sizeof romCopy, "%s/smoke.gba", saveDir);
  if (copyFile(argv[1], romCopy) != 0) {
    fprintf(stderr, "cannot copy the ROM to %s\n", romCopy);
    return 2;
  }
  core = mCoreFind(romCopy);
  if (!core) {
    fprintf(stderr, "no core for %s\n", romCopy);
    return 2;
  }
  core->init(core);
  mCoreInitConfig(core, NULL);
  core->desiredVideoDimensions(core, &width, &height);
  pixels = calloc(width * height, sizeof(uint32_t));
  core->setVideoBuffer(core, pixels, width);
  if (!mCoreLoadFile(core, romCopy)) {
    fprintf(stderr, "cannot load %s\n", romCopy);
    return 2;
  }
  mCoreAutoloadSave(core);
  core->reset(core);

  {
    char dir[1024];
    char *slash;

    snprintf(dir, sizeof dir, "%s", argv[2]);
    slash = strrchr(dir, 47);
    if (slash)
      *slash = 0;
    else
      strcpy(dir, ".");
    runScript(argv[2], dir);
  }
  core->deinit(core);
  return 0;
}
