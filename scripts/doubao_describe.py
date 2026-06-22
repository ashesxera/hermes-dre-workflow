#!/usr/bin/env python3
"""
使用 doubao-seed-2.0-pro 模型描述图片内容。

用法:
    python3 doubao_describe.py <图片路径>
    python3 doubao_describe.py /path/to/image.png
    python3 doubao_describe.py /path/to/image.png "用中文描述这张图"

依赖: requests
    pip3 install requests
"""

import sys
import base64
import json
import os
from pathlib import Path

# ── 配置 ──────────────────────────────────────────────
API_KEY = "ark-8f7324a8-b8a5-47a6-8c1c-02f7f958e576-a19c0"
BASE_URL = "https://ark.cn-beijing.volces.com/api/coding/v3/chat/completions"
MODEL = "doubao-seed-2.0-pro"
# ───────────────────────────────────────────────────────


def encode_image(image_path: str) -> tuple[str, str]:
    """将图片编码为 base64 data URI，返回 (data_uri, mime_type)"""
    path = Path(image_path)
    if not path.exists():
        print(f"❌ 文件不存在: {image_path}", file=sys.stderr)
        sys.exit(1)

    ext = path.suffix.lower()
    mime_map = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
        ".gif": "image/gif",
        ".bmp": "image/bmp",
    }
    mime_type = mime_map.get(ext, "image/png")

    with open(path, "rb") as f:
        data = base64.b64encode(f.read()).decode("utf-8")

    data_uri = f"data:{mime_type};base64,{data}"
    return data_uri, mime_type


def describe_image(image_path: str, prompt: str = "请详细描述这张图片的内容、风格和细节") -> str:
    """调用 doubao-seed-2.0-pro 描述图片"""
    import requests

    data_uri, mime_type = encode_image(image_path)

    payload = {
        "model": MODEL,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": data_uri},
                    },
                    {
                        "type": "text",
                        "text": prompt,
                    },
                ],
            }
        ],
        "max_tokens": 2000,
        "temperature": 0.3,
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}",
    }

    print(f"📤 正在调用 {MODEL}...", file=sys.stderr)
    print(f"📷 图片: {image_path} ({os.path.getsize(image_path) / 1024:.1f} KB)", file=sys.stderr)

    try:
        resp = requests.post(BASE_URL, headers=headers, json=payload, timeout=120)
    except requests.exceptions.ConnectionError as e:
        print(f"❌ 连接失败: {e}", file=sys.stderr)
        sys.exit(1)
    except requests.exceptions.Timeout:
        print(f"❌ 请求超时 (120s)", file=sys.stderr)
        sys.exit(1)

    if resp.status_code != 200:
        print(f"❌ HTTP {resp.status_code}: {resp.text[:500]}", file=sys.stderr)
        sys.exit(1)

    result = resp.json()

    try:
        content = result["choices"][0]["message"]["content"]
    except (KeyError, IndexError) as e:
        print(f"❌ 解析响应失败: {e}", file=sys.stderr)
        print(json.dumps(result, ensure_ascii=False, indent=2)[:1000], file=sys.stderr)
        sys.exit(1)

    usage = result.get("usage", {})
    if usage:
        print(
            f"📊 tokens: prompt={usage.get('prompt_tokens', '?')} "
            f"completion={usage.get('completion_tokens', '?')} "
            f"total={usage.get('total_tokens', '?')}",
            file=sys.stderr,
        )

    return content


def main():
    if len(sys.argv) < 2:
        print(f"用法: python3 {sys.argv[0]} <图片路径> [提示词]", file=sys.stderr)
        print(f"示例: python3 {sys.argv[0]} photo.png", file=sys.stderr)
        print(f"示例: python3 {sys.argv[0]} photo.png '用中文描述'", file=sys.stderr)
        sys.exit(1)

    image_path = sys.argv[1]
    prompt = sys.argv[2] if len(sys.argv) > 2 else "请详细描述这张图片的内容、风格和细节"

    description = describe_image(image_path, prompt)

    print()
    print("=" * 60)
    print(description)
    print("=" * 60)


if __name__ == "__main__":
    main()
