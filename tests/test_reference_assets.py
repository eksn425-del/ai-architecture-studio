from pathlib import Path

from app.reference_assets import (
    MAX_REFERENCE_IMAGE_BYTES,
    discover_project_reference_images,
    image_data_url,
    reference_image_label,
)


def _write(path: Path, data: bytes = b"fake-image") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return path


def test_reference_images_are_reference_first_and_project_local(tmp_path: Path) -> None:
    project = tmp_path / "project"
    reference = _write(project / "inputs" / "reference" / "b.webp")
    site = _write(project / "inputs" / "site" / "a.png")
    _write(project / "inputs" / "brief" / "notes.txt")
    _write(project / "outputs" / "renders" / "generated.png")

    images = discover_project_reference_images(project)

    assert images == [reference.resolve(), site.resolve()]
    assert all(path.is_relative_to((project / "inputs").resolve()) for path in images)


def test_reference_image_discovery_skips_unsupported_and_oversized(tmp_path: Path) -> None:
    project = tmp_path / "project"
    valid = _write(project / "inputs" / "reference" / "valid.jpg")
    _write(project / "inputs" / "reference" / "unsupported.bmp")
    oversized = project / "inputs" / "reference" / "too-large.png"
    oversized.parent.mkdir(parents=True, exist_ok=True)
    oversized.write_bytes(b"x" * (MAX_REFERENCE_IMAGE_BYTES + 1))

    assert discover_project_reference_images(project) == [valid.resolve()]


def test_reference_image_data_url_and_label(tmp_path: Path) -> None:
    image = _write(tmp_path / "inputs" / "reference" / "precedent.png", b"png-bytes")

    data_url = image_data_url(image)
    label = reference_image_label([image])

    assert data_url.startswith("data:image/png;base64,")
    assert "precedent.png" in label
    assert "first-class design evidence" in label
