# VISÕES production adapter

This adapter takes an approved episode and produces one CLI batch task for
MoneyPrinterTurbo. It preserves a fixed shot order and refuses incomplete
episodes. It does not create images, choose stock footage, or publish a video.

1. Place approved images or clips in an episode folder.
2. Write an episode JSON with `episode_id`, `title`, `script`,
   `expected_narration_seconds`, `clip_duration`, and ordered `shots` entries
   such as `{"id":"01","file":"shots/01.png"}`.
3. Compile: `python integrations/visoes/prepare.py episode.json --out episode.batch.json`.
4. From the repository root, run
   `uv run python cli.py --batch-file episode.batch.json --stop-at video`.
5. Review the result in `storage/tasks/<task-id>/` before any publication.

The default `pt-BR-AntonioNeural` voice is only a test voice. A reviewed
`narration_file` can replace it; subtitles are then disabled because the
default Edge subtitle path cannot time imported narration. Enable a verified
Whisper/SRT workflow before publishing. Music is disabled until licensed
VISÕES tracks are available.

MoneyPrinterTurbo applies one `clip_duration` across the episode, renders
stills with automatic zoom, and can repeat footage when audio is longer than
the supplied material. The adapter checks for a spare clip based on the
expected narration duration; inspect the actual render for timing and repeats.

This is an assembly stage. Elias' identity, motion, voice, music, caption
legibility, and publication approval remain editorial checks.
