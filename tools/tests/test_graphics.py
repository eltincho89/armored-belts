"""The recolor pipeline: sprite bookkeeping and the color claims themselves.

graphics-map.lua is what the Lua remap walks, so it is the single source of
truth these tests pin down from both ends: every entry must point at a vanilla
file that still exists (or the remap silently does nothing) and at a recolored
file that really was written (or the game fails to load).
"""

from harness import test, Skip
import context as ctx

SUITE = "graphics"


def _load(path):
    try:
        import numpy as np
        from PIL import Image
    except ImportError as exc:
        raise Skip("needs Pillow and numpy (%s)" % exc)
    with Image.open(path) as image:
        return np.asarray(image.convert("RGBA"), dtype=np.float64) / 255.0


def _stats(array):
    """Mean HSL lightness, mean saturation and the high-chroma fraction."""
    import numpy as np
    opaque = array[..., 3] > 0.5
    if not opaque.any():
        return None
    rgb = array[..., :3][opaque]
    mx = rgb.max(axis=1)
    mn = rgb.min(axis=1)
    lightness = (mx + mn) / 2.0
    delta = mx - mn
    denom = 1.0 - np.abs(2.0 * lightness - 1.0)
    saturation = np.where(denom > 1e-6, delta / np.maximum(denom, 1e-6), 0.0)
    return {
        "lightness": float(lightness.mean()),
        "saturation": float(saturation.mean()),
        "chromatic": float((saturation > 0.3).mean()),
    }


@test(SUITE, "graphics-map lists every sprite exactly once")
def test_map_shape(t):
    mapping = ctx.load_graphics_map()
    t.eq(len(mapping), ctx.SPRITE_COUNT, "map has %d entries" % ctx.SPRITE_COUNT)
    t.eq(len(set(mapping.values())), len(mapping), "no two sources share a target")


@test(SUITE, "every mapped vanilla source still exists in base")
def test_sources_exist(t):
    # A vanilla rename would not raise: the remap would just leave the express
    # path in place and the armored belt would quietly render blue again.
    missing = []
    for source in ctx.load_graphics_map():
        path = ctx.resolve(source)
        if path is None or not path.exists():
            missing.append(source)
    t.empty(missing, "all %d source sprites exist in the game install"
            % len(ctx.load_graphics_map()))


@test(SUITE, "every mapped target exists, and no generated file is orphaned")
def test_targets_exist(t):
    mapping = ctx.load_graphics_map()
    targets = set(mapping.values())

    missing = []
    for target in sorted(targets):
        path = ctx.resolve(target)
        if path is None or not path.exists():
            missing.append(target)
    t.empty(missing, "all %d recolored sprites exist on disk" % len(targets))

    on_disk = {
        "__%s__/%s" % (ctx.MOD_NAME, p.relative_to(ctx.MOD_DIR).as_posix())
        for p in (ctx.MOD_DIR / "graphics").rglob("*.png")
    }
    t.empty(sorted(on_disk - targets), "no PNG in graphics/ is missing from the map")
    t.empty(sorted(targets - on_disk), "no map entry lacks its PNG")


@test(SUITE, "recolored sprites keep the source geometry and alpha")
def test_geometry_and_alpha(t):
    import numpy as np
    for source, target in sorted(ctx.load_graphics_map().items()):
        src_path, dst_path = ctx.resolve(source), ctx.resolve(target)
        if not (src_path and dst_path and src_path.exists() and dst_path.exists()):
            continue
        src, dst = _load(src_path), _load(dst_path)
        label = dst_path.name
        # A sprite sheet whose size drifts silently shifts every animation frame.
        if not t.eq(dst.shape[:2], src.shape[:2], "%s: same dimensions" % label):
            continue
        # The recolor must touch chroma only; a changed alpha means cut edges.
        t.true(np.array_equal(src[..., 3], dst[..., 3]),
               "%s: alpha channel untouched" % label,
               "max alpha delta %.4f" % float(np.abs(src[..., 3] - dst[..., 3]).max()))


@test(SUITE, "the recolor actually neutralized the cyan")
def test_color_claims(t):
    mapping = ctx.load_graphics_map()
    aggregate = {"src_sat": [], "dst_sat": []}

    for source, target in sorted(mapping.items()):
        src_path, dst_path = ctx.resolve(source), ctx.resolve(target)
        if not (src_path and dst_path and src_path.exists() and dst_path.exists()):
            continue
        src, dst = _stats(_load(src_path)), _stats(_load(dst_path))
        if not src or not dst:
            continue
        label = dst_path.name
        aggregate["src_sat"].append(src["saturation"])
        aggregate["dst_sat"].append(dst["saturation"])

        t.true(dst["saturation"] < 0.05, "%s: mean saturation is neutral" % label,
               "%.3f (source %.3f)" % (dst["saturation"], src["saturation"]))
        t.true(dst["chromatic"] < 0.01, "%s: <1%% strongly chromatic pixels" % label,
               "%.2f%%" % (dst["chromatic"] * 100))
        # The whole point of the approach: chroma out, luminance intact. A big
        # drop here would mean the tread detail got flattened.
        t.true(abs(dst["lightness"] - src["lightness"]) / max(src["lightness"], 1e-6) < 0.25,
               "%s: luminance preserved" % label,
               "%.3f -> %.3f" % (src["lightness"], dst["lightness"]))
        # Guards against a sprite that was copied instead of recolored.
        t.true(dst["saturation"] < src["saturation"],
               "%s: less saturated than the express source" % label)

    if aggregate["dst_sat"]:
        before = sum(aggregate["src_sat"]) / len(aggregate["src_sat"])
        after = sum(aggregate["dst_sat"]) / len(aggregate["dst_sat"])
        print("      (mean saturation across sprites: %.3f -> %.3f)" % (before, after))
