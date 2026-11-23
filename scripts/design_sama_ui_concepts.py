"""
Screen 2 (SAMA ZW360 Ultra 6.8" Curved OLED, 2320x1080) — Luxury Frameless UI Concept Designer (v2 Large-Scale)
--------------------------------------------------------------------------------------------------------------
Up-scaled typography tuned for real 60-90cm desk viewing distance through tempered PC glass:
  - Right telemetry wing widened cleanly to x = 1585..2255 (670px wide, still 100% clear of the
    heroine on the left x = 0..1510 across ALL 3 shots!).
  - Edition A ("horology_full"):    Complete Haute-Horlogerie Telemetry Suite (larger hero & spec fonts!)
  - Edition B ("editorial_minimal"): Ultra-Pure Gallery Minimal Edition (giant sculptural clock + bold temps!)
"""

import os
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

BASE_DIR = Path(__file__).resolve().parent.parent
HFLIP_DIR = BASE_DIR / "assets" / "frames"
OUT_DIR = BASE_DIR / "preview"
ART_DIR = BASE_DIR / "preview"
FONT_DIR = Path(r"C:\Windows\Fonts")
SAMA_FONT_DIR = Path(os.environ.get("SAMA_ROOT", r"C:\SAMA_Multi_Chn")) / "fonts"

OUT_DIR.mkdir(parents=True, exist_ok=True)
ART_DIR.mkdir(parents=True, exist_ok=True)

W, H = 2320, 1080

SLATE_SHADOW = (12, 22, 40)
VEIL_TINT = (14, 24, 42)
PLAT_TOP = np.array([255.0, 255.0, 255.0], dtype=np.float32)
PLAT_BOT = np.array([228.0, 238.0, 250.0], dtype=np.float32)
GOLD_TOP = np.array([255.0, 247.0, 218.0], dtype=np.float32)
GOLD_MID = np.array([250.0, 224.0, 162.0], dtype=np.float32)
GOLD_BOT = np.array([216.0, 174.0, 102.0], dtype=np.float32)
PEARL_SUB = np.array([240.0, 245.0, 252.0], dtype=np.float32)


def find_font_file(candidates: list[str]) -> Path:
    for c in candidates:
        for root in (SAMA_FONT_DIR, FONT_DIR):
            p = root / c
            if p.exists():
                return p
    raise FileNotFoundError(f"None of {candidates} found in {SAMA_FONT_DIR} or {FONT_DIR}")


def load_font(candidates: list[str], size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(find_font_file(candidates)), size)


def draw_tracked_text(mask_draw: ImageDraw.ImageDraw, x: int, y: int, text: str, font: ImageFont.FreeTypeFont, tracking: float = 0.0, align: str = "left") -> tuple[int, int]:
    widths = [font.getlength(ch) for ch in text]
    total_w = sum(widths) + tracking * max(0, len(text) - 1)
    if align == "right":
        cur_x = x - total_w
    elif align == "center":
        cur_x = x - total_w / 2.0
    else:
        cur_x = float(x)
    x_start = int(round(cur_x))
    for i, ch in enumerate(text):
        mask_draw.text((cur_x, y), ch, font=font, fill=255)
        cur_x += widths[i] + tracking
    return x_start, int(round(x_start + total_w))


def colorize_vertical_gradient(mask_l: Image.Image, y0: int, y1: int, c_top: np.ndarray, c_bot: np.ndarray, c_mid: np.ndarray | None = None, opacity: float = 1.0) -> Image.Image:
    a = np.clip(np.asarray(mask_l, dtype=np.float32) * opacity, 0, 255).astype(np.uint8)
    yy = np.arange(H, dtype=np.float32)[:, None]
    t = np.clip((yy - float(y0)) / max(1.0, float(y1 - y0)), 0.0, 1.0)
    if c_mid is None:
        rgb_col = c_top[None, None, :] * (1.0 - t[..., None]) + c_bot[None, None, :] * t[..., None]
    else:
        t1 = np.clip(t * 2.0, 0.0, 1.0)[..., None]
        t2 = np.clip((t - 0.5) * 2.0, 0.0, 1.0)[..., None]
        upper = c_top[None, None, :] * (1.0 - t1) + c_mid[None, None, :] * t1
        lower = c_mid[None, None, :] * (1.0 - t2) + c_bot[None, None, :] * t2
        rgb_col = np.where((t < 0.5)[..., None], upper, lower)
    rgb = np.broadcast_to(rgb_col, (H, W, 3)).astype(np.uint8)
    return Image.fromarray(np.dstack([rgb, a]), mode="RGBA")


def composite_luminous(base: Image.Image, fg_rgba: Image.Image, sh_alpha: float = 0.78, bloom_alpha: float = 0.20) -> Image.Image:
    alpha = fg_rgba.split()[3]
    sh_a = np.clip(np.asarray(alpha, dtype=np.float32) * sh_alpha, 0, 255).astype(np.uint8)
    sh = Image.new("RGBA", fg_rgba.size, (*SLATE_SHADOW, 0))
    sh.putalpha(Image.fromarray(sh_a, mode="L"))

    sh_wide = Image.new("RGBA", fg_rgba.size, (0, 0, 0, 0))
    sh_wide.paste(sh.filter(ImageFilter.GaussianBlur(radius=8.5)), (0, 5))

    sh_tight = Image.new("RGBA", fg_rgba.size, (0, 0, 0, 0))
    sh_tight.paste(sh.filter(ImageFilter.GaussianBlur(radius=2.0)), (0, 2))

    fg_arr = np.asarray(fg_rgba, dtype=np.float32)
    bl_arr = fg_arr.copy()
    bl_arr[..., 3] = np.clip(bl_arr[..., 3] * bloom_alpha, 0, 255)
    bloom = Image.fromarray(bl_arr.astype(np.uint8), mode="RGBA").filter(ImageFilter.GaussianBlur(radius=4.0))

    out = Image.alpha_composite(base, sh_wide)
    out = Image.alpha_composite(out, sh_tight)
    out = Image.alpha_composite(out, bloom)
    out = Image.alpha_composite(out, fg_rgba)
    return out


def make_right_atmospheric_veil(x_start: float = 1320.0, x_full: float = 1710.0, max_alpha: float = 0.52, sun_boost: float = 0.18, y_top_fade: bool = False) -> Image.Image:
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    tx = np.clip((xx - x_start) / max(1.0, x_full - x_start), 0.0, 1.0)
    wx = 0.5 - 0.5 * np.cos(np.pi * tx)
    sun_orb = np.exp(-(((xx - 2080.0) / 380.0) ** 2 + ((yy - 185.0) / 240.0) ** 2)) * sun_boost
    if y_top_fade:
        top_zone = np.exp(-(((yy - 210.0) / 225.0) ** 2)) * 0.96
        bot_zone = np.clip((yy - 430.0) / 210.0, 0.0, 1.0)
        wy = np.maximum(top_zone, bot_zone)
    else:
        wy = 1.0
    alpha_f = np.clip(wx * wy * max_alpha + wx * sun_orb, 0.0, 0.64)
    rgba = np.zeros((H, W, 4), dtype=np.uint8)
    rgba[..., 0] = VEIL_TINT[0]
    rgba[..., 1] = VEIL_TINT[1]
    rgba[..., 2] = VEIL_TINT[2]
    rgba[..., 3] = np.clip(alpha_f * 255.0, 0, 255).astype(np.uint8)
    return Image.fromarray(rgba, mode="RGBA")


def draw_hairline_rule(arr: np.ndarray, x0: int, x1: int, y: int, color: tuple[int, int, int], max_a: int, ticks: int = 0, diamond_x: int | None = None):
    length = max(1, x1 - x0)
    for px in range(x0, x1):
        t = (px - x0) / float(length)
        w = min(1.0, t / 0.12) * min(1.0, (1.0 - t) / 0.05)
        a = int(max_a * w)
        if a > 0 and 0 <= y < H:
            arr[y, px] = (color[0], color[1], color[2], max(int(arr[y, px, 3]), a))
            if y + 1 < H:
                arr[y + 1, px] = (color[0], color[1], color[2], max(int(arr[y + 1, px, 3]), int(a * 0.50)))
    if ticks > 1:
        for i in range(ticks):
            tx = int(round(x0 + (x1 - x0) * (i / float(ticks - 1))))
            th = 7 if i in (0, ticks - 1, ticks // 2) else 4
            for dy in range(-th, 1):
                if 0 <= y + dy < H and 0 <= tx < W:
                    arr[y + dy, tx] = (color[0], color[1], color[2], max(int(arr[y + dy, tx, 3]), int(max_a * 0.88)))
    if diamond_x is not None:
        r = 5
        for dy in range(-r, r + 1):
            for dx in range(-r, r + 1):
                if abs(dx) + abs(dy) <= r and 0 <= y + dy < H and 0 <= diamond_x + dx < W:
                    arr[y + dy, diamond_x + dx] = (255, 240, 192, 240)


def draw_bar_track_and_fill(arr: np.ndarray, x0: int, x1: int, y: int, h: int, pct: float, fill_col: tuple[int, int, int]):
    arr[y:y + h, x0:x1] = (255, 255, 255, 54)
    arr[y - 3:y + h + 3, x0:x0 + 2] = (255, 255, 255, 130)
    arr[y - 3:y + h + 3, x1 - 2:x1] = (255, 255, 255, 130)
    fw = max(3, int(round((x1 - x0) * pct)))
    arr[y:y + h, x0:x0 + fw] = (*fill_col, 242)
    tip_x = min(x1 - 3, x0 + fw - 3)
    arr[y - 1:y + h + 1, tip_x:tip_x + 3] = (255, 252, 242, 255)


def render_edition_a() -> tuple[Image.Image, Image.Image]:
    """
    Edition A (Large-Scale): Haute Horlogerie Full Telemetry (Matched Twin to Screen 1 PlatinumBlade_A)
    Sculptural oversized numerals readable effortlessly from 80cm behind tempered PC glass!
    """
    f_butler_clock = load_font(["Butler_Ultra_Light.otf"], 184)
    f_butler_temp  = load_font(["Butler_Ultra_Light.otf"], 138)
    f_futura_cap   = load_font(["Futura LT Book.ttf", "KumbhSans-Light.ttf"], 24)
    f_futura_sm    = load_font(["Futura LT Book.ttf", "KumbhSans-Light.ttf"], 19)
    f_helv_mid     = load_font(["HelveticaNeueLTPro-LtCn.otf", "KumbhSans-Light.ttf", "arial.ttf"], 66)
    f_helv_spec    = load_font(["HelveticaNeueLTPro-LtCn.otf", "KumbhSans-Light.ttf", "arial.ttf"], 34)
    f_helv_date    = load_font(["HelveticaNeueLTPro-LtCn.otf", "KumbhSans-Light.ttf", "arial.ttf"], 32)
    f_cn           = load_font(["NotoSerifSC-SemiBold.otf", "NotoSerifSC-Medium.otf", "msyh.ttc"], 26)

    X_L = 1585
    X_R = 2255

    static = make_right_atmospheric_veil(x_start=1300.0, x_full=1680.0, max_alpha=0.52, sun_boost=0.19)
    geom = np.zeros((H, W, 4), dtype=np.uint8)

    # Vertical architectural datum spine
    for py in range(74, 1006):
        t = (py - 74) / 932.0
        w = min(1.0, t / 0.07) * min(1.0, (1.0 - t) / 0.07)
        geom[py, X_L - 28] = (255, 240, 200, int(78 * w))

    # Horizontal Leica hairline rules separating 4 bold editorial tiers
    draw_hairline_rule(geom, X_L, X_R, 102, (250, 224, 162), 195, diamond_x=X_L + 5)
    draw_hairline_rule(geom, X_L, X_R, 348, (240, 246, 255), 150, ticks=9)
    draw_hairline_rule(geom, X_L, X_R, 608, (240, 246, 255), 130, ticks=5)
    draw_hairline_rule(geom, X_L, X_R, 856, (250, 224, 162), 155, diamond_x=X_L + 332)
    static = Image.alpha_composite(static, Image.fromarray(geom, mode="RGBA"))

    # Static micro-labels & Chinese editorial seal
    m_gold_lbl = Image.new("L", (W, H), 0)
    dg = ImageDraw.Draw(m_gold_lbl)
    draw_tracked_text(dg, X_L + 22, 60, "CHRONO · SYSTEM", f_futura_cap, tracking=5.0, align="left")
    draw_tracked_text(dg, X_R, 56, "白昼残响", f_cn, tracking=8.0, align="right")

    m_plat_lbl = Image.new("L", (W, H), 0)
    dp = ImageDraw.Draw(m_plat_lbl)
    draw_tracked_text(dp, X_L, 368, "CPU · THERMAL", f_futura_cap, tracking=4.5, align="left")
    draw_tracked_text(dp, X_R, 514, "LOAD", f_futura_sm, tracking=5.0, align="right")
    draw_tracked_text(dp, X_L, 628, "GPU · THERMAL", f_futura_cap, tracking=4.5, align="left")
    draw_tracked_text(dp, X_R, 774, "LOAD", f_futura_sm, tracking=5.0, align="right")
    draw_tracked_text(dp, X_L, 876, "MEMORY · RAM", f_futura_sm, tracking=4.0, align="left")
    draw_tracked_text(dp, X_L + 356, 876, "GRAPHICS · VRAM", f_futura_sm, tracking=4.0, align="left")

    static = composite_luminous(static, colorize_vertical_gradient(m_gold_lbl, 52, 100, GOLD_TOP, GOLD_BOT, GOLD_MID), sh_alpha=0.80, bloom_alpha=0.22)
    static = composite_luminous(static, colorize_vertical_gradient(m_plat_lbl, 360, 910, PEARL_SUB, PLAT_BOT, opacity=0.92), sh_alpha=0.72, bloom_alpha=0.15)

    # Sample live telemetry layer
    full = static.copy()
    bars = np.zeros((H, W, 4), dtype=np.uint8)
    draw_bar_track_and_fill(bars, X_L, X_R, 566, 5, 0.24, (248, 220, 150))
    draw_bar_track_and_fill(bars, X_L, X_R, 822, 5, 0.36, (230, 242, 255))
    draw_bar_track_and_fill(bars, X_L, X_L + 310, 994, 4, 0.42, (248, 220, 150))
    draw_bar_track_and_fill(bars, X_L + 356, X_R, 994, 4, 0.31, (230, 242, 255))
    full = Image.alpha_composite(full, Image.fromarray(bars, mode="RGBA"))

    m_hero_plat = Image.new("L", (W, H), 0)
    dhp = ImageDraw.Draw(m_hero_plat)
    draw_tracked_text(dhp, X_R + 6, 108, "15:48", f_butler_clock, tracking=4.0, align="right")
    draw_tracked_text(dhp, X_L - 6, 656, "42°", f_butler_temp, tracking=2.0, align="left")
    draw_tracked_text(dhp, X_R, 434, "24%", f_helv_mid, tracking=1.5, align="right")
    draw_tracked_text(dhp, X_R, 364, "5420 MHz", f_helv_spec, tracking=1.5, align="right")
    draw_tracked_text(dhp, X_L, 908, "42%", f_helv_mid, tracking=1.5, align="left")
    draw_tracked_text(dhp, X_L + 356, 908, "31%", f_helv_mid, tracking=1.5, align="left")

    m_hero_gold = Image.new("L", (W, H), 0)
    dhg = ImageDraw.Draw(m_hero_gold)
    draw_tracked_text(dhg, X_R, 294, "2026 · 11 · 21", f_helv_date, tracking=3.5, align="right")
    draw_tracked_text(dhg, X_L - 6, 398, "46°", f_butler_temp, tracking=2.0, align="left")
    draw_tracked_text(dhg, X_R, 694, "36%", f_helv_mid, tracking=1.5, align="right")
    draw_tracked_text(dhg, X_R, 624, "2640 MHz", f_helv_spec, tracking=1.5, align="right")

    full = composite_luminous(full, colorize_vertical_gradient(m_hero_plat, 105, 995, PLAT_TOP, PLAT_BOT), sh_alpha=0.82, bloom_alpha=0.22)
    full = composite_luminous(full, colorize_vertical_gradient(m_hero_gold, 290, 780, GOLD_TOP, GOLD_BOT, GOLD_MID), sh_alpha=0.82, bloom_alpha=0.22)
    return static, full


def render_edition_b() -> tuple[Image.Image, Image.Image]:
    """
    Edition B (Large-Scale): Ultra-Pure Gallery Minimal Edition
    Giant sculptural clock at top + oversized clean CPU/GPU/RAM vitals nestled below,
    leaving the bright upper-middle sunlit horizon completely open!
    """
    f_butler_clock = load_font(["Butler_Ultra_Light.otf"], 196)
    f_butler_temp  = load_font(["Butler_Ultra_Light.otf"], 140)
    f_futura_cap   = load_font(["Futura LT Book.ttf", "KumbhSans-Light.ttf"], 24)
    f_futura_sm    = load_font(["Futura LT Book.ttf", "KumbhSans-Light.ttf"], 22)
    f_helv_mid     = load_font(["HelveticaNeueLTPro-LtCn.otf", "KumbhSans-Light.ttf", "arial.ttf"], 68)
    f_helv_date    = load_font(["HelveticaNeueLTPro-LtCn.otf", "KumbhSans-Light.ttf", "arial.ttf"], 34)
    f_cn           = load_font(["NotoSerifSC-SemiBold.otf", "NotoSerifSC-Medium.otf", "msyh.ttc"], 26)

    X_L = 1615
    X_R = 2255

    static = make_right_atmospheric_veil(x_start=1340.0, x_full=1730.0, max_alpha=0.49, sun_boost=0.20, y_top_fade=True)
    geom = np.zeros((H, W, 4), dtype=np.uint8)

    draw_hairline_rule(geom, X_L, X_R, 104, (250, 224, 162), 195, diamond_x=X_L + 5)
    draw_hairline_rule(geom, X_L, X_R, 476, (240, 246, 255), 150, ticks=7)
    draw_hairline_rule(geom, X_L, X_R, 926, (250, 224, 162), 155, diamond_x=X_L + 5)
    static = Image.alpha_composite(static, Image.fromarray(geom, mode="RGBA"))

    m_gold_lbl = Image.new("L", (W, H), 0)
    dg = ImageDraw.Draw(m_gold_lbl)
    draw_tracked_text(dg, X_L + 22, 62, "WASTELAND · 02", f_futura_cap, tracking=5.0, align="left")
    draw_tracked_text(dg, X_R, 58, "白昼残响", f_cn, tracking=8.0, align="right")

    m_plat_lbl = Image.new("L", (W, H), 0)
    dp = ImageDraw.Draw(m_plat_lbl)
    draw_tracked_text(dp, X_L, 496, "CPU · CORE", f_futura_cap, tracking=4.8, align="left")
    draw_tracked_text(dp, X_L, 718, "GPU · CORE", f_futura_cap, tracking=4.8, align="left")
    draw_tracked_text(dp, X_L + 22, 964, "SYSTEM MEMORY", f_futura_sm, tracking=4.2, align="left")

    static = composite_luminous(static, colorize_vertical_gradient(m_gold_lbl, 55, 102, GOLD_TOP, GOLD_BOT, GOLD_MID), sh_alpha=0.80, bloom_alpha=0.22)
    static = composite_luminous(static, colorize_vertical_gradient(m_plat_lbl, 490, 995, PEARL_SUB, PLAT_BOT, opacity=0.92), sh_alpha=0.72, bloom_alpha=0.15)

    full = static.copy()
    bars = np.zeros((H, W, 4), dtype=np.uint8)
    draw_bar_track_and_fill(bars, X_L, X_R, 686, 5, 0.24, (248, 220, 150))
    draw_bar_track_and_fill(bars, X_L, X_R, 902, 5, 0.36, (230, 242, 255))
    full = Image.alpha_composite(full, Image.fromarray(bars, mode="RGBA"))

    m_hero_plat = Image.new("L", (W, H), 0)
    dhp = ImageDraw.Draw(m_hero_plat)
    draw_tracked_text(dhp, X_R + 6, 110, "15:48", f_butler_clock, tracking=4.0, align="right")
    draw_tracked_text(dhp, X_L - 6, 756, "42°", f_butler_temp, tracking=2.0, align="left")
    draw_tracked_text(dhp, X_R, 594, "24%", f_helv_mid, tracking=1.5, align="right")
    draw_tracked_text(dhp, X_R, 944, "42%", f_helv_mid, tracking=1.5, align="right")

    m_hero_gold = Image.new("L", (W, H), 0)
    dhg = ImageDraw.Draw(m_hero_gold)
    draw_tracked_text(dhg, X_R, 308, "2026 · 11 · 21", f_helv_date, tracking=3.5, align="right")
    draw_tracked_text(dhg, X_L - 6, 536, "46°", f_butler_temp, tracking=2.0, align="left")
    draw_tracked_text(dhg, X_R, 812, "36%", f_helv_mid, tracking=1.5, align="right")

    full = composite_luminous(full, colorize_vertical_gradient(m_hero_plat, 108, 1005, PLAT_TOP, PLAT_BOT), sh_alpha=0.82, bloom_alpha=0.22)
    full = composite_luminous(full, colorize_vertical_gradient(m_hero_gold, 305, 865, GOLD_TOP, GOLD_BOT, GOLD_MID), sh_alpha=0.82, bloom_alpha=0.22)
    return static, full


def main():
    bg_s1  = Image.open(HFLIP_DIR / "hflip_s1_legs.png").convert("RGBA")
    bg_s2  = Image.open(HFLIP_DIR / "hflip_s2_fullbody.png").convert("RGBA")
    bg_s3b = Image.open(HFLIP_DIR / "hflip_s3b_smile.png").convert("RGBA")

    editions = [
        ("A_horology_full",    "方案 A · 高奢制表大字全监控版（与 8.8 寸屏 PlatinumBlade_A 同套）", render_edition_a),
        ("B_editorial_minimal","方案 B · 极简杂志大字留白版（留出中上晨光留白 + 超大字号）",         render_edition_b),
    ]

    f_tag = load_font(["msyh.ttc", "arial.ttf"], 28)
    s2_previews = []
    for key, label, fn in editions:
        static_ov, mock_ov = fn()
        static_ov.save(OUT_DIR / f"sama_ui_{key}_static_overlay.png")
        for s_tag, bg in [("s1", bg_s1), ("s2", bg_s2), ("s3b", bg_s3b)]:
            comp = Image.alpha_composite(bg, mock_ov).convert("RGB")
            p = OUT_DIR / f"preview_{key}_{s_tag}.png"
            comp.save(p, quality=95)
            if s_tag in ("s2", "s3b"):
                comp.save(ART_DIR / p.name, quality=95)
            if s_tag == "s2":
                s2_previews.append((label, comp))
        tw = 1500
        th = int(round(tw * H / W))
        strip = Image.new("RGB", (tw, th * 3 + 24), (16, 18, 22))
        for idx, s_tag in enumerate(["s1", "s2", "s3b"]):
            im = Image.open(OUT_DIR / f"preview_{key}_{s_tag}.png").resize((tw, th), Image.Resampling.LANCZOS)
            strip.paste(im, (0, idx * (th + 12)))
        strip.save(OUT_DIR / f"strip_{key}_3shots.png", quality=94)
        strip.save(ART_DIR / f"strip_{key}_3shots.png", quality=94)
        print(f"[OK] Rendered {key} (large-scale)")

    tw = 1600
    th = int(round(tw * H / W))
    ab = Image.new("RGB", (tw, th * 2 + 16), (14, 16, 20))
    dr = ImageDraw.Draw(ab)
    for i, (label, comp) in enumerate(s2_previews):
        y0 = i * (th + 16)
        ab.paste(comp.resize((tw, th), Image.Resampling.LANCZOS), (0, y0))
        dr.rectangle([18, y0 + 18, 920, y0 + 66], fill=(10, 16, 28))
        dr.text((32, y0 + 25), label, font=f_tag, fill=(255, 236, 178))
    ab.save(OUT_DIR / "compare_A_vs_B_shot2.png", quality=95)
    ab.save(ART_DIR / "compare_A_vs_B_shot2.png", quality=95)
    print(f"[DONE] Saved large-scale UI concept previews!")


if __name__ == "__main__":
    main()
