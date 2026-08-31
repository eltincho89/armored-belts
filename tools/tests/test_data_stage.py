"""Assertions against data-raw-dump.json -- the prototypes as Factorio built them.

This is the layer that catches what reading the Lua cannot: values inherited
from a deepcopy, fields another mod overwrote, and sprite paths that survived
the remap. Run `python tools/run_tests.py --dump` to regenerate the dump first.
"""

import os

from harness import test, Skip
import context as ctx

SUITE = "data stage"


def dump():
    if not ctx.DUMP_PATH.exists():
        raise Skip("no dump at %s -- run with --dump" % ctx.DUMP_PATH)
    return ctx.load_dump()


@test(SUITE, "the dump is newer than the mod sources")
def test_dump_fresh(t):
    if not ctx.DUMP_PATH.exists():
        raise Skip("no dump -- run with --dump")
    if not ctx.is_live_mod_dir():
        # The dump describes whatever is linked into mods/, so comparing it
        # against a clone's checkout timestamps proves nothing.
        raise Skip("this checkout is not the copy the dump was built from")
    dump_mtime = ctx.DUMP_PATH.stat().st_mtime
    stale = []
    for path in ctx.MOD_DIR.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() not in (".lua", ".json", ".png", ".cfg"):
            continue
        if path.stat().st_mtime > dump_mtime:
            stale.append(os.path.relpath(path, ctx.MOD_DIR))
    t.empty(sorted(stale), "no mod file is newer than the dump")


@test(SUITE, "the three entities exist with the expected health")
def test_entities_exist(t):
    raw = dump()
    for name, kind, _source, health in ctx.ENTITIES:
        entity = raw.get(kind, {}).get(name)
        if not t.true(entity is not None, "%s exists as a %s" % (name, kind)):
            continue
        t.eq(entity.get("max_health"), health, "%s: max_health" % name)


@test(SUITE, "throughput is identical to express -- this is a side-grade")
def test_speed(t):
    raw = dump()
    for name, kind, source, _health in ctx.ENTITIES:
        armored = raw.get(kind, {}).get(name)
        express = raw.get(kind, {}).get(source)
        if not (armored and express):
            continue
        t.eq(armored.get("speed"), express.get("speed"),
             "%s: same speed as %s" % (name, source))

    turbo = raw.get("transport-belt", {}).get("turbo-transport-belt")
    belt = raw.get("transport-belt", {}).get("armored-transport-belt")
    if turbo and belt:
        t.true(belt["speed"] <= turbo["speed"],
               "armored belt is not faster than turbo",
               "%s vs %s" % (belt["speed"], turbo["speed"]))


@test(SUITE, "all four resistances are present and exact")
def test_resistances(t):
    raw = dump()
    expected_types = sorted(r["type"] for r in ctx.EXPECTED_RESISTANCES)
    for name, kind, _source, _health in ctx.ENTITIES:
        entity = raw.get(kind, {}).get(name)
        if not entity:
            continue
        actual = {r["type"]: r for r in entity.get("resistances") or []}
        # Extras inherited from the cloned express prototype are allowed and
        # are covered by test_no_resistance_regression; the armor set itself
        # has to be present and exact.
        t.empty(sorted(set(expected_types) - set(actual)),
                "%s: every armor resistance is present" % name)
        for expected in ctx.EXPECTED_RESISTANCES:
            got = actual.get(expected["type"])
            if not got:
                continue
            t.eq(got.get("percent"), expected["percent"],
                 "%s: %s percent" % (name, expected["type"]))
            t.eq(got.get("decrease", 0), expected.get("decrease", 0),
                 "%s: %s decrease" % (name, expected["type"]))


@test(SUITE, "armored belts are a dead end for upgrade planners")
def test_upgrade_chain(t):
    raw = dump()
    for name, kind, source, _health in ctx.ENTITIES:
        entity = raw.get(kind, {}).get(name)
        express = raw.get(kind, {}).get(source)
        if not entity:
            continue
        t.is_none(entity.get("next_upgrade"), "%s: next_upgrade is nil" % name)
        if express:
            t.eq(entity.get("fast_replaceable_group"),
                 express.get("fast_replaceable_group"),
                 "%s: keeps the express fast_replaceable_group" % name)
        t.is_none(entity.get("factoriopedia_simulation"),
                  "%s: no inherited express simulation" % name)


@test(SUITE, "entities are minable into their own item and cross-linked")
def test_minable_and_links(t):
    raw = dump()
    for name, kind, _source, _health in ctx.ENTITIES:
        entity = raw.get(kind, {}).get(name)
        if not entity:
            continue
        t.eq((entity.get("minable") or {}).get("result"), name,
             "%s: mines into its own item" % name)

    belt = raw.get("transport-belt", {}).get("armored-transport-belt")
    splitter = raw.get("splitter", {}).get("armored-splitter")
    if belt:
        t.eq(belt.get("related_underground_belt"), "armored-underground-belt",
             "belt points at the armored underground belt")
    if splitter:
        t.eq(splitter.get("related_transport_belt"), "armored-transport-belt",
             "splitter points at the armored belt")


@test(SUITE, "each entity has its own armored corpse")
def test_corpses(t):
    raw = dump()
    for name, kind, _source, _health in ctx.ENTITIES:
        entity = raw.get(kind, {}).get(name)
        if not entity:
            continue
        corpse_name = entity.get("corpse")
        t.eq(corpse_name, "%s-remnants" % name, "%s: corpse name" % name)
        corpse = raw.get("corpse", {}).get(corpse_name)
        if not t.true(corpse is not None, "%s: corpse prototype exists" % corpse_name):
            continue
        icons = corpse.get("icons") or []
        t.true(icons and all("__%s__" % ctx.MOD_NAME in i.get("icon", "")
                             for i in icons),
               "%s: icon is the armored one" % corpse_name,
               "got %r" % icons)


@test(SUITE, "no graphical reference to express survives anywhere")
def test_no_express_graphics(t):
    raw = dump()
    leftovers = []
    for name, kind, _source, _health in ctx.ENTITIES:
        targets = ((raw.get(kind, {}).get(name), name),
                   (raw.get("corpse", {}).get("%s-remnants" % name),
                    "%s-remnants" % name))
        for proto, label in targets:
            if not proto:
                continue
            for path, value in ctx.walk_strings(proto):
                if value.endswith(".ogg"):
                    continue
                if "express" in value and ("/" in value or value.endswith(".png")):
                    leftovers.append("%s.%s = %s" % (label, path, value))
    t.empty(leftovers, "no express sprite path remains in the 6 prototypes")


@test(SUITE, "every sprite the prototypes reference exists on disk")
def test_sprites_resolve(t):
    raw = dump()
    missing, checked = [], 0
    for name, kind, _source, _health in ctx.ENTITIES:
        for proto in (raw.get(kind, {}).get(name),
                      raw.get("corpse", {}).get("%s-remnants" % name)):
            if not proto:
                continue
            for _path, value in ctx.walk_strings(proto):
                if not value.endswith(".png"):
                    continue
                resolved = ctx.resolve(value)
                if resolved is None:
                    continue
                checked += 1
                if not resolved.exists():
                    missing.append("%s: %s" % (name, value))
    t.empty(sorted(set(missing)), "all %d referenced PNGs exist" % checked)
    t.true(checked > 0, "sprite references were actually found to check")


@test(SUITE, "items are placeable and sort after express")
def test_items(t):
    raw = dump()
    items = raw.get("item", {})
    orders = {}
    for name, _kind, source, _health in ctx.ENTITIES:
        item = items.get(name)
        express = items.get(source)
        if not t.true(item is not None, "item %s exists" % name):
            continue
        t.eq(item.get("place_result"), name, "%s: place_result" % name)
        icons = item.get("icons") or []
        t.true(icons and all("__%s__" % ctx.MOD_NAME in i.get("icon", "")
                             for i in icons), "%s: armored item icon" % name)
        if express:
            t.eq(item.get("stack_size"), express.get("stack_size"),
                 "%s: same stack size as %s" % (name, source))
            t.eq(item.get("subgroup"), express.get("subgroup"),
                 "%s: same subgroup as %s" % (name, source))
            t.true(item.get("order", "") > express.get("order", ""),
                   "%s: sorts after %s" % (name, source),
                   "%r vs %r" % (item.get("order"), express.get("order")))
        orders[name] = item.get("order")
    t.eq(len(set(orders.values())), len(orders), "item orders are distinct")


@test(SUITE, "recipes match the intended cost and stay hand-craftable")
def test_recipes(t):
    raw = dump()
    recipes = raw.get("recipe", {})
    items = raw.get("item", {})
    for name, expected in ctx.EXPECTED_RECIPES.items():
        recipe = recipes.get(name)
        if not t.true(recipe is not None, "recipe %s exists" % name):
            continue
        t.eq(recipe.get("category", "crafting"), "pressing",
             "%s: pressing category (hand-craftable, Foundry-buildable)" % name)
        t.eq(recipe.get("enabled", True), False,
             "%s: locked until researched" % name)
        t.eq(recipe.get("energy_required"), expected["energy_required"],
             "%s: craft time" % name)
        got_in = [(i["name"], i["amount"]) for i in recipe.get("ingredients", [])]
        t.eq(got_in, expected["ingredients"], "%s: ingredients" % name)
        got_out = [(r["name"], r["amount"]) for r in recipe.get("results", [])]
        t.eq(got_out, expected["results"], "%s: results" % name)
        for item_name, _amount in expected["ingredients"]:
            t.true(item_name in items, "%s: ingredient %s exists" % (name, item_name))


@test(SUITE, "the technology gates the recipes at the right point in the tree")
def test_technology(t):
    raw = dump()
    tech = raw.get("technology", {}).get(ctx.TECH_NAME)
    if not t.true(tech is not None, "technology %s exists" % ctx.TECH_NAME):
        return

    t.eq(sorted(tech.get("prerequisites") or []), sorted(ctx.TECH_PREREQUISITES),
         "prerequisites")
    for prereq in ctx.TECH_PREREQUISITES:
        t.true(prereq in raw.get("technology", {}), "prerequisite %s exists" % prereq)

    unlocked = sorted(e["recipe"] for e in tech.get("effects") or []
                      if e.get("type") == "unlock-recipe")
    t.eq(unlocked, sorted(ctx.EXPECTED_RECIPES), "unlocks exactly the three recipes")

    unit = tech.get("unit") or {}
    t.eq(unit.get("count"), ctx.TECH_COUNT, "research count")
    t.eq(unit.get("time"), ctx.TECH_TIME, "research time")
    packs = [i[0] if isinstance(i, list) else i["name"]
             for i in unit.get("ingredients") or []]
    t.eq(sorted(packs), sorted(ctx.TECH_PACKS), "science packs")
    for pack in packs:
        t.true(pack in raw.get("tool", {}), "science pack %s exists" % pack)

    icon = tech.get("icon") or (tech.get("icons") or [{}])[0].get("icon")
    resolved = ctx.resolve(icon or "")
    t.true(resolved is not None and resolved.exists(),
           "technology icon exists on disk", "got %r" % icon)
    t.true("__%s__" % ctx.MOD_NAME in (icon or ""),
           "technology icon is the recolored one, not the blue logistics-3")


@test(SUITE, "no armored recipe is left unreachable")
def test_recipes_reachable(t):
    raw = dump()
    unlocked = set()
    for tech in raw.get("technology", {}).values():
        for effect in tech.get("effects") or []:
            if effect.get("type") == "unlock-recipe":
                unlocked.add(effect["recipe"])
    for name in ctx.EXPECTED_RECIPES:
        t.true(name in unlocked, "%s is unlocked by some technology" % name)


@test(SUITE, "vanilla express belts are left untouched")
def test_vanilla_untouched(t):
    raw = dump()
    for name, kind, source, _health in ctx.ENTITIES:
        express = raw.get(kind, {}).get(source)
        if not express:
            continue
        armor_only = {"explosion", "physical", "acid"}
        leaked = sorted(armor_only.intersection(
            r["type"] for r in express.get("resistances") or []))
        t.empty(leaked, "%s: no armor resistance leaked onto vanilla" % source)
        t.true(express.get("max_health", 0) < 200,
               "%s: health unchanged" % source, "got %r" % express.get("max_health"))
        t.eq((express.get("minable") or {}).get("result"), source,
             "%s: still mines into itself" % source)


@test(SUITE, "armored is never worse than the express it replaces")
def test_no_resistance_regression(t):
    raw = dump()
    # The armored line is a strict side-grade: same throughput, more armor.
    # Overwriting `resistances` wholesale silently drops anything vanilla had
    # that the armor set does not mention -- underground belts, for instance,
    # ship with 30% impact resistance against vehicle collisions.
    for name, kind, source, _health in ctx.ENTITIES:
        armored = raw.get(kind, {}).get(name)
        express = raw.get(kind, {}).get(source)
        if not (armored and express):
            continue
        mine = {r["type"]: r for r in armored.get("resistances") or []}
        theirs = {r["type"]: r for r in express.get("resistances") or []}
        for kind_name, source_resist in theirs.items():
            got = mine.get(kind_name)
            if not t.true(got is not None,
                          "%s: keeps the %s resistance express had" % (name, kind_name),
                          "express has %r, armored has none" % (source_resist,)):
                continue
            t.true(got.get("percent", 0) >= source_resist.get("percent", 0),
                   "%s: %s resistance not reduced" % (name, kind_name),
                   "%s%% vs express %s%%" % (got.get("percent", 0),
                                             source_resist.get("percent", 0)))
        t.true(armored.get("max_health", 0) > express.get("max_health", 0),
               "%s: tougher than %s" % (name, source))
