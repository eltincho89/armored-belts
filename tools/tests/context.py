"""Paths, loaders and shared constants for the test suite."""

import json
import os
import re
from pathlib import Path

MOD_DIR = Path(__file__).resolve().parents[2]
MOD_NAME = "armored-belts"

FACTORIO_DIR = Path(os.environ.get(
    "FACTORIO_DIR", r"C:\Program Files (x86)\Steam\steamapps\common\Factorio"))
FACTORIO_EXE = FACTORIO_DIR / "bin" / "x64" / "factorio.exe"
DATA_DIR = FACTORIO_DIR / "data"

USER_DIR = Path(os.environ.get(
    "FACTORIO_USER_DIR",
    Path(os.environ.get("APPDATA", Path.home())) / "Factorio"))
DUMP_PATH = USER_DIR / "script-output" / "data-raw-dump.json"
MODS_DIR = USER_DIR / "mods"

# The three entities, their data.raw type, and the express prototype each was
# cloned from. Everything else in the suite is derived from this table.
ENTITIES = [
    ("armored-transport-belt",    "transport-belt",    "express-transport-belt",    600),
    ("armored-underground-belt",  "underground-belt",  "express-underground-belt",  600),
    ("armored-splitter",          "splitter",          "express-splitter",          670),
]
NAMES = [e[0] for e in ENTITIES]

EXPECTED_RESISTANCES = [
    {"type": "fire", "percent": 95},
    {"type": "explosion", "percent": 80, "decrease": 15},
    {"type": "physical", "percent": 60, "decrease": 8},
    {"type": "acid", "percent": 60, "decrease": 5},
]

EXPECTED_RECIPES = {
    "armored-transport-belt": {
        "ingredients": [("express-transport-belt", 1), ("steel-plate", 4)],
        "results": [("armored-transport-belt", 1)],
        "energy_required": 1,
    },
    "armored-underground-belt": {
        "ingredients": [("express-underground-belt", 2), ("steel-plate", 10)],
        "results": [("armored-underground-belt", 2)],
        "energy_required": 2,
    },
    "armored-splitter": {
        "ingredients": [("express-splitter", 1), ("steel-plate", 8)],
        "results": [("armored-splitter", 1)],
        "energy_required": 2,
    },
}

TECH_NAME = "armored-belts"
TECH_PREREQUISITES = ["logistics-3", "military-3"]
TECH_PACKS = ["automation-science-pack", "logistic-science-pack",
              "military-science-pack", "chemical-science-pack",
              "production-science-pack"]
TECH_COUNT = 200
TECH_TIME = 30

SPRITE_COUNT = 17

# Mod-name -> directory, for resolving "__mod__/path" sprite references.
_ROOTS = {
    "__core__": DATA_DIR / "core",
    "__base__": DATA_DIR / "base",
    "__space-age__": DATA_DIR / "space-age",
    "__quality__": DATA_DIR / "quality",
    "__elevated-rails__": DATA_DIR / "elevated-rails",
    "__%s__" % MOD_NAME: MOD_DIR,
}


def resolve(path_ref):
    """Turn a Factorio "__mod__/dir/file.png" reference into a real Path.

    Returns None for a reference whose mod root is unknown (an unrelated mod),
    so callers can tell "does not exist" apart from "cannot be checked".
    """
    match = re.match(r"^(__[^_][^/]*__)/(.*)$", path_ref)
    if not match:
        return None
    root = _ROOTS.get(match.group(1))
    if root is None:
        return None
    return root / match.group(2)


_dump_cache = {}


def load_dump():
    """data-raw-dump.json, produced by `factorio.exe --dump-data`."""
    if "dump" not in _dump_cache:
        with open(DUMP_PATH, encoding="utf-8") as handle:
            _dump_cache["dump"] = json.load(handle)
    return _dump_cache["dump"]


def load_graphics_map():
    """Parse prototypes/graphics-map.lua into a {source: target} dict.

    The file is generated, so its shape is a flat table of string pairs; a
    regex is enough and keeps the suite free of a Lua interpreter.
    """
    text = (MOD_DIR / "prototypes" / "graphics-map.lua").read_text(encoding="utf-8")
    pairs = re.findall(r'\["([^"]+)"\]\s*=\s*"([^"]+)"', text)
    return dict(pairs)


def load_locale(locale):
    """Parse locale/<locale>/strings.cfg into {"section.key": value}.

    Returns (entries, duplicate_keys) so a shadowed key is reported instead of
    silently winning.
    """
    path = MOD_DIR / "locale" / locale / "strings.cfg"
    entries, duplicates, section = {}, [], None
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith(("#", ";")):
            continue
        if line.startswith("[") and line.endswith("]"):
            section = line[1:-1]
            continue
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        full = "%s.%s" % (section, key.strip())
        if full in entries:
            duplicates.append(full)
        entries[full] = value.strip()
    return entries, duplicates


def walk_strings(node, path=()):
    """Yield (dotted_path, string) for every string value in a prototype tree."""
    if isinstance(node, dict):
        for key, value in node.items():
            yield from walk_strings(value, path + (str(key),))
    elif isinstance(node, list):
        for index, value in enumerate(node):
            yield from walk_strings(value, path + (str(index),))
    elif isinstance(node, str):
        yield ".".join(path), node


def walk_damage(node):
    """Yield every {amount, type} damage spec nested anywhere under node."""
    if isinstance(node, dict):
        if node.get("type") == "damage" and isinstance(node.get("damage"), dict):
            yield node["damage"]
        for value in node.values():
            yield from walk_damage(value)
    elif isinstance(node, list):
        for value in node:
            yield from walk_damage(value)


def final_damage(damage, damage_type, resistances):
    """Factorio's damage formula: final = (damage - decrease) * (1 - percent).

    Returns None when the target is immune, i.e. the flat decrease alone eats
    the whole hit.
    """
    resist = next((r for r in (resistances or []) if r["type"] == damage_type), None)
    result = float(damage)
    if resist:
        result = ((result - resist.get("decrease", 0))
                  * (1.0 - resist.get("percent", 0) / 100.0))
    return result if result > 0 else None


def hits_to_destroy(health, damage, damage_type, resistances):
    """Whole hits needed to destroy the target, or None if it is immune."""
    import math
    final = final_damage(damage, damage_type, resistances)
    return None if final is None else math.ceil(health / final)
