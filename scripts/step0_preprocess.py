#!/usr/bin/env python3
"""
Step 0 — Reference Image Preprocessing for DRE Workflow.

Calls Meshy's gpt-image-2 image-to-image endpoint to clean up the
reference image before it enters the DRE pipeline.

Cleans:
  - Background: replaces cluttered/complex backgrounds with pure white
  - Facial features: removes eyes, nose, mouth, eyebrows, blush
  - Floating props: removes decorative elements suspended in the air
  - Hair issues: simplifies overly curly/wispy/translucent hair into
    solid vinyl-friendly masses with rounded blunt tips — suitable for
    3D printing / vinyl toy production

Usage:
  python3 step0_preprocess.py <input_reference.png> <output_dir>

Output:
  <output_dir>/reference_clean.png   — preprocessed reference image
  <output_dir>/step0_prompt.md      — the prompt used
  <output_dir>/step0_result.json    — raw API response

Config: reads Meshy API key/model from ~/.hermes/config.yaml
        (image_gen section with provider=meshy)
"""

import base64
import json
import mimetypes
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, Optional

import requests
import yaml


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

MESHY_BASE_URL = "https://api.meshy.ai"
DEFAULT_MODEL = "gpt-image-2"
MAX_POLL_ATTEMPTS = 3
POLL_INTERVAL = 40.0  # seconds


def load_meshy_config() -> Dict[str, str]:
    """Load Meshy API credentials.
    
    Priority: MESHY_API_KEY env var > image_gen config (if provider=meshy) > error.
    Base URL is always api.meshy.ai — never overridden from image_gen config
    because Step 0 specifically calls Meshy's image-to-image endpoint.
    """
    config_path = Path.home() / ".hermes" / "config.yaml"
    api_key = os.getenv("MESHY_API_KEY", "")
    model = os.getenv("MESHY_MODEL", DEFAULT_MODEL)

    if not api_key and config_path.exists():
        with open(config_path) as f:
            cfg = yaml.safe_load(f) or {}
        ig = cfg.get("image_gen", {})
        if isinstance(ig, dict):
            api_key = ig.get("api_key", "")
            model = ig.get("model", DEFAULT_MODEL)

    return {
        "api_key": api_key,
        "model": model,
        "base_url": MESHY_BASE_URL,  # always api.meshy.ai, never from config
    }


# ---------------------------------------------------------------------------
# Image encoding
# ---------------------------------------------------------------------------

def encode_image_to_b64(image_path: str) -> Optional[str]:
    """Encode a local image file to base64 data URI."""
    path = Path(image_path).expanduser()
    if not path.exists():
        print(f"ERROR: Image not found: {path}", file=sys.stderr)
        return None

    mime_type, _ = mimetypes.guess_type(str(path))
    if not mime_type or not mime_type.startswith("image/"):
        mime_type = "image/png"

    data = path.read_bytes()
    b64 = base64.b64encode(data).decode("ascii")
    return f"data:{mime_type};base64,{b64}"


# ---------------------------------------------------------------------------
# Prompt
# ---------------------------------------------------------------------------

PREPROCESS_PROMPT = """\
Clean up this character reference image for vinyl toy production:

BACKGROUND:
- Replace the entire background with pure white (#FFFFFF).
- Remove ALL background elements: patterns, gradients, sparkles,
  stars, hearts, text, decorative frames, scenery, floors, shadows.

FACE:
- Remove ALL facial features completely: eyes, eyebrows, nose,
  mouth, blush, freckles, beauty marks.
- The face becomes a completely blank smooth surface — like an
  unpainted vinyl doll head.
- Keep the face shape and skin tone unchanged.

FLOATING ELEMENTS:
- Remove ALL objects floating in the air: sparkles, stars, hearts,
  petals, ribbons, magical effects, dust particles.
- Objects that are HELD by the character (in hands) or WORN on the
  body should be KEPT.

HAIR:
- Simplify overly curly, wispy, or flyaway hair into solid,
  smooth, rounded masses — like molded vinyl plastic.
- Remove translucent/see-through hair effects. Hair must be opaque.
- Round off sharp or pointed hair tips into blunt rounded ends.
- Remove individual hair strands — replace with solid sculpted blocks.
- Keep the overall hairstyle silhouette and color.

CHARACTER:
- Keep the character's body, pose, clothing, accessories, and props
  exactly as they are — do NOT change proportions, colors, or design.
- The character should remain fully recognizable.

OUTPUT:
- Clean product-photo style on pure white background.
- No text, no watermark, no logo.
- The result should look like a clean reference sheet for a
  vinyl toy / 3D print production.
"""


# ---------------------------------------------------------------------------
# API call
# ---------------------------------------------------------------------------

def submit_task(
    base_url: str,
    api_key: str,
    model: str,
    image_b64: str,
    prompt: str,
) -> Optional[str]:
    """Submit image-to-image task to Meshy, return task_id."""
    url = f"{base_url}/openapi/v1/image-to-image"
    payload = {
        "ai_model": model,
        "prompt": prompt,
        "reference_image_urls": [image_b64],
    }

    resp = requests.post(
        url,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    task_id = data.get("result")
    if not task_id:
        print(f"ERROR: No task_id in response: {json.dumps(data)[:500]}", file=sys.stderr)
        return None
    return task_id


def poll_task(
    base_url: str,
    api_key: str,
    task_id: str,
) -> Optional[Dict[str, Any]]:
    """Poll Meshy task until completion, return task data."""
    url = f"{base_url}/openapi/v1/image-to-image/{task_id}"

    for attempt in range(MAX_POLL_ATTEMPTS):
        time.sleep(POLL_INTERVAL)
        try:
            resp = requests.get(
                url,
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()
            status = data.get("status", "")

            if status == "SUCCEEDED":
                return data
            elif status in ("FAILED", "EXPIRED", "CANCELLED"):
                error_msg = data.get("error", {}).get("message", f"Task {status}")
                print(f"ERROR: Task {task_id} {status}: {error_msg}", file=sys.stderr)
                return None

            print(f"  Poll {attempt + 1}/{MAX_POLL_ATTEMPTS}: status={status} "
                  f"progress={data.get('progress', 0)}%")

        except requests.HTTPError as e:
            print(f"ERROR: Poll HTTP {e.response.status_code}: {e.response.text[:300]}",
                  file=sys.stderr)
            return None
        except Exception as e:
            print(f"  Poll attempt {attempt + 1} failed: {e}", file=sys.stderr)
            continue

    print(f"ERROR: Task {task_id} timed out after {MAX_POLL_ATTEMPTS * POLL_INTERVAL}s",
          file=sys.stderr)
    return None


def download_image(image_url: str, output_path: Path) -> bool:
    """Download image from URL to local path."""
    try:
        resp = requests.get(image_url, timeout=60)
        resp.raise_for_status()
        output_path.write_bytes(resp.content)
        return True
    except Exception as e:
        print(f"ERROR: Failed to download image: {e}", file=sys.stderr)
        return False


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    if len(sys.argv) < 3:
        print("Usage: python3 step0_preprocess.py <input_reference.png> <output_dir>",
              file=sys.stderr)
        sys.exit(1)

    input_path = sys.argv[1]
    output_dir = Path(sys.argv[2]).expanduser()
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load config
    cfg = load_meshy_config()
    if not cfg["api_key"]:
        print("ERROR: No Meshy API key found. Set image_gen.api_key in "
              "~/.hermes/config.yaml or MESHY_API_KEY env var.", file=sys.stderr)
        sys.exit(1)

    print(f"Step 0: Preprocessing reference image")
    print(f"  Input:  {input_path}")
    print(f"  Output: {output_dir}")
    print(f"  Model:  {cfg['model']}")
    print(f"  API:    {cfg['base_url']}")

    # Encode image
    print("  Encoding reference image...")
    image_b64 = encode_image_to_b64(input_path)
    if not image_b64:
        sys.exit(1)
    print(f"  Encoded: {len(image_b64)} chars")

    # Submit task
    print("  Submitting image-to-image task...")
    task_id = submit_task(
        base_url=cfg["base_url"],
        api_key=cfg["api_key"],
        model=cfg["model"],
        image_b64=image_b64,
        prompt=PREPROCESS_PROMPT,
    )
    if not task_id:
        sys.exit(1)
    print(f"  Task ID: {task_id}")

    # Poll
    print(f"  Polling (max {MAX_POLL_ATTEMPTS} × {POLL_INTERVAL}s)...")
    task_data = poll_task(
        base_url=cfg["base_url"],
        api_key=cfg["api_key"],
        task_id=task_id,
    )
    if not task_data:
        sys.exit(1)

    # Download result
    image_urls = task_data.get("image_urls", [])
    if not image_urls:
        print("ERROR: Task succeeded but no image_urls returned", file=sys.stderr)
        sys.exit(1)

    output_path = output_dir / "reference_clean.png"
    print(f"  Downloading result to {output_path}...")
    if not download_image(image_urls[0], output_path):
        sys.exit(1)

    # Save artifacts
    prompt_path = output_dir / "step0_prompt.md"
    prompt_path.write_text(f"# Step 0 Preprocessing Prompt\n\n```\n{PREPROCESS_PROMPT}\n```\n")
    print(f"  Saved prompt to {prompt_path}")

    result_path = output_dir / "step0_result.json"
    result_path.write_text(json.dumps(task_data, indent=2))
    print(f"  Saved result to {result_path}")

    print(f"\n✅ Step 0 complete: {output_path}")
    print(f"   Size: {output_path.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()
