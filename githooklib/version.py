MINIMUM_COMPATIBLE_VERSION: str = "1.0.0"


def _parse_version(version_str: str) -> tuple[int, int, int]:
    parts = version_str.split(".")
    if len(parts) != 3:
        raise ValueError(
            f"Invalid version format: {version_str}. Expected format: x.y.z"
        )
    try:
        return (int(parts[0]), int(parts[1]), int(parts[2]))
    except ValueError as e:
        raise ValueError(
            f"Invalid version format: {version_str}. All parts must be integers."
        ) from e


def _compare_versions(version1: str, version2: str) -> int:
    v1 = _parse_version(version1)
    v2 = _parse_version(version2)
    if v1 < v2:
        return -1
    if v1 > v2:
        return 1
    return 0


def is_version_compatible(installed_version: str) -> bool:
    try:
        comparison = _compare_versions(installed_version, MINIMUM_COMPATIBLE_VERSION)
        return comparison >= 0
    except ValueError:
        return False


__all__ = [
    "MINIMUM_COMPATIBLE_VERSION",
    "is_version_compatible",
]
