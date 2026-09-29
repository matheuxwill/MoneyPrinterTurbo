"""Compile a reviewed VISÕES episode into a MoneyPrinterTurbo CLI batch task.

This intentionally does not generate assets or publish anything. It refuses to
render when a shot is missing, preserving the character's visual continuity.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
VIDEO_EXTENSIONS = {".mp4", ".mov", ".mkv", ".webm"}


def compile_episode(spec_path: Path) -> dict:
    spec_path = spec_path.resolve()
    episode = json.loads(spec_path.read_text(encoding="utf-8"))
    required = ("episode_id", "title", "script", "shots")
    missing_fields = [key for key in required if not episode.get(key)]
    if missing_fields:
        raise ValueError("required fields missing: " + ", ".join(missing_fields))

    shots = episode["shots"]
    if not isinstance(shots, list) or len(shots) < 2:
        raise ValueError("at least two approved shots are required")
    clip_duration = episode.get("clip_duration", 5)
    if not isinstance(clip_duration, int) or not 1 <= clip_duration <= 30:
        raise ValueError("clip_duration must be an integer from 1 to 30 seconds")

    media = []
    missing_assets = []
    shot_ids = set()
    for i, shot in enumerate(shots, 1):
        if not isinstance(shot, dict) or not shot.get("id") or not shot.get("file"):
            raise ValueError(f"shot {i} needs an id and file")
        if shot["id"] in shot_ids:
            raise ValueError(f"duplicate shot id: {shot['id']}")
        shot_ids.add(shot["id"])
        source = (spec_path.parent / shot["file"]).resolve()
        if source.suffix.lower() not in IMAGE_EXTENSIONS | VIDEO_EXTENSIONS:
            raise ValueError(f"unsupported media extension for shot {shot['id']}")
        if not source.is_file():
            missing_assets.append(f"{shot['id']}: {source}")
        media.append({"provider": "local", "url": str(source)})

    if missing_assets:
        raise ValueError("missing approved assets:\n" + "\n".join(missing_assets))

    # MPT presently applies one duration to every still/clip and may recycle
    # footage if the narration runs longer. Require the editor to provide a
    # conservative expected length, then leave a full clip of headroom.
    expected_seconds = episode.get("expected_narration_seconds")
    if not isinstance(expected_seconds, (int, float)) or expected_seconds <= 0:
        raise ValueError("expected_narration_seconds must be a positive number")
    if len(shots) * clip_duration < expected_seconds + clip_duration:
        raise ValueError("shots do not cover narration plus one clip of headroom")

    narration = episode.get("narration_file")
    if narration:
        narration_path = (spec_path.parent / narration).resolve()
        if not narration_path.is_file():
            raise ValueError(f"narration file missing: {narration_path}")
    else:
        narration_path = None

    # A preset for assembly, not an aesthetic or voice approval. No automatic
    # stock search, random footage, transitions, music, or social posting.
    task = {
        "video_subject": episode["title"],
        "video_script": episode["script"],
        "video_language": "pt-BR",
        "video_source": "local",
        "video_materials": media,
        "video_aspect": "9:16",
        "video_fit_mode": "cover",
        "video_concat_mode": "sequential",
        "video_transition_mode": None,
        "video_clip_duration": clip_duration,
        "video_count": 1,
        "voice_name": episode.get("voice_name", "pt-BR-AntonioNeural"),
        "voice_rate": episode.get("voice_rate", 1.0),
        "bgm_type": "",
        "bgm_volume": 0,
        "subtitle_enabled": bool(episode.get("subtitles", True)),
        "subtitle_display_mode": "sentence",
        "subtitle_animation": "none",
        "subtitle_position": "bottom",
        "font_name": "BeVietnamPro-Medium.ttf",
        "text_fore_color": "#F4F0E7",
        "stroke_color": "#11110F",
        "stroke_width": 1.0,
        "font_size": 48,
    }
    if narration_path:
        task["custom_audio_file"] = str(narration_path)
        task["voice_name"] = ""
        # The default Edge subtitle provider has no timestamps for imported
        # audio. Subtitles need Whisper or a separately verified SRT pass.
        task["subtitle_enabled"] = False
    return task


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("episode", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    try:
        task = compile_episode(args.episode)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        parser.exit(2, f"Episode is not ready for rendering:\n{exc}\n")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps([task], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Ready: {args.out} ({len(task['video_materials'])} ordered shots)")
    print(f"Run from the repository root: uv run python cli.py --batch-file {args.out} --stop-at video")


if __name__ == "__main__":
    main()
