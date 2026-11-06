"""Validate reference pixels before SDK startup; never infer MIME from suffix alone."""
import base64
import hashlib
import io
from pathlib import Path
import warnings
import json
from PIL import Image, ImageOps

FORMATS = {'PNG': ('image/png', {'.png'}), 'JPEG': ('image/jpeg', {'.jpg', '.jpeg'}),
           'WEBP': ('image/webp', {'.webp'}), 'GIF': ('image/gif', {'.gif'})}


def attachment_order(project, images):
    """Preserve the UI's upload sequence across reference/site/brief categories."""
    path=Path(project)/'state/project_context.json'
    if not path.is_file():return list(images)
    context=json.loads(path.read_text(encoding='utf-8'))
    order={}
    for reference in context.get('references',[]):
        if isinstance(reference,dict) and isinstance(reference.get('source'),str):
            order.setdefault((Path(project)/reference['source']).resolve(),len(order))
    return sorted(images,key=lambda p:order.get(Path(p).resolve(),len(order)))


def image_block(path, *, max_bytes=25 * 1024 * 1024, max_pixels=40_000_000):
    path = Path(path)
    if path.stat().st_size > max_bytes:
        raise ValueError('参考图片超过允许文件大小。')
    raw = path.read_bytes()
    with warnings.catch_warnings():
        warnings.simplefilter('error', Image.DecompressionBombWarning)
        try:
            with Image.open(io.BytesIO(raw)) as check:
                fmt = check.format
                if fmt not in FORMATS or path.suffix.lower() not in FORMATS[fmt][1]:
                    raise ValueError('图片内容与扩展名不一致或格式不支持。')
                if check.width * check.height > max_pixels:
                    raise ValueError('参考图片解码尺寸过大。')
                check.verify()
            with Image.open(io.BytesIO(raw)) as original:
                original.seek(0)
                orientation = original.getexif().get(274, 1)
                convert = fmt == 'GIF' or orientation != 1
                size = [original.width, original.height]
                if convert:
                    normalized = ImageOps.exif_transpose(original).convert('RGBA')
                    out = io.BytesIO(); normalized.save(out, format='PNG'); payload = out.getvalue()
                    mime = 'image/png'
                else:
                    original.load(); payload = raw; mime = FORMATS[fmt][0]
        except (OSError, SyntaxError, Image.DecompressionBombWarning, Image.DecompressionBombError) as e:
            raise ValueError('图片损坏或解码尺寸不安全。') from e
    if len(payload) > max_bytes:
        raise ValueError('图片规范化后超过请求大小限制。')
    return ({'type': 'image', 'data': base64.b64encode(payload).decode(), 'mimeType': mime},
            {'original_sha256': hashlib.sha256(raw).hexdigest(),
             'sent_sha256': hashlib.sha256(payload).hexdigest(), 'original_format': fmt,
             'sent_mime': mime, 'original_size': size, 'exif_orientation': orientation,
             'conversion': 'first_frame_and_exif_to_png' if fmt == 'GIF' else 'exif_to_png' if convert else 'none',
             'frame': 0 if fmt == 'GIF' else None, 'original_preserved': True})
