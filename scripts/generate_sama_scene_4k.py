"""
4K Sun-Bleached Light Wasteland Master Scene Generator via TeamoRouter (GPT-Image-2.6 Sunburst 4K Max)
------------------------------------------------------------------------------------------------------
Pure organic text-to-image 4K (3840x2160) cinematic environment film plate (NO blocky primitive blockout!)
featuring a naturally weathered, elevated broken pale-concrete overpass/terrace edge on the right half
overlooking a vast, poetic, sun-bleached pale wasteland ruined city stretching into misty backlight on the left,
matching BV1UHs56DEr2 desaturated airy Japanese film lighting + exact 2320x1080 SAMA ZW360 Ultra preview crop.
"""

import argparse
import base64
import json
import os
import time
import urllib.request
from pathlib import Path
import requests
from PIL import Image

BASE_DIR = Path(__file__).resolve().parent.parent
ASSETS_DIR = BASE_DIR / "assets"
ART_DIR = BASE_DIR / "preview"

SCENE_PROMPT = (
    "Breathtaking native 4K photorealistic cinematic 3D CG film environment plate rendered with Unreal Engine 5 Lumen / "
    "Octane path-traced realism at MAXIMUM micro-detail clarity, photographed on an ARRI Alexa 65 with a 50mm f/1.4 "
    "cinema prime lens and Black Pro-Mist 1/2 optical diffusion filter (STRICTLY PURE EMPTY ENVIRONMENT — ZERO PEOPLE, "
    "ZERO CHARACTERS, ZERO WEAPONS, ZERO TEXT, ZERO UI, ZERO WATERMARKS, ZERO ARTIFICIAL STUDIO BOXES OR NEAT CUBES). "
    "NATURAL ASYMMETRIC ORGANIC ARCHITECTURE & WASTELAND GEOGRAPHY (POETIC SUN-BLEACHED LIGHT WASTELAND LIKE NIER: "
    "AUTOMATA'S SUNLIT WHITE RUINS MEETS MAKOTO SHINKAI / SHUNJI IWAI JAPANESE CINEMA — NEVER GEOMETRIC, NEVER NEAT "
    "RECTANGULAR PLINTHS, NEVER SYMMETRICAL PILLARS, NEVER DARK MUDDY GRIME): "
    "- FOREGROUND ELEVATED BROKEN TERRACE EDGE (Right Half, x=48% to 100%, Vertical Height Around Lower-Middle Third): "
    "The naturally fractured, cantilevered pale-concrete edge of a weathered, abandoned elevated rooftop walkway / "
    "collapsed highway sky-terrace jutting organically from the right side of the frame high above an open, sunlit "
    "sunken ruined valley below — leaving open airy depth beneath the drop-off edge so someone seated on its worn "
    "right-hand rim could naturally dangle their legs freely into the breezy open air. The broken concrete parapet "
    "has organic asymmetric weathering: naturally chipped undulating stone bevels, hairline moss-free sun-bleached "
    "cracks, windblown pale chalk dust, small scattered limestone pebbles, a few bent rusty-pale rebar rods protruding "
    "naturally ONLY from the jagged fractured far-left break-off tip, and slender asymmetrical clusters of sun-bleached "
    "silver-blonde wild pampas grass, dry foxtail stalks, and tiny delicate white wildflowers swaying softly from "
    "fissures along the far-left fracture and far-right corner — leaving the smooth weathered pale-concrete seating "
    "rim on the right-center cleanly worn and unobstructed. "
    "- EXPANSIVE LAYERED PALE WASTELAND VISTA (Left Half & Deep Background): "
    "Stretching organically across the left half and sweeping deep into the misty distance is a vast, breathtakingly "
    "quiet, sun-bleached white-and-dove-grey ruined coastal/urban wasteland reclaimed gently by decades of wind and "
    "pale wild flora: curving collapsed elevated highway ribbons sloping naturally down into overgrown pale-stone "
    "rubble hills, weathered asymmetric concrete overpass fragments draped in pale bleached vines, distant tilted "
    "ivory-grey skeletal skyscraper husks, broken modernist concrete domes, and faint weathered radio towers dissolving "
    "across 5 natural atmospheric haze planes into a luminous, vast morning sky. Every shape is authentically broken, "
    "weathered, irregular, and organically settled by gravity and time — ZERO neat boxes, ZERO uniform vertical cylinders! "
    "- SIGNATURE LIGHTING & COLOR GRADING (BV1UHs56DEr2 AIRY JAPANESE FILM AESTHETIC FOR A PURE-WHITE PC CASE): "
    "Ultra-refined DESATURATED COOL-LIGHT FILM PALETTE (-25% saturation: chalky bone-white, pale sun-washed ivory "
    "limestone, muted silver-slate grey, misty pale ice-blue morning horizon, lifted translucent milky cool-grey shadows "
    "with ZERO heavy black shadows and ZERO dark gloomy brown apocalypse mud). EXTREME BLOWN-OUT MILKY-WHITE MORNING "
    "SUNLIGHT BACKLIGHTING pouring softly from upper-left through the misty ruined city skyline, wrapping the broken "
    "concrete terrace rim, swaying pale wild grass plumes, and drifting white dandelion fluff / luminous airborne dust "
    "motes in ethereal backlit halation and silky Black Pro-Mist 1/2 optical veiling glare. "
    "- CINEMATIC SHALLOW DEPTH OF FIELD (f/1.4): Only the weathered foreground pale-concrete terrace rim on the right "
    "is in crisp tactile 4K focus, while the entire left-side collapsed highway valley, overgrown ruins, and distant "
    "sunlit pale wasteland skyline melt progressively into lush, dreamy, buttery creamy optical bokeh, finished with "
    "whisper-fine organic 35mm film grain."
)


def is_true_max(resp_dict: dict) -> bool:
    usage = resp_dict.get("usage") or {}
    if usage.get("usage_source") == "chatgpt2api_worker":
        return False
    out_tok = usage.get("output_tokens") or usage.get("output_image_tokens") or 0
    return resp_dict.get("quality") == "max" or out_tok >= 8000


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="gpt-image-2.6-sunburst-4k-upscale")
    parser.add_argument("--size", default="3840x2160")
    parser.add_argument("--quality", default="max")
    parser.add_argument("--require-max", action="store_true")
    parser.add_argument("--max-tries", type=int, default=3)
    args = parser.parse_args()

    base_url = (os.environ.get("TEAMOROUTER_IMAGE_BASE_URL") or "https://api.teamorouter.com/v1").rstrip("/")
    api_key = os.environ.get("TEAMOROUTER_IMAGE_API_KEY") or os.environ.get("TEAMOROUTER_API_KEY")
    if not api_key:
        raise SystemExit("Missing TEAMOROUTER_IMAGE_API_KEY / TEAMOROUTER_API_KEY.")

    endpoint = f"{base_url}/images/generations"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model": args.model,
        "prompt": SCENE_PROMPT,
        "size": args.size,
        "quality": args.quality,
        "complexity": "high",
        "output_format": "png",
        "n": 1,
    }
    print(f"[RUN] POST {endpoint} model={args.model} size={args.size} quality={args.quality} mode=pure-organic-t2i")

    best_resp = None
    tries = args.max_tries if args.require_max else 1
    for t in range(1, tries + 1):
        resp = None
        for attempt in range(1, 3):
            try:
                resp = requests.post(endpoint, headers=headers, json=payload, timeout=360)
                break
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectionError) as exc:
                print(f"[WARN] transient connection drop on attempt {attempt}: {exc}")
                if attempt == 2:
                    raise SystemExit(f"Connection failed: {exc}")
                time.sleep(3)

        if resp.status_code != 200:
            raise SystemExit(f"HTTP {resp.status_code}: {resp.text[:800]}")
        data = resp.json()
        best_resp = data
        if is_true_max(data):
            print(f"[MAX_OK] Confirmed true high-sampling quality=max backend on try {t}/{tries}!")
            break
        usage = data.get("usage") or {}
        print(f"[WARN] Try {t}/{tries} hit lower-sampling backend (usage_source={usage.get('usage_source')}, output_tokens={usage.get('output_tokens')}).")
        if t < tries:
            time.sleep(2)

    meta = {k: v for k, v in best_resp.items() if k != "data"}
    item = best_resp["data"][0]
    item_meta = {k: v for k, v in item.items() if k not in ("b64_json", "url")}
    print(f"[META] top={json.dumps(meta, ensure_ascii=False)} item={json.dumps(item_meta, ensure_ascii=False)}")

    if item.get("b64_json"):
        raw_bytes = base64.b64decode(item["b64_json"])
    elif item.get("url"):
        req = urllib.request.Request(item["url"], headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=180) as r:
            raw_bytes = r.read()
    else:
        raise RuntimeError(f"Unexpected response keys: {list(item.keys())}")

    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    ART_DIR.mkdir(parents=True, exist_ok=True)

    out_ws = ASSETS_DIR / "04_scene_light_wasteland_4k.png"
    out_art = ART_DIR / "04_scene_light_wasteland_4k.png"
    out_ws.write_bytes(raw_bytes)
    out_art.write_bytes(raw_bytes)

    with Image.open(out_ws) as im:
        w, h = im.size
        print(f"[OK] Saved 4K Light Wasteland Scene -> {out_ws.name} {im.size} ({len(raw_bytes)/1024/1024:.2f} MB)")
        # Also save exact 2320x1080 (2.15:1) SAMA ZW360 Ultra center-cropped preview!
        crop_h = int(round(w * 1080 / 2320))  # 3840 -> 1788px
        y0 = (h - crop_h) // 2
        sama_crop = im.crop((0, y0, w, y0 + crop_h)).resize((2320, 1080), Image.Resampling.LANCZOS)
        crop_ws = ASSETS_DIR / "04_scene_light_wasteland_sama_2320x1080.png"
        crop_art = ART_DIR / "04_scene_light_wasteland_sama_2320x1080.png"
        sama_crop.save(crop_ws, quality=96)
        sama_crop.save(crop_art, quality=96)
        print(f"[OK] Saved 2320x1080 SAMA crop preview -> {crop_ws.name}")


if __name__ == "__main__":
    main()
