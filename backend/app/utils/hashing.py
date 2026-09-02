import hashlib
from typing import Any, List, Sequence

from app.core.exceptions import ValidationException


def compute_composite_sha256(artifacts: Sequence[Any]) -> str:
    """
    Computes a deterministic 32-byte composite SHA-256 digest across all participating
    project version artifacts strictly conforming to docs/blockchain/BLOCKCHAIN_DESIGN.md Section 2.

    Algorithm specification:
    1. Participating Artifacts:
       - Every file belonging to the snapshot is included.
       - Empty versions (0 files) are rejected.
    2. Artifact Sorting Order:
       - Artifacts are sorted in ascending lexicographical order based on their canonical UTF-8 file name
         using standard ASCII / Unicode byte-order comparison (a < b < c).
    3. Participating Fields per Artifact:
       - file_name: Normalized string (no leading/trailing whitespace).
       - file_size_bytes: Integer formatted as base-10 ASCII string.
       - sha256_hash: Standard 64-character lowercase hexadecimal SHA-256 digest of raw file contents.
    4. Canonical Line Serialization:
       Line_i = file_name_i || ":" || file_size_bytes_i || ":" || sha256_hash_i
    5. Payload Delimiter & Character Encoding:
       - Strict UTF-8 without BOM.
       - Unix newline '\\n' between artifact lines; no trailing newline after the last artifact.
    6. Composite Hashing:
       Composite SHA-256 = SHA-256_hex(Line_1 || "\\n" || Line_2 || "\\n" || ... || Line_n)
    """
    if not artifacts:
        raise ValidationException(
            code="EMPTY_ARTIFACTS_NOT_ALLOWED",
            message="Cannot compute composite SHA-256 digest for an empty artifact snapshot. At least one artifact is required.",
            details={"artifacts_count": 0},
        )

    # Extract participating fields
    processed_items = []
    for art in artifacts:
        # Support both ORM models and dictionaries/objects with attributes
        file_name = getattr(art, "file_name", None)
        if file_name is None and isinstance(art, dict):
            file_name = art.get("file_name")

        file_size_bytes = getattr(art, "file_size_bytes", None)
        if file_size_bytes is None and isinstance(art, dict):
            file_size_bytes = art.get("file_size_bytes")

        sha256_hash = getattr(art, "sha256_hash", None)
        if sha256_hash is None and isinstance(art, dict):
            sha256_hash = art.get("sha256_hash")

        if not file_name or file_size_bytes is None or not sha256_hash:
            raise ValidationException(
                code="INVALID_ARTIFACT_METADATA",
                message="Artifact is missing required fields (file_name, file_size_bytes, or sha256_hash) for composite hashing.",
                details={"file_name": file_name},
            )

        clean_file_name = str(file_name).strip()
        clean_size = str(int(file_size_bytes))
        clean_hash = str(sha256_hash).strip().lower()

        processed_items.append((clean_file_name, clean_size, clean_hash))

    # Sort in ascending lexicographical order by canonical UTF-8 file name
    # Python's string comparison follows standard Unicode codepoints / UTF-8 byte order
    processed_items.sort(key=lambda x: x[0])

    # Construct canonical lines
    lines = [f"{fn}:{size}:{h}" for fn, size, h in processed_items]

    # Concatenate with Unix newline without trailing newline
    canonical_string = "\n".join(lines)

    # Compute SHA-256 hex digest
    return hashlib.sha256(canonical_string.encode("utf-8")).hexdigest().lower()
