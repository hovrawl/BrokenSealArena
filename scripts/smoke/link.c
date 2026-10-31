/* Two-console smoke driver: two copies of the ROM linked by mGBA's own lockstep
 * link (what its multiplayer windows use), each running a smoke script.
 *
 *   link ROM SCRIPT0 SCRIPT1 [SAVEDIR]
 *
 * The scripts use the commands of smoke.c (wait, press, tap, mash, shot, peek,
 * poke, include; not save, load or reset). Each console runs in its own
 * mCoreThread, unthrottled; the script is turned into a timeline of frames
 * first, and each console follows its own. The two are kept roughly level with a
 * loose frame barrier (the lockstep keeps them level while a transfer runs).
 * Console 0 is the link's master. A watchdog ends the run after 240 seconds.
 *
 * The lockstep callbacks follow mGBA's Qt MultiplayerController: the master
 * sleeps in wait() until the slaves signal(); slaves sleep when their posted
 * cycles run out and are woken when the master posts more.
 */
/* The library is built with scripting, which adds a field to struct mCoreThread:
 * without this define our copy of the struct is too short and the library
 * overwrites the next field. Build with -DENABLE_SCRIPTING. */
#ifndef ENABLE_SCRIPTING
#error "build link.c with -DENABLE_SCRIPTING (the struct mCoreThread layout)"
#endif
#include <mgba/core/core.h>
#include <mgba/core/config.h>
#include <mgba/core/lockstep.h>
#include <mgba/core/thread.h>
#include <mgba/gba/core.h>
#include <mgba/internal/gba/gba.h>
#include <mgba/internal/gba/sio.h>
#include <mgba/internal/gba/sio/lockstep.h>
#include <png.h>
#include <pthread.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>

#define SCALE 3
#define PLAYERS 2
#define MAX_EVENTS 20000
#define BARRIER_SLACK 2

enum EvType { EV_KEYS, EV_SHOT, EV_PEEK, EV_POKE, EV_PEEKP, EV_PEEKPP, EV_PEEKP3 };

struct Event {
  int frame;
  enum EvType type;
  uint32_t keys;
  char path[256];
  unsigned addr, value;
  int size;
};

struct Player {
  struct mCore *core;
  struct mCoreThread thread;
  uint32_t *pixels;
  unsigned width, height;
  struct Event *events;
  int eventCount, nextEvent;
  int totalFrames;
  volatile int frames;
  volatile int done;
  /* lockstep bookkeeping, as the Qt controller keeps per player */
  int awake;
  int32_t cyclesPosted;
  unsigned waitMask;
  struct GBASIOLockstepNode node;
  int id;
};

static struct Player players[PLAYERS];
static struct GBASIOLockstep coordinator;
static pthread_mutex_t lockstepLock;
static pthread_mutex_t frameLock = PTHREAD_MUTEX_INITIALIZER;
static pthread_cond_t frameCond = PTHREAD_COND_INITIALIZER;
static pthread_mutex_t printLock = PTHREAD_MUTEX_INITIALIZER;

/* ----------------------------------------------------------------- script */

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

static void addEvent(struct Player *p, int frame, enum EvType type, uint32_t keys,
                     const char *path, unsigned addr, int size, unsigned value) {
  struct Event *e;
  if (p->eventCount >= MAX_EVENTS) {
    fprintf(stderr, "too many events\n");
    exit(2);
  }
  e = &p->events[p->eventCount++];
  e->frame = frame;
  e->type = type;
  e->keys = keys;
  e->addr = addr;
  e->size = size;
  e->value = value;
  snprintf(e->path, sizeof e->path, "%s", path ? path : "");
}

/* Turns a script into events, as smoke.c's runFrames would have run it. */
static void compile(struct Player *p, const char *path, const char *dir, int *frame) {
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

    if (line[0] == '#' || line[0] == '\n' || line[0] == '\r')
      continue;
    sscanf(line, "%31s %899s", cmd, arg);
    if (!strcmp(cmd, "include")) {
      char sub[1200];
      snprintf(sub, sizeof sub, "%s/%s", dir, arg);
      compile(p, sub, dir, frame);
    } else if (!strcmp(cmd, "wait")) {
      addEvent(p, *frame, EV_KEYS, 0, NULL, 0, 0, 0);
      *frame += atoi(arg);
    } else if (!strcmp(cmd, "press")) {
      const char *sp = strchr(line + strlen(cmd) + 1, ' ');
      int frames = sp ? atoi(sp) : 4;
      addEvent(p, *frame, EV_KEYS, parseKeys(arg), NULL, 0, 0, 0);
      *frame += frames;
      addEvent(p, *frame, EV_KEYS, 0, NULL, 0, 0, 0);
      *frame += 1;
    } else if (!strcmp(cmd, "mash")) {
      const char *sp = strchr(line + strlen(cmd) + 1, ' ');
      int times = sp ? atoi(sp) : 1, k;
      for (k = 0; k < times; k++) {
        addEvent(p, *frame, EV_KEYS, parseKeys(arg), NULL, 0, 0, 0);
        *frame += 4;
        addEvent(p, *frame, EV_KEYS, 0, NULL, 0, 0, 0);
        *frame += 20;
      }
    } else if (!strcmp(cmd, "tap")) {
      addEvent(p, *frame, EV_KEYS, parseKeys(arg), NULL, 0, 0, 0);
      *frame += 4;
      addEvent(p, *frame, EV_KEYS, 0, NULL, 0, 0, 0);
      *frame += 20;
    } else if (!strcmp(cmd, "shot")) {
      addEvent(p, *frame, EV_SHOT, 0, arg, 0, 0, 0);
    } else if (!strcmp(cmd, "peek")) {
      n = 0;
      sscanf(line, "%*s %x %d", &a, &n);
      addEvent(p, *frame, EV_PEEK, 0, NULL, a, n, 0);
    } else if (!strcmp(cmd, "peekp")) {
      /* peekp PTRADDR OFFSET SIZE: read the pointer at PTRADDR, then SIZE bytes at pointer+OFFSET */
      unsigned off = 0;
      n = 1;
      sscanf(line, "%*s %x %x %d", &a, &off, &n);
      addEvent(p, *frame, EV_PEEKP, 0, NULL, a, n, off);
    } else if (!strcmp(cmd, "peekpp")) {
      /* peekpp PTRADDR OFF1 OFF2 SIZE: p = [PTRADDR]; q = [p + OFF1]; read SIZE at q + OFF2 */
      unsigned off1 = 0, off2 = 0;
      n = 1;
      sscanf(line, "%*s %x %x %x %d", &a, &off1, &off2, &n);
      addEvent(p, *frame, EV_PEEKPP, off2, NULL, a, n, off1);
    } else if (!strcmp(cmd, "peekp3")) {
      /* peekp3 PTRADDR OFF1 OFF2 OFF3 SIZE: p = [PTRADDR]; q = [p + OFF1]; r = [q + OFF2]; read SIZE at r + OFF3 */
      unsigned off1 = 0, off2 = 0, off3 = 0;
      char off3text[16];
      n = 1;
      sscanf(line, "%*s %x %x %x %x %d", &a, &off1, &off2, &off3, &n);
      snprintf(off3text, sizeof off3text, "%x", off3);
      addEvent(p, *frame, EV_PEEKP3, off2, off3text, a, n, off1);
    } else if (!strcmp(cmd, "poke")) {
      b = 0;
      sscanf(line, "%*s %x %d %u", &a, &n, &b);
      addEvent(p, *frame, EV_POKE, 0, NULL, a, n, b);
    } else {
      fprintf(stderr, "link: unsupported command: %s", line);
    }
  }
  fclose(script);
}

/* -------------------------------------------------------------------- png */

static int writePng(struct Player *p, const char *path) {
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
  png_set_IHDR(png, info, p->width * SCALE, p->height * SCALE, 8,
               PNG_COLOR_TYPE_RGB, PNG_INTERLACE_NONE,
               PNG_COMPRESSION_TYPE_DEFAULT, PNG_FILTER_TYPE_DEFAULT);
  png_write_info(png, info);
  row = malloc(p->width * SCALE * 3);
  for (y = 0; y < p->height; y++) {
    for (x = 0; x < p->width; x++) {
      uint32_t c = p->pixels[y * p->width + x];
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

/* --------------------------------------------------- per-frame, per thread */

static void applyEvents(struct Player *p, int frame) {
  while (p->nextEvent < p->eventCount && p->events[p->nextEvent].frame <= frame) {
    struct Event *e = &p->events[p->nextEvent++];
    switch (e->type) {
    case EV_KEYS:
      p->core->setKeys(p->core, e->keys);
      break;
    case EV_SHOT:
      if (writePng(p, e->path) != 0)
        fprintf(stderr, "P%d cannot write %s\n", p->id, e->path);
      break;
    case EV_PEEK:
      pthread_mutex_lock(&printLock);
      if (e->size == 4)
        printf("P%d f%d %08x: %u\n", p->id, frame, e->addr, p->core->busRead32(p->core, e->addr));
      else if (e->size == 2)
        printf("P%d f%d %08x: %u\n", p->id, frame, e->addr, p->core->busRead16(p->core, e->addr));
      else
        printf("P%d f%d %08x: %u\n", p->id, frame, e->addr, p->core->busRead8(p->core, e->addr));
      fflush(stdout);
      pthread_mutex_unlock(&printLock);
      break;
    case EV_PEEKP: {
      uint32_t base = p->core->busRead32(p->core, e->addr);
      uint32_t at = base + e->value;
      pthread_mutex_lock(&printLock);
      if (e->size == 4)
        printf("P%d f%d +%x = %08x: %u\n", p->id, frame, e->value, at,
               p->core->busRead32(p->core, at));
      else if (e->size == 2)
        printf("P%d f%d +%x = %08x: %u\n", p->id, frame, e->value, at,
               p->core->busRead16(p->core, at));
      else
        printf("P%d f%d +%x = %08x: %u\n", p->id, frame, e->value, at,
               p->core->busRead8(p->core, at));
      fflush(stdout);
      pthread_mutex_unlock(&printLock);
      break;
    }
    case EV_PEEKPP: {
      uint32_t first = p->core->busRead32(p->core, e->addr);
      uint32_t second = p->core->busRead32(p->core, first + e->value);
      uint32_t at = second + e->keys;
      uint32_t v = e->size == 4   ? p->core->busRead32(p->core, at)
                   : e->size == 2 ? p->core->busRead16(p->core, at)
                                  : p->core->busRead8(p->core, at);
      pthread_mutex_lock(&printLock);
      printf("P%d f%d pp +%x +%x = %08x: %u\n", p->id, frame, e->value, e->keys, at, v);
      fflush(stdout);
      pthread_mutex_unlock(&printLock);
      break;
    }
    case EV_PEEKP3: {
      uint32_t first = p->core->busRead32(p->core, e->addr);
      uint32_t second = p->core->busRead32(p->core, first + e->value);
      uint32_t third = p->core->busRead32(p->core, second + e->keys);
      unsigned off3 = (unsigned)strtoul(e->path, NULL, 16);
      uint32_t at = third + off3;
      uint32_t v = e->size == 4   ? p->core->busRead32(p->core, at)
                   : e->size == 2 ? p->core->busRead16(p->core, at)
                                  : p->core->busRead8(p->core, at);
      pthread_mutex_lock(&printLock);
      printf("P%d f%d p3 +%x +%x +%x = %08x: %u\n", p->id, frame, e->value, e->keys, off3, at, v);
      fflush(stdout);
      pthread_mutex_unlock(&printLock);
      break;
    }
    case EV_POKE:
      if (e->size == 4)
        p->core->busWrite32(p->core, e->addr, e->value);
      else if (e->size == 2)
        p->core->busWrite16(p->core, e->addr, e->value);
      else
        p->core->busWrite8(p->core, e->addr, e->value);
      break;
    }
  }
}

static void startCallback(struct mCoreThread *thread) {
  struct Player *p = thread->userData;
  applyEvents(p, 0);
}

static void frameCallback(struct mCoreThread *thread) {
  struct Player *p = thread->userData;
  struct Player *other = &players[1 - p->id];
  struct timespec until;
  int waited = 0;

  p->frames++;
  applyEvents(p, p->frames);
  if (p->frames >= p->totalFrames)
    p->done = 1;

  pthread_mutex_lock(&frameLock);
  pthread_cond_broadcast(&frameCond);
  /* Loose barrier: do not run more than BARRIER_SLACK frames ahead of the other
   * console, but never wait long (a console asleep in the lockstep cannot catch
   * up until this one runs). */
  while (!other->done && p->frames > other->frames + BARRIER_SLACK && waited < 50) {
    clock_gettime(CLOCK_REALTIME, &until);
    until.tv_nsec += 4 * 1000 * 1000;
    if (until.tv_nsec >= 1000000000L) {
      until.tv_sec++;
      until.tv_nsec -= 1000000000L;
    }
    pthread_cond_timedwait(&frameCond, &frameLock, &until);
    waited++;
  }
  pthread_mutex_unlock(&frameLock);
}

/* ---------------------------------------------------- lockstep callbacks */

static void lsLock(struct mLockstep *l) { (void)l; pthread_mutex_lock(&lockstepLock); }
static void lsUnlock(struct mLockstep *l) { (void)l; pthread_mutex_unlock(&lockstepLock); }

static bool lsSignal(struct mLockstep *l, unsigned mask) {
  struct Player *master = &players[0];
  (void)l;
  master->waitMask &= ~mask;
  if (!master->waitMask && !master->awake) {
    mCoreThreadStopWaiting(&master->thread);
    master->awake = 1;
  }
  return true;
}

static bool lsWait(struct mLockstep *l, unsigned mask) {
  struct Player *master = &players[0];
  (void)l;
  master->waitMask |= mask;
  if (master->waitMask && master->awake) {
    mCoreThreadWaitFromThread(&master->thread);
    master->awake = 0;
  }
  return true;
}

static void lsAddCycles(struct mLockstep *l, int id, int32_t cycles) {
  int i;
  (void)l;
  if (cycles < 0)
    abort();
  if (id == 0) {
    for (i = 1; i < PLAYERS; i++) {
      struct Player *s = &players[i];
      s->cyclesPosted += cycles;
      if (!s->awake && s->cyclesPosted > 0) {
        mCoreThreadStopWaiting(&s->thread);
        s->awake = 1;
      }
    }
  } else {
    struct Player *s = &players[id];
    s->cyclesPosted += cycles;
    if (!s->awake && s->cyclesPosted > 0) {
      mCoreThreadStopWaiting(&s->thread);
      s->awake = 1;
    }
  }
}

static int32_t lsUseCycles(struct mLockstep *l, int id, int32_t cycles) {
  struct Player *s = &players[id];
  (void)l;
  s->cyclesPosted -= cycles;
  if (s->cyclesPosted <= 0 && s->awake) {
    mCoreThreadWaitFromThread(&s->thread);
    s->awake = 0;
  }
  return s->cyclesPosted;
}

static int32_t lsUnusedCycles(struct mLockstep *l, int id) {
  (void)l;
  return players[id].cyclesPosted;
}

static void lsUnload(struct mLockstep *l, int id) {
  struct Player *master = &players[0];
  int i;
  (void)l;
  if (id) {
    players[id].cyclesPosted = 0;
    master->waitMask &= ~(1u << id);
    if (!master->waitMask && !master->awake) {
      mCoreThreadStopWaiting(&master->thread);
      master->awake = 1;
    }
  } else {
    for (i = 1; i < PLAYERS; i++) {
      if (!players[i].awake) {
        mCoreThreadStopWaiting(&players[i].thread);
        players[i].awake = 1;
      }
    }
  }
}

/* ------------------------------------------------------------------ main */

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

static void watchdog(int sig) {
  (void)sig;
  fprintf(stderr, "link: watchdog (240 s): P0 frame %d/%d awake %d cyc %d, P1 frame %d/%d awake %d cyc %d\n",
          players[0].frames, players[0].totalFrames, players[0].awake, players[0].cyclesPosted,
          players[1].frames, players[1].totalFrames, players[1].awake, players[1].cyclesPosted);
  _exit(3);
}

int main(int argc, char **argv) {
  const char *saveDir = argc > 4 ? argv[4] : ".";
  char dir[1024], rom[1100];
  char *slash;
  pthread_mutexattr_t attr;
  int i;

  if (argc < 4) {
    fprintf(stderr, "usage: link ROM SCRIPT0 SCRIPT1 [SAVEDIR]\n");
    return 2;
  }
  pthread_mutexattr_init(&attr);
  pthread_mutexattr_settype(&attr, PTHREAD_MUTEX_RECURSIVE);
  pthread_mutex_init(&lockstepLock, &attr);
  signal(SIGALRM, watchdog);
  alarm(240);

  mLockstepInit(&coordinator.d);
  coordinator.d.lock = lsLock;
  coordinator.d.unlock = lsUnlock;
  coordinator.d.signal = lsSignal;
  coordinator.d.wait = lsWait;
  coordinator.d.addCycles = lsAddCycles;
  coordinator.d.useCycles = lsUseCycles;
  coordinator.d.unusedCycles = lsUnusedCycles;
  coordinator.d.unload = lsUnload;
  GBASIOLockstepInit(&coordinator);

  for (i = 0; i < PLAYERS; i++) {
    struct Player *p = &players[i];
    int frame = 0;

    p->id = i;
    p->awake = 1;
    p->events = calloc(MAX_EVENTS, sizeof(struct Event));
    snprintf(dir, sizeof dir, "%s", argv[2 + i]);
    slash = strrchr(dir, '/');
    if (slash)
      *slash = 0;
    else
      strcpy(dir, ".");
    compile(p, argv[2 + i], dir, &frame);
    p->totalFrames = frame;

    snprintf(rom, sizeof rom, "%s/link%d.gba", saveDir, i);
    /* ROM1 names a different ROM for player 1, to link two builds. */
    if (copyFile((i == 1 && getenv("ROM1")) ? getenv("ROM1") : argv[1], rom) != 0) {
      fprintf(stderr, "cannot copy the ROM to %s\n", rom);
      return 2;
    }
    p->core = mCoreFind(rom);
    p->core->init(p->core);
    mCoreInitConfig(p->core, NULL);
    p->core->opts.audioSync = false;
    p->core->opts.videoSync = false;
    p->core->desiredVideoDimensions(p->core, &p->width, &p->height);
    p->pixels = calloc(p->width * p->height, sizeof(uint32_t));
    p->core->setVideoBuffer(p->core, p->pixels, p->width);
    if (!mCoreLoadFile(p->core, rom)) {
      fprintf(stderr, "cannot load %s\n", rom);
      return 2;
    }
    mCoreAutoloadSave(p->core);
    p->core->reset(p->core);

    GBASIOLockstepNodeCreate(&p->node);
    if (!GBASIOLockstepAttachNode(&coordinator, &p->node)) {
      fprintf(stderr, "cannot attach node %d\n", i);
      return 2;
    }
    GBASIOSetDriver(&((struct GBA *)p->core->board)->sio, &p->node.d, SIO_MULTI);
    GBASIOSetDriver(&((struct GBA *)p->core->board)->sio, &p->node.d, SIO_NORMAL_32);

    memset(&p->thread, 0, sizeof p->thread);
    p->thread.core = p->core;
    p->thread.userData = p;
    p->thread.startCallback = startCallback;
    p->thread.frameCallback = frameCallback;
  }
  fprintf(stderr, "link: P0 %d frames, P1 %d frames; starting\n", players[0].totalFrames,
          players[1].totalFrames);
  for (i = 0; i < PLAYERS; i++) {
    if (!mCoreThreadStart(&players[i].thread)) {
      fprintf(stderr, "cannot start thread %d\n", i);
      return 2;
    }
  }
  while (!(players[0].done && players[1].done))
    usleep(20 * 1000);
  fprintf(stderr, "link: both scripts finished\n");
  for (i = 0; i < PLAYERS; i++)
    mCoreThreadEnd(&players[i].thread);
  for (i = 0; i < PLAYERS; i++)
    mCoreThreadJoin(&players[i].thread);
  return 0;
}
