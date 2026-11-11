"""Prepare pinned upstream assets and the chosen AVE feature rows for reproduction."""

import argparse
import hashlib
from pathlib import Path
import subprocess
from urllib.request import urlopen

import h5py
import numpy as np

from ave_reference import UPSTREAM_REVISION, fetch_visual
from ave_smoke import (
    CHECKPOINT_SHA256, FEATURES, LOCAL, MODEL_SOURCE_SHA256, SAMPLE, UPSTREAM,
    read_annotations, split_indices, validation_rows,
)


AUDIO_URL = "https://huggingface.co/datasets/LECOO/AVE/resolve/main/audio_feature.h5?download=true"
AUDIO_SHA256 = "6765e445a5a66853282964576222c7aaf895b563100b2d99f29ecfd413c7d8fc"


def digest(path):
    with path.open("rb") as file:
        return hashlib.file_digest(file, "sha256").hexdigest()


def git(*args):
    return subprocess.check_output(["git", "-C", str(UPSTREAM), *args], text=True).strip()


def prepare_upstream():
    UPSTREAM.mkdir(parents=True, exist_ok=True)
    if not (UPSTREAM / ".git").exists():
        git("init")
        git("remote", "add", "origin", "https://github.com/YapengTian/AVE-ECCV18.git")
        git("fetch", "--depth", "1", "origin", UPSTREAM_REVISION)
        git("checkout", "--detach", "FETCH_HEAD")
    if git("rev-parse", "HEAD") != UPSTREAM_REVISION or git("status", "--porcelain"):
        raise ValueError("The upstream checkout must be clean at the pinned revision")
    for relative, expected in (("models.py", MODEL_SOURCE_SHA256), ("model/AV_att.pt", CHECKPOINT_SHA256)):
        if digest(UPSTREAM / relative) != expected:
            raise ValueError(f"Unexpected upstream file: {relative}")


def prepare_audio():
    path = LOCAL / "audio_feature.h5"
    if not path.exists():
        temporary = path.with_suffix(".download")
        try:
            with urlopen(AUDIO_URL, timeout=60) as remote, temporary.open("wb") as file:
                while chunk := remote.read(1024 * 1024):
                    file.write(chunk)
            if digest(temporary) != AUDIO_SHA256:
                raise ValueError("The audio mirror does not match the recorded experiment version")
            temporary.replace(path)
        finally:
            temporary.unlink(missing_ok=True)
    if digest(path) != AUDIO_SHA256:
        raise ValueError("The local audio file differs from the recorded mirror")
    official = LOCAL / "audio_feature_official.h5"
    if official.exists() and digest(official) != AUDIO_SHA256:
        raise ValueError("An alternative official audio file would change the recorded experiment inputs")
    with h5py.File(path, "r") as file:
        if file["avadataset"].shape != FEATURES["audio"][2]:
            raise ValueError("Unexpected audio feature shape")


def prepare_smoke():
    from ave_reference import VISUAL_DTYPE, VISUAL_SHAPE, cached_visual

    rows = validation_rows(read_annotations())
    directory = LOCAL / "visual_validation"
    fetch_visual(rows, directory)
    visual = np.stack([np.frombuffer(cached_visual(int(row), directory).read_bytes(), dtype=VISUAL_DTYPE)
                       .reshape(VISUAL_SHAPE[1:]) for row in rows])
    with h5py.File(LOCAL / "audio_feature.h5", "r") as file:
        audio = np.stack([file["avadataset"][int(row)] for row in rows])
    temporary = SAMPLE.with_suffix(".part.npz")
    np.savez(temporary, rows=rows, audio=audio, visual=visual)
    temporary.replace(SAMPLE)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--split", choices=("smoke", "val", "test", "all"), default="smoke")
    args = parser.parse_args()
    LOCAL.mkdir(exist_ok=True)
    prepare_upstream()
    prepare_audio()
    if args.split in ("smoke", "all"):
        prepare_smoke()
    for split, directory in (("val", "visual_validation"), ("test", "visual_test")):
        if args.split in (split, "all"):
            fetch_visual(split_indices(split), LOCAL / directory)
    print(f"Prepared {args.split}; upstream {UPSTREAM_REVISION}")
