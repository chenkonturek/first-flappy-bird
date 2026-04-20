import math
import os
import random
import struct
import wave

import pygame


# --- Constants ---
WIDTH, HEIGHT = 400, 600
FPS = 60

GRAVITY = 1400.0          # px/s^2
FLAP_VELOCITY = -420.0    # px/s (negative = up)
MAX_FALL_SPEED = 700.0

PIPE_SPEED = 180.0        # px/s
PIPE_GAP = 150            # vertical gap size
PIPE_WIDTH = 60
PIPE_SPAWN_INTERVAL = 1.5 # seconds

GROUND_HEIGHT = 80

BIRD_X = 80
BIRD_RADIUS = 14

SKY_TOP = (113, 197, 207)
SKY_BOTTOM = (223, 246, 245)
GROUND_COLOR = (222, 216, 149)
GROUND_STRIPE = (204, 189, 104)
PIPE_COLOR = (92, 174, 72)
PIPE_DARK = (58, 124, 42)
PIPE_LIGHT = (138, 207, 112)
BIRD_COLOR = (252, 211, 55)
BIRD_OUTLINE = (163, 118, 28)
BEAK_COLOR = (241, 134, 52)
EYE_WHITE = (255, 255, 255)
EYE_BLACK = (0, 0, 0)
TEXT_COLOR = (255, 255, 255)
SHADOW_COLOR = (0, 0, 0)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
HIGH_SCORE_PATH = os.path.join(BASE_DIR, "high_score.txt")
SAMPLE_RATE = 22050


# --- Sound generation (stdlib only) ---
def _write_wav(path, samples):
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SAMPLE_RATE)
        frames = b"".join(
            struct.pack("<h", max(-32767, min(32767, int(s * 32767))))
            for s in samples
        )
        w.writeframes(frames)


def _envelope(i, total, attack=0.02, release=0.1):
    a = max(1, int(total * attack))
    r = max(1, int(total * release))
    if i < a:
        return i / a
    if i > total - r:
        return max(0.0, (total - i) / r)
    return 1.0


def _gen_flap():
    dur = 0.09
    n = int(SAMPLE_RATE * dur)
    out = []
    for i in range(n):
        t = i / SAMPLE_RATE
        f = 300 + (700 - 300) * (i / n)
        s = math.sin(2 * math.pi * f * t) * 0.5
        out.append(s * _envelope(i, n, 0.02, 0.5))
    return out


def _gen_score():
    dur = 0.18
    n = int(SAMPLE_RATE * dur)
    out = []
    for i in range(n):
        t = i / SAMPLE_RATE
        s = (math.sin(2 * math.pi * 880 * t) + 0.6 * math.sin(2 * math.pi * 1320 * t)) * 0.32
        out.append(s * _envelope(i, n, 0.01, 0.5))
    return out


def _gen_hit():
    dur = 0.15
    n = int(SAMPLE_RATE * dur)
    out = []
    for i in range(n):
        s = (random.random() * 2 - 1) * 0.6
        out.append(s * _envelope(i, n, 0.005, 0.9))
    return out


def _gen_die():
    dur = 0.4
    n = int(SAMPLE_RATE * dur)
    out = []
    for i in range(n):
        t = i / SAMPLE_RATE
        f = 500 - (500 - 120) * (i / n)
        s = math.sin(2 * math.pi * f * t) * 0.45
        out.append(s * _envelope(i, n, 0.02, 0.6))
    return out


SOUND_GENERATORS = {
    "flap.wav": _gen_flap,
    "score.wav": _gen_score,
    "hit.wav": _gen_hit,
    "die.wav": _gen_die,
}


def ensure_sounds():
    os.makedirs(ASSETS_DIR, exist_ok=True)
    for name, gen in SOUND_GENERATORS.items():
        path = os.path.join(ASSETS_DIR, name)
        if not os.path.exists(path):
            _write_wav(path, gen())


# --- High score persistence ---
def load_high_score():
    try:
        with open(HIGH_SCORE_PATH) as f:
            return int(f.read().strip() or "0")
    except (OSError, ValueError):
        return 0


def save_high_score(score):
    try:
        with open(HIGH_SCORE_PATH, "w") as f:
            f.write(str(score))
    except OSError:
        pass


# --- Entities ---
class Bird:
    def __init__(self):
        self.x = BIRD_X
        self.y = HEIGHT / 2
        self.vy = 0.0
        self.radius = BIRD_RADIUS
        self._base = self._make_sprite()

    @staticmethod
    def _make_sprite():
        size = BIRD_RADIUS * 2 + 8
        s = pygame.Surface((size + 8, size), pygame.SRCALPHA)
        cx, cy = size // 2, size // 2
        pygame.draw.circle(s, BIRD_COLOR, (cx, cy), BIRD_RADIUS)
        pygame.draw.circle(s, BIRD_OUTLINE, (cx, cy), BIRD_RADIUS, 2)
        pygame.draw.ellipse(s, BIRD_OUTLINE, (cx - 7, cy + 1, 11, 6), 1)
        pygame.draw.polygon(
            s,
            BEAK_COLOR,
            [
                (cx + BIRD_RADIUS - 2, cy - 3),
                (cx + BIRD_RADIUS + 8, cy + 1),
                (cx + BIRD_RADIUS - 2, cy + 5),
            ],
        )
        pygame.draw.circle(s, EYE_WHITE, (cx + 5, cy - 5), 4)
        pygame.draw.circle(s, EYE_BLACK, (cx + 6, cy - 5), 2)
        return s

    def flap(self):
        self.vy = FLAP_VELOCITY

    def update(self, dt):
        self.vy = min(self.vy + GRAVITY * dt, MAX_FALL_SPEED)
        self.y += self.vy * dt
        if self.y < self.radius:
            self.y = self.radius
            self.vy = 0.0

    def rect(self):
        return pygame.Rect(
            int(self.x - self.radius + 2),
            int(self.y - self.radius + 2),
            self.radius * 2 - 4,
            self.radius * 2 - 4,
        )

    def draw(self, surface):
        angle = max(-25.0, min(75.0, -self.vy * 0.08))
        rot = pygame.transform.rotate(self._base, angle)
        rect = rot.get_rect(center=(int(self.x), int(self.y)))
        surface.blit(rot, rect.topleft)


class PipePair:
    def __init__(self, x, gap_y):
        self.x = float(x)
        self.gap_y = gap_y
        self.passed = False

    def update(self, dt):
        self.x -= PIPE_SPEED * dt

    def top_rect(self):
        return pygame.Rect(int(self.x), 0, PIPE_WIDTH, int(self.gap_y - PIPE_GAP / 2))

    def bottom_rect(self):
        top = int(self.gap_y + PIPE_GAP / 2)
        return pygame.Rect(int(self.x), top, PIPE_WIDTH, HEIGHT - GROUND_HEIGHT - top)

    def collides(self, bird_rect):
        return bird_rect.colliderect(self.top_rect()) or bird_rect.colliderect(self.bottom_rect())

    def off_screen(self):
        return self.x + PIPE_WIDTH < 0

    def draw(self, surface):
        for r in (self.top_rect(), self.bottom_rect()):
            pygame.draw.rect(surface, PIPE_COLOR, r)
            pygame.draw.rect(surface, PIPE_LIGHT, pygame.Rect(r.x + 6, r.y, 4, r.height))
            pygame.draw.rect(surface, PIPE_DARK, r, 2)
            if r.y == 0:
                cap = pygame.Rect(r.x - 4, r.bottom - 18, PIPE_WIDTH + 8, 18)
            else:
                cap = pygame.Rect(r.x - 4, r.y, PIPE_WIDTH + 8, 18)
            pygame.draw.rect(surface, PIPE_COLOR, cap)
            pygame.draw.rect(surface, PIPE_LIGHT, pygame.Rect(cap.x + 4, cap.y + 3, 4, cap.height - 6))
            pygame.draw.rect(surface, PIPE_DARK, cap, 2)


class Background:
    def __init__(self):
        self.sky = self._make_sky()
        self.ground = self._make_ground_tile()
        self.scroll_x = 0.0

    @staticmethod
    def _make_sky():
        h = HEIGHT - GROUND_HEIGHT
        s = pygame.Surface((WIDTH, h))
        for y in range(h):
            t = y / max(1, h - 1)
            r = int(SKY_TOP[0] + (SKY_BOTTOM[0] - SKY_TOP[0]) * t)
            g = int(SKY_TOP[1] + (SKY_BOTTOM[1] - SKY_TOP[1]) * t)
            b = int(SKY_TOP[2] + (SKY_BOTTOM[2] - SKY_TOP[2]) * t)
            pygame.draw.line(s, (r, g, b), (0, y), (WIDTH, y))
        return s

    @staticmethod
    def _make_ground_tile():
        tile_w = 48
        s = pygame.Surface((tile_w, GROUND_HEIGHT))
        s.fill(GROUND_COLOR)
        pygame.draw.rect(s, GROUND_STRIPE, (0, 0, tile_w, 6))
        pygame.draw.rect(s, (181, 166, 90), (0, 6, tile_w, 2))
        for i in range(3):
            pygame.draw.circle(s, GROUND_STRIPE, (8 + i * 16, 30 + (i % 2) * 14), 3)
        return s

    def update(self, dt, scrolling):
        if scrolling:
            self.scroll_x = (self.scroll_x + PIPE_SPEED * dt) % self.ground.get_width()

    def draw(self, surface):
        surface.blit(self.sky, (0, 0))
        tile_w = self.ground.get_width()
        x = -int(self.scroll_x)
        while x < WIDTH:
            surface.blit(self.ground, (x, HEIGHT - GROUND_HEIGHT))
            x += tile_w


# --- Game ---
STATE_START = "start"
STATE_PLAYING = "playing"
STATE_GAME_OVER = "game_over"

DIE_SOUND_EVENT = pygame.USEREVENT + 1


class Game:
    def __init__(self):
        try:
            pygame.mixer.pre_init(SAMPLE_RATE, -16, 1, 256)
        except pygame.error:
            pass
        pygame.init()
        try:
            pygame.mixer.init()
            self.audio = True
        except pygame.error:
            self.audio = False
        ensure_sounds()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Flappy Bird")
        self.clock = pygame.time.Clock()
        self.font_sm = pygame.font.SysFont(None, 28)
        self.font_md = pygame.font.SysFont(None, 44)
        self.font_lg = pygame.font.SysFont(None, 64)
        self.sounds = self._load_sounds()
        self.high_score = load_high_score()
        self.reset()

    def _load_sounds(self):
        if not self.audio:
            return {}
        out = {}
        for name in SOUND_GENERATORS:
            try:
                out[name.split(".")[0]] = pygame.mixer.Sound(os.path.join(ASSETS_DIR, name))
            except pygame.error:
                pass
        return out

    def _play(self, name):
        snd = self.sounds.get(name)
        if snd:
            snd.play()

    def reset(self):
        self.state = STATE_START
        self.bird = Bird()
        self.pipes = []
        self.background = Background()
        self.score = 0
        self.spawn_timer = 0.0

    def handle_event(self, event):
        if event.type == pygame.QUIT:
            return False
        if event.type == DIE_SOUND_EVENT:
            self._play("die")
            pygame.time.set_timer(DIE_SOUND_EVENT, 0)
            return True
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return False
            if event.key == pygame.K_SPACE:
                if self.state == STATE_START:
                    self.state = STATE_PLAYING
                    self.bird.flap()
                    self._play("flap")
                elif self.state == STATE_PLAYING:
                    self.bird.flap()
                    self._play("flap")
            elif event.key == pygame.K_r and self.state == STATE_GAME_OVER:
                self.reset()
        return True

    def _spawn_pipe(self):
        min_gap_y = PIPE_GAP / 2 + 40
        max_gap_y = HEIGHT - GROUND_HEIGHT - PIPE_GAP / 2 - 40
        gap_y = random.uniform(min_gap_y, max_gap_y)
        self.pipes.append(PipePair(WIDTH + 10, gap_y))

    def update(self, dt):
        self.background.update(dt, scrolling=(self.state != STATE_GAME_OVER))

        if self.state == STATE_START:
            self.bird.y = HEIGHT / 2 + math.sin(pygame.time.get_ticks() * 0.005) * 6
            return

        if self.state != STATE_PLAYING:
            return

        self.bird.update(dt)

        self.spawn_timer += dt
        if self.spawn_timer >= PIPE_SPAWN_INTERVAL:
            self.spawn_timer = 0.0
            self._spawn_pipe()

        for p in self.pipes:
            p.update(dt)
        self.pipes = [p for p in self.pipes if not p.off_screen()]

        for p in self.pipes:
            if not p.passed and p.x + PIPE_WIDTH < self.bird.x:
                p.passed = True
                self.score += 1
                self._play("score")

        br = self.bird.rect()
        hit_pipe = any(p.collides(br) for p in self.pipes)
        hit_ground = self.bird.y + self.bird.radius >= HEIGHT - GROUND_HEIGHT
        if hit_pipe or hit_ground:
            self._game_over()

    def _game_over(self):
        self.state = STATE_GAME_OVER
        self._play("hit")
        pygame.time.set_timer(DIE_SOUND_EVENT, 180, loops=1)
        if self.score > self.high_score:
            self.high_score = self.score
            save_high_score(self.high_score)

    def draw(self):
        self.background.draw(self.screen)
        for p in self.pipes:
            p.draw(self.screen)
        self.bird.draw(self.screen)

        if self.state == STATE_START:
            self._centered("Flappy Bird", self.font_lg, HEIGHT // 2 - 140)
            self._centered("Press SPACE to flap", self.font_sm, HEIGHT // 2 + 60)
            self._centered(f"High score: {self.high_score}", self.font_sm, HEIGHT // 2 + 95)
        elif self.state == STATE_PLAYING:
            self._centered(str(self.score), self.font_lg, 60)
        elif self.state == STATE_GAME_OVER:
            self._centered("Game Over", self.font_lg, HEIGHT // 2 - 100)
            self._centered(f"Score: {self.score}", self.font_md, HEIGHT // 2 - 30)
            self._centered(f"Best: {self.high_score}", self.font_md, HEIGHT // 2 + 15)
            self._centered("Press R to restart", self.font_sm, HEIGHT // 2 + 80)

        pygame.display.flip()

    def _centered(self, text, font, y):
        shadow = font.render(text, True, SHADOW_COLOR)
        label = font.render(text, True, TEXT_COLOR)
        rect = label.get_rect(center=(WIDTH // 2, y))
        self.screen.blit(shadow, rect.move(2, 2))
        self.screen.blit(label, rect)

    def run(self):
        running = True
        while running:
            dt = self.clock.tick(FPS) / 1000.0
            for event in pygame.event.get():
                if not self.handle_event(event):
                    running = False
                    break
            if not running:
                break
            self.update(dt)
            self.draw()
        pygame.quit()


def main():
    Game().run()


if __name__ == "__main__":
    main()
