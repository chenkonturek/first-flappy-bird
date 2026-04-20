# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

- Install: `pip install -r requirements.txt`
- Run: `python main.py`
- Syntax check: `python -m py_compile main.py`
- Headless smoke test (no display/audio required):
  ```
  SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python -c "import main; g = main.Game(); g.state = main.STATE_PLAYING; [g.update(1/60) or g.draw() for _ in range(120)]"
  ```

No test suite, linter, or build step is configured.

## Architecture

Single-file pygame game (`main.py`). One entry point, one process, no packages. All sections delimited by `# ---` comment headers.

**State machine** lives on `Game.state` with three values: `STATE_START`, `STATE_PLAYING`, `STATE_GAME_OVER`. Input handling, physics, and rendering all branch on this. Transitions:
- START → PLAYING: first SPACE press (also triggers initial flap)
- PLAYING → GAME_OVER: pipe, ground, or ceiling collision in `Game.update`
- GAME_OVER → START: `R` key calls `Game.reset()`

**Self-contained assets.** The project ships no binary assets. Sprites are drawn at runtime via `pygame.draw` primitives (see `Bird._make_sprite`, `PipePair.draw`, `Background._make_sky/_make_ground_tile`). Sound effects are synthesized on first run into `assets/*.wav` using stdlib `wave` + `struct` + `math` — see `_gen_flap/_gen_score/_gen_hit/_gen_die` and `ensure_sounds()`. If a WAV already exists it is not regenerated, so **bumping a generator function won't take effect until the matching file under `assets/` is deleted**.

**Death sound timing.** `_game_over` plays `hit.wav` immediately and schedules `die.wav` 180ms later via `pygame.time.set_timer(DIE_SOUND_EVENT, 180, loops=1)`. That custom event is consumed in `Game.handle_event`, not in `update` — keep it there so the timer cancels itself (`set_timer(..., 0)`) after firing.

**Tuning knobs** are the module-level constants at the top of `main.py` (`GRAVITY`, `FLAP_VELOCITY`, `PIPE_SPEED`, `PIPE_GAP`, `PIPE_SPAWN_INTERVAL`, etc.). Physics uses real seconds via `dt = clock.tick(FPS) / 1000.0`, so changing `FPS` does not change game feel.

**Persistence.** High score lives in a plain text file `high_score.txt` (single integer). `load_high_score` swallows `OSError`/`ValueError` and returns 0; `save_high_score` swallows `OSError`. Written only on game-over when the new score beats the stored one.

**Graceful audio degradation.** `pygame.mixer.init()` is wrapped in try/except; if it fails (e.g., headless CI), `self.audio = False`, `self.sounds = {}`, and `_play()` becomes a no-op. The rest of the game runs normally.
