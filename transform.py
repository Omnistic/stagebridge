import numpy as np
import json, os, re

# Only letters, numbers, underscore and hyphen. This is deliberately a
# whitelist (not a blocklist of "../" etc.) so there's no clever encoding
# that sneaks past it - anything not in this set is rejected outright.
_VALID_NAME = re.compile(r"^[A-Za-z0-9_-]+$")


def _validate_name(filename: str) -> None:
    if not _VALID_NAME.match(filename):
        raise ValueError(
            "Transform name can only contain letters, numbers, underscores, and hyphens."
        )


def calculate_transform(positions_a, positions_b):
    if len(positions_a) != len(positions_b):
        raise ValueError("The same number of positions must be provided for Microscope A and B")

    positions_a = np.array(positions_a)
    positions_b = np.array(positions_b)

    centroid_a = positions_a.mean(axis=0)
    centroid_b = positions_b.mean(axis=0)

    centered_a = positions_a - centroid_a
    centered_b = positions_b - centroid_b

    scaling = np.sqrt(np.sum(centered_b**2) / np.sum(centered_a**2))

    mirrors = [
        np.diag([1.0, 1.0]),
        np.diag([-1.0, 1.0]),
        np.diag([1.0, -1.0]),
        np.diag([-1.0, -1.0]),
    ]

    best_residual = np.inf
    best_mirror = None
    best_rotation = None

    for mirror in mirrors:
        scaled_a = (centered_a @ mirror) * scaling
        H = centered_b.T @ scaled_a
        U, _, Vt = np.linalg.svd(H)
        rotation = U @ Vt
        if np.linalg.det(rotation) < 0:
            U[:, -1] *= -1
            rotation = U @ Vt
        residual = np.sum((centered_b - scaled_a @ rotation.T) ** 2)
        if residual < best_residual:
            best_residual = residual
            best_mirror = mirror
            best_rotation = rotation

    return centroid_a, centroid_b, scaling, best_mirror, best_rotation

def apply_transform(positions, centroid_a, centroid_b, scaling, mirror, rotation):
    return ((positions - centroid_a) @ mirror) * scaling @ rotation.T + centroid_b

def write_transform(transform, filename):
    _validate_name(filename)
    os.makedirs("available_transforms", exist_ok=True)
    # "x" mode fails atomically (FileExistsError) if the file already exists,
    # instead of the caller pre-checking existence and then writing separately
    # (which would be racy if two users saved the same name at the same time).
    with open(f"available_transforms/{filename}.json", "x") as f:
        json.dump(transform, f, indent=2)

def read_transform(filename):
    _validate_name(filename)
    with open(f"available_transforms/{filename}.json") as f:
        return json.load(f)