"""Manifest, project structure and locale coverage.

None of this needs Factorio to have run: it is the cheap layer that catches a
broken info.json or a missing translation before a five-minute data dump.
"""

import json
import re

from harness import test, Skip
import context as ctx

SUITE = "manifest"


@test(SUITE, "info.json is well formed")
def test_info(t):
    path = ctx.MOD_DIR / "info.json"
    if not t.true(path.exists(), "info.json exists"):
        return
    info = json.loads(path.read_text(encoding="utf-8"))

    # The folder name must equal the mod name or Factorio refuses to load it.
    t.eq(info.get("name"), ctx.MOD_NAME, "name matches the mod folder")
    # Factorio refuses a mod whose folder name differs from info.json, but a
    # clone can sit in any directory, so this only binds the installed copy.
    if ctx.is_live_mod_dir():
        t.eq(ctx.MOD_DIR.name, ctx.MOD_NAME, "folder is named after the mod")
    t.true(re.fullmatch(r"\d+\.\d+\.\d+", info.get("version", "")),
           "version is major.minor.patch", "got %r" % info.get("version"))
    t.eq(info.get("factorio_version"), "2.0", "targets Factorio 2.0")
    for field in ("title", "author", "description"):
        t.true(info.get(field), "%s is set" % field)
    t.contains(info.get("dependencies", []), "base >= 2.0", "depends on base >= 2.0")


@test(SUITE, "data.lua requires every prototype file, and each one exists")
def test_data_lua(t):
    text = (ctx.MOD_DIR / "data.lua").read_text(encoding="utf-8")
    required = re.findall(r'require\("([^"]+)"\)', text)
    for module in ("prototypes.entities", "prototypes.items",
                   "prototypes.recipes", "prototypes.technology"):
        t.contains(required, module, "data.lua requires %s" % module)

    # Every require() anywhere in the mod must resolve to a file on disk.
    missing = []
    for lua in ctx.MOD_DIR.rglob("*.lua"):
        for module in re.findall(r'require\("([^"]+)"\)', lua.read_text(encoding="utf-8")):
            if not (ctx.MOD_DIR / (module.replace(".", "/") + ".lua")).exists():
                missing.append("%s -> %s" % (lua.name, module))
    t.empty(missing, "every require() resolves to a file")


@test(SUITE, "graphics-map.lua is generated, never hand-edited")
def test_generated_header(t):
    text = (ctx.MOD_DIR / "prototypes" / "graphics-map.lua").read_text(encoding="utf-8")
    t.true(text.lstrip().startswith("-- GENERATED"),
           "graphics-map.lua carries its GENERATED banner")


@test(SUITE, "locale covers every prototype in both languages")
def test_locale(t):
    expected = set()
    for name in ctx.NAMES:
        for section in ("entity-name", "item-name",
                        "entity-description", "item-description"):
            expected.add("%s.%s" % (section, name))
    expected.add("technology-name.%s" % ctx.TECH_NAME)
    expected.add("technology-description.%s" % ctx.TECH_NAME)

    locales = {}
    for locale in ("en", "es-ES"):
        entries, duplicates = ctx.load_locale(locale)
        locales[locale] = entries
        t.empty(duplicates, "%s: no duplicate keys" % locale)
        t.empty(sorted(expected - set(entries)), "%s: no missing keys" % locale)
        t.empty(sorted(set(entries) - expected), "%s: no orphan keys" % locale)
        t.empty([k for k, v in entries.items() if not v],
                "%s: no empty values" % locale)

    t.eq(set(locales["es-ES"]), set(locales["en"]),
         "es-ES and en declare the same keys")
    # A copy-paste that left English text in the Spanish file is a real bug the
    # key-set check above cannot see.
    untranslated = [k for k in locales["en"]
                    if locales["en"][k] == locales["es-ES"].get(k)]
    t.empty(untranslated, "es-ES strings differ from en (nothing left untranslated)")


@test(SUITE, "mod is installed and enabled for the local game")
def test_installed(t):
    link = ctx.MODS_DIR / ctx.MOD_NAME
    if not link.exists():
        raise Skip("%s is not linked into the mods folder" % ctx.MOD_NAME)
    if not ctx.is_live_mod_dir():
        raise Skip("this checkout is not the copy linked into mods/")
    t.eq(link.resolve(), ctx.MOD_DIR,
         "mods/%s resolves to the working directory" % ctx.MOD_NAME)

    mod_list = json.loads((ctx.MODS_DIR / "mod-list.json").read_text(encoding="utf-8"))
    entry = next((m for m in mod_list["mods"] if m["name"] == ctx.MOD_NAME), None)
    if t.true(entry is not None, "mod-list.json lists the mod"):
        t.true(entry.get("enabled"), "mod is enabled")
