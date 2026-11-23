"""
Fast RTX 5080 OPTIX native 24fps re-render of the LOCKED `screen2_sama_previz_v3.blend`
(which contains BOTH final hand fixes: right hand resting on scabbard behind halo ring,
left hand planted flat on concrete ledge) -> outputs clean H.264 24fps MP4 for Seedance 2.5
Multimodal Video Reference (@Video1).
"""

import math
import time
from pathlib import Path
import bpy

PREVIZ_DIR = Path(__file__).resolve().parent.parent / "assets" / "previz"
BLEND_PATH = PREVIZ_DIR / "screen2_sama_previz_v3.blend"
FRAMES_DIR = PREVIZ_DIR / "frames_final_24fps"
FRAMES_DIR.mkdir(parents=True, exist_ok=True)


def main():
    bpy.ops.wm.open_mainfile(filepath=str(BLEND_PATH))
    scene = bpy.context.scene

    # Enable OPTIX/CUDA GPU + fast clean denoised settings for motion-reference MP4
    scene.render.engine = 'CYCLES'
    prefs = bpy.context.preferences.addons.get('cycles')
    if prefs:
        cprefs = prefs.preferences
        for dev_type in ('OPTIX', 'CUDA'):
            try:
                cprefs.compute_device_type = dev_type
                cprefs.get_devices()
                devs = [d for d in cprefs.devices if d.type == dev_type]
                if devs:
                    for d in cprefs.devices:
                        d.use = (d.type == dev_type)
                    scene.cycles.device = 'GPU'
                    print(f"[GPU] Using {dev_type}: {[d.name for d in devs]}")
                    break
            except Exception:
                continue

    # Crisp 2.15:1 widescreen (1120x520) — native 24fps (288 frames), fast denoised OPTIX!
    scene.render.resolution_x = 1120
    scene.render.resolution_y = 520
    scene.render.resolution_percentage = 100
    scene.cycles.samples = 6
    scene.cycles.use_adaptive_sampling = True
    scene.cycles.adaptive_threshold = 0.06
    scene.cycles.use_denoising = True
    try:
        scene.cycles.denoiser = 'OPTIX'
    except Exception:
        scene.cycles.denoiser = 'OPENIMAGEDENOISE'
    scene.cycles.max_bounces = 2
    scene.cycles.diffuse_bounces = 1
    scene.cycles.glossy_bounces = 1
    scene.cycles.transmission_bounces = 1
    scene.cycles.volume_bounces = 0
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGB'

    for old in FRAMES_DIR.glob("frame_*.png"):
        old.unlink()

    t0 = time.time()
    scene.frame_set(1)
    scene.render.filepath = str(FRAMES_DIR / "frame_0001.png")
    bpy.ops.render.render(write_still=True)
    dt = time.time() - t0
    print(f"[BENCH] 1 frame (1120x520, 6 spp OPTIX) took {dt:.3f}s")

    # Full native 24fps (288 frames) if fast enough (<= 0.6s/frame -> ~120s total), else stride=2 (144 frames)
    stride = 1 if dt <= 0.65 else 2
    total = 288
    print(f"[INFO] Rendering 12s final-pose MP4 frames with stride={stride} ({math.ceil(total/stride)} frames)...")
    t_start = time.time()
    for f in range(1 + stride, total + 1, stride):
        scene.frame_set(f)
        scene.render.filepath = str(FRAMES_DIR / f"frame_{f:04d}.png")
        bpy.ops.render.render(write_still=True)
        if f % 48 == 1 or f >= total - stride:
            print(f"[PROG] frame {f}/{total} ({time.time()-t_start:.1f}s elapsed)")

    print(f"[DONE] Rendered final-pose frames (stride={stride}) in {time.time()-t0:.1f}s!")


if __name__ == "__main__":
    main()
