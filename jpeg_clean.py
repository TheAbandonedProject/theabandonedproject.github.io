"""Dependency-free JPEG metadata check (standard library only), shared by the derivative maker, the image-swap step
and the hosting repository's own CI. A JPEG is 'clean' when the only segment beyond the picture data is the plain
JFIF header. Returns a list of problems; empty means clean."""
import struct

METADATA_MARKERS = [b"Exif", b"GPS", b"http://ns.adobe.com", b"xmpmeta", b"Photoshop 3.0", b"ICC_PROFILE", b"MakerNote",
                    b"8BIM", b"IPTC", b"XMP"]


def jpeg_segments(data: bytes):
    """Yield (marker, payload) for every segment up to the start of scan data."""
    if data[:2] != b"\xff\xd8":
        raise ValueError("not a JPEG")
    i = 2
    while i < len(data):
        if data[i] != 0xFF:
            raise ValueError(f"bad marker at {i}")
        while data[i] == 0xFF:
            i += 1
        m = data[i]; i += 1
        if m == 0xDA or m == 0xD9:
            yield m, b""
            return
        if 0xD0 <= m <= 0xD7 or m == 0x01:
            continue
        (ln,) = struct.unpack(">H", data[i:i + 2])
        yield m, data[i + 2:i + ln]
        i += ln


def verify_clean_raw(data: bytes):
    problems = []
    try:
        for m, payload in jpeg_segments(data):
            if m == 0xE0:
                if not payload.startswith(b"JFIF\x00"):
                    problems.append("APP0 segment that is not plain JFIF")
            elif 0xE1 <= m <= 0xEF:
                problems.append(f"APP{m - 0xE0} segment ({payload[:12]!r})")
            elif m == 0xFE:
                problems.append("COM (comment) segment")
    except Exception as e:
        return [f"not a readable JPEG ({e})"]
    head = data[:200000]
    for s in METADATA_MARKERS:
        if s in head:
            problems.append(f"metadata marker string {s!r} present")
    return problems


def jpeg_dimensions(data: bytes):
    """Return (width, height) from the JPEG's start-of-frame segment, or None if it cannot be found."""
    try:
        for m, payload in jpeg_segments(data):
            if m in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
                h, w = struct.unpack(">HH", payload[1:5])
                return w, h
    except Exception:
        return None
    return None
