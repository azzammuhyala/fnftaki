# -*- coding: utf-8 -*-

# dari claude btw

"""
Timestamp Helper
-----------------
Alat bantu untuk menentukan timestamp note pada chart rhythm game
sambil mendengarkan lagu & melihat preview note di layar.

Kontrol:
    SPACE        : Play / Pause
    LEFT / RIGHT : Seek mundur / maju
    SHIFT        : step 10 ms
    CTRL         : step 500 ms
    ENTER        : copy timestamp saat ini ke clipboard (+ print ke console)
"""

import sys
import csv
import bisect
import subprocess

import pygame

# ==========================
# CONFIG
# ==========================

PATH = r"assets/songs/crucify anniversary"

SONG = PATH + "/music.ogg"
CHART = PATH + "/chart.csv"

WIDTH = 1200
HEIGHT = 320

TIMELINE_TOP = 40
TIMELINE_BOTTOM = 220
LANE_HEIGHT = 22

SLIDER_Y = 275

VISIBLE_MS = 6000  # total jendela waktu yang terlihat (±3000 ms dari current_time)
FPS = 60

BG_COLOR = (24, 24, 28)
PANEL_COLOR = (32, 32, 38)
LINE_COLOR = (230, 230, 230)
GUIDE_COLOR = (90, 90, 100)
TEXT_COLOR = (235, 235, 235)
SUBTEXT_COLOR = (160, 160, 170)
SLIDER_TRACK = (70, 70, 80)
SLIDER_FILL = (255, 205, 60)

LANE_COLORS = (
    (255, 90, 90),
    (255, 190, 60),
    (110, 220, 110),
    (90, 170, 255),
    (200, 110, 255),
    (255, 110, 200),
    (110, 230, 230),
    (230, 230, 110),
)

# ==========================
# LOAD CHART
# ==========================


def load_notes(path):
    """Baca chart.csv dengan aman. Baris yang rusak akan di-skip, bukan
    membuat seluruh program crash."""
    loaded = []
    max_lane_seen = 0

    try:
        f = open(path, newline="")
    except OSError as e:
        print(f"[FATAL] Tidak bisa membuka chart: {path} ({e})")
        sys.exit(1)

    with f:
        reader = csv.reader(f)
        for line_no, row in enumerate(reader, start=1):
            if not row:
                continue
            try:
                lane = int(row[0])
                time = int(row[1])
                length = int(row[2]) if len(row) >= 3 and row[2].strip() else 0
            except (ValueError, IndexError):
                print(f"[WARN] Baris {line_no} pada chart tidak valid, dilewati: {row}")
                continue

            if lane < 0:
                print(f"[WARN] Baris {line_no}: lane negatif ({lane}), dilewati")
                continue
            if time < 0:
                print(f"[WARN] Baris {line_no}: time negatif ({time}), dilewati")
                continue
            if length < 0:
                length = 0

            max_lane_seen = max(max_lane_seen, lane)
            loaded.append((lane, time, length))

    loaded.sort(key=lambda n: n[1])

    if max_lane_seen >= len(LANE_COLORS):
        print(f"[WARN] Ada lane {max_lane_seen} tapi hanya {len(LANE_COLORS)} warna "
              f"terdefinisi, warna akan berulang (mod).")

    return loaded


notes = load_notes(CHART)
note_times = [n[1] for n in notes]  # daftar waktu terurut, dipakai untuk bisect

if notes:
    song_length = max(n[1] + n[2] for n in notes) + 3000
else:
    print("[WARN] Chart kosong, memakai panjang default 60 detik.")
    song_length = 60_000

song_length = max(song_length, 1)  # jangan sampai 0 -> hindari ZeroDivisionError

# ==========================
# INIT
# ==========================

pygame.init()
pygame.mixer.init()

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Timestamp Helper")

font_big = pygame.font.SysFont(None, 42)
font_small = pygame.font.SysFont(None, 22)
font_tiny = pygame.font.SysFont(None, 18)

clock = pygame.time.Clock()

music_available = True
try:
    pygame.mixer.music.load(SONG)
except pygame.error as e:
    music_available = False
    print(f"[WARN] Tidak bisa memuat audio '{SONG}': {e}")
    print("       Program tetap berjalan tanpa audio.")

playing = False
current_time = 0
dragging = False

last_tick = pygame.time.get_ticks()

# ==========================
# HELPERS
# ==========================


def format_time(ms):
    ms = max(0, ms)
    m = ms // 60000
    s = (ms % 60000) // 1000
    f = ms % 1000
    return f"{m:02}:{s:02}.{f:03}"


def clamp_time():
    global current_time
    current_time = max(0, min(current_time, song_length))


def restart_music():
    """Mulai ulang playback dari current_time. Aman dipanggil walau
    audio gagal dimuat atau backend tidak mendukung seek."""
    if not music_available:
        return

    clamp_time()
    pygame.mixer.music.stop()

    start_sec = current_time / 1000
    try:
        pygame.mixer.music.play(start=start_sec)
    except pygame.error:
        # Backend tidak mendukung parameter start= (mis. beberapa format non-ogg).
        # Fallback: mainkan dari awal lalu coba geser posisi.
        try:
            pygame.mixer.music.play()
            pygame.mixer.music.set_pos(start_sec)
        except pygame.error as e:
            print(f"[WARN] Gagal seek audio: {e}")

    if not playing:
        pygame.mixer.music.pause()


def copy_to_clipboard(text):
    """Copy ke clipboard lintas platform. Kalau gagal, cukup print saja
    tanpa membuat program crash."""
    candidates = {
        "win32": [["clip"]],
        "darwin": [["pbcopy"]],
    }
    commands = candidates.get(sys.platform, [["xclip", "-selection", "clipboard"], ["xsel", "--clipboard", "--input"]])

    for cmd in commands:
        try:
            subprocess.run(cmd, input=text, text=True, encoding="utf-8", check=True)
            return True
        except (OSError, subprocess.CalledProcessError):
            continue

    print("[INFO] Clipboard tool tidak tersedia, hanya di-print.")
    return False


def visible_notes():
    """Ambil hanya notes yang jatuh dalam jendela waktu yang tampil di layar,
    memakai bisect di list waktu yang sudah terurut (bukan loop semua notes)."""
    if not notes:
        return []

    lo_time = current_time - VISIBLE_MS // 2
    hi_time = current_time + VISIBLE_MS // 2

    lo_idx = bisect.bisect_left(note_times, lo_time)
    hi_idx = bisect.bisect_right(note_times, hi_time)

    return notes[lo_idx:hi_idx]


# ==========================
# DRAWING
# ==========================


def draw_notes():
    center = WIDTH // 2
    px_per_ms = WIDTH / VISIBLE_MS

    # panel latar timeline
    pygame.draw.rect(screen, PANEL_COLOR, (0, TIMELINE_TOP - 10, WIDTH, TIMELINE_BOTTOM - TIMELINE_TOP + 20), border_radius=8)

    # garis panduan waktu tiap 500ms
    step = 500
    first_guide = (current_time - VISIBLE_MS // 2) // step * step
    t = first_guide
    while t <= current_time + VISIBLE_MS // 2:
        gx = center + (t - current_time) * px_per_ms
        if 0 <= gx <= WIDTH:
            pygame.draw.line(screen, GUIDE_COLOR, (gx, TIMELINE_TOP), (gx, TIMELINE_BOTTOM), 1)
        t += step

    # garis playhead (waktu sekarang)
    pygame.draw.line(screen, LINE_COLOR, (center, TIMELINE_TOP - 6), (center, TIMELINE_BOTTOM + 6), 2)

    for lane, time, length in visible_notes():
        diff = time - current_time
        x = center + diff * px_per_ms
        y = TIMELINE_TOP + LANE_HEIGHT * (lane % len(LANE_COLORS))
        color = LANE_COLORS[lane % len(LANE_COLORS)]

        if length:
            endx = x + length * px_per_ms
            pygame.draw.line(screen, color, (x, y + 10), (endx, y + 10), 4)

        pygame.draw.line(screen, color, (x, y), (x, y + 20), 3)
        pygame.draw.circle(screen, color, (int(x), int(y + 10)), 4)


def draw_slider():
    pygame.draw.line(screen, SLIDER_TRACK, (40, SLIDER_Y), (WIDTH - 40, SLIDER_Y), 5)

    ratio = current_time / song_length
    ratio = max(0.0, min(1.0, ratio))
    x = 40 + ratio * (WIDTH - 80)

    pygame.draw.line(screen, SLIDER_FILL, (40, SLIDER_Y), (x, SLIDER_Y), 5)
    pygame.draw.circle(screen, SLIDER_FILL, (int(x), SLIDER_Y), 8)
    pygame.draw.circle(screen, (0, 0, 0), (int(x), SLIDER_Y), 8, 1)


def draw_header():
    txt = font_big.render(format_time(current_time), True, TEXT_COLOR)
    screen.blit(txt, (20, 8))

    status = "PLAYING" if playing else "PAUSED"
    status_color = (110, 220, 110) if playing else (220, 110, 110)
    stxt = font_small.render(status, True, status_color)
    screen.blit(stxt, (WIDTH - stxt.get_width() - 20, 18))

    if not music_available:
        wtxt = font_small.render("audio tidak tersedia", True, (220, 150, 90))
        screen.blit(wtxt, (WIDTH - wtxt.get_width() - 20, 40))


def draw_footer():
    txt = font_tiny.render(
        "SPACE Play/Pause    LEFT/RIGHT Seek    SHIFT=10ms  CTRL=500ms    ENTER Copy timestamp",
        True,
        SUBTEXT_COLOR,
    )
    screen.blit(txt, (20, HEIGHT - 24))

    ntxt = font_tiny.render(f"{len(notes)} notes", True, SUBTEXT_COLOR)
    screen.blit(ntxt, (WIDTH - ntxt.get_width() - 20, HEIGHT - 24))


# ==========================
# MAIN LOOP
# ==========================


def handle_keydown(event):
    global current_time, playing

    mods = pygame.key.get_mods()
    step = 1
    if mods & pygame.KMOD_CTRL:
        step = 500
    elif mods & pygame.KMOD_SHIFT:
        step = 10

    if event.key == pygame.K_SPACE:
        playing = not playing
        if music_available:
            if playing:
                pygame.mixer.music.unpause()
            else:
                pygame.mixer.music.pause()

    elif event.key == pygame.K_LEFT:
        current_time -= step
        clamp_time()
        restart_music()

    elif event.key == pygame.K_RIGHT:
        current_time += step
        clamp_time()
        restart_music()

    elif event.key == pygame.K_RETURN:
        text = str(current_time)
        copy_to_clipboard(text)
        print(text)


def handle_mousedown(event):
    global dragging, playing
    mx, my = event.pos
    if abs(my - SLIDER_Y) < 20:
        dragging = True
        if music_available and playing:
            pygame.mixer.music.pause()


def handle_mouseup(event):
    global dragging
    if dragging:
        dragging = False
        restart_music()


def handle_mousemotion(event):
    global current_time
    if dragging:
        mx = max(40, min(WIDTH - 40, event.pos[0]))
        ratio = (mx - 40) / (WIDTH - 80)
        current_time = int(song_length * ratio)
        clamp_time()


def main():
    global current_time, last_tick, running

    running = True
    restart_music()

    while running:
        now = pygame.time.get_ticks()
        dt = now - last_tick
        last_tick = now

        if playing and not dragging:
            current_time += dt
            if current_time >= song_length:
                current_time = song_length
                # lagu selesai; hentikan otomatis biar tidak lanjut menghitung tak terbatas
                globals()["playing"] = False
                if music_available:
                    pygame.mixer.music.pause()
            clamp_time()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                handle_keydown(event)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                handle_mousedown(event)
            elif event.type == pygame.MOUSEBUTTONUP:
                handle_mouseup(event)
            elif event.type == pygame.MOUSEMOTION:
                handle_mousemotion(event)

        screen.fill(BG_COLOR)
        draw_header()
        draw_notes()
        draw_slider()
        draw_footer()
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()


if __name__ == "__main__":
    main()