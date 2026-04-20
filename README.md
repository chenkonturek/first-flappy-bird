# Flappy Bird

A Flappy Bird clone in Python + [pygame](https://www.pygame.org/). Single-file, no binary assets — sprites are drawn with `pygame.draw` and sound effects are synthesized at first run with the Python standard library.

![Python](https://img.shields.io/badge/python-3.8%2B-blue) ![pygame](https://img.shields.io/badge/pygame-%E2%89%A52.5-green)

## Install

```bash
pip install -r requirements.txt
```

## Run

```bash
python main.py
```

On first launch, `assets/flap.wav`, `score.wav`, `hit.wav`, and `die.wav` are generated under `assets/`. `high_score.txt` is written the first time you beat a score.

## Controls

| Key    | Action              |
| ------ | ------------------- |
| SPACE  | Flap / start game   |
| R      | Restart after death |
| ESC    | Quit                |

## Features

- Gravity + flap physics tuned for the classic feel
- Procedurally drawn bird, pipes, and scrolling ground
- Start screen, game-over screen, and persistent high score
- Sound effects generated on the fly with `wave` + `math` (no audio files shipped)
- Graceful fallback when audio is unavailable (headless / no mixer)

## Tuning

Physics and difficulty live as module-level constants at the top of `main.py`: `GRAVITY`, `FLAP_VELOCITY`, `PIPE_SPEED`, `PIPE_GAP`, `PIPE_SPAWN_INTERVAL`.

If you change a sound generator (`_gen_flap`, `_gen_score`, `_gen_hit`, `_gen_die`), delete the corresponding `assets/*.wav` so it gets regenerated — existing files are never overwritten.

## License

MIT — do whatever you like.
