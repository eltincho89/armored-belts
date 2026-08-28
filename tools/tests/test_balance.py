"""Combat math, recomputed from the dump instead of trusted from the README.

Enemy damage is read out of the shipped prototypes and pushed through the real
formula, so a vanilla rebalance shows up here as a failing number rather than
as a README that quietly went out of date.
"""

from harness import test, Skip
import context as ctx

SUITE = "balance"

# The table in README section 4. Hit counts there are HP/damage rounded to the
# nearest whole hit, which is how the README presents them.
README_TABLE = [
    # enemy prototype,           damage, express hits, armored hits (None = immune)
    ("small-wriggler-pentapod",  3.75,   45,   None),
    ("medium-wriggler-pentapod", 5.5,    31,   None),
    ("small-biter",              7,      24,   None),
    ("big-wriggler-pentapod",    9,      19,   1500),
    ("medium-biter",             15,     11,   214),
    ("big-biter",                30,     6,    68),
    ("behemoth-biter",           90,     2,    18),
]

FOLLOWABLE = ("stream", "projectile", "fire", "explosion",
              "artillery-projectile", "sticker")


def dump():
    if not ctx.DUMP_PATH.exists():
        raise Skip("no dump -- run with --dump")
    return ctx.load_dump()


def _lookup(raw, name):
    for kind in FOLLOWABLE:
        proto = raw.get(kind, {}).get(name)
        if proto is not None:
            return proto
    return None


def collect_damage(raw, node, seen=None):
    """Every damage type an attack can deliver, following streams/projectiles.

    Spitters and worms do not carry their damage inline: the attack points at
    an acid stream, and the stream carries the action. Walking the reference
    is the only way to see the acid.
    """
    seen = seen if seen is not None else set()
    found = set()
    if isinstance(node, dict):
        if node.get("type") == "damage" and isinstance(node.get("damage"), dict):
            found.add(node["damage"]["type"])
        for key, value in node.items():
            if key in FOLLOWABLE + ("entity_name",) and isinstance(value, str):
                if value not in seen:
                    seen.add(value)
                    target = _lookup(raw, value)
                    if target is not None:
                        found |= collect_damage(raw, target, seen)
            else:
                found |= collect_damage(raw, value, seen)
    elif isinstance(node, list):
        for value in node:
            found |= collect_damage(raw, value, seen)
    return found


def _armored(raw):
    return raw["transport-belt"]["armored-transport-belt"]


def _express(raw):
    return raw["transport-belt"]["express-transport-belt"]


@test(SUITE, "enemies deal no fire and no explosion damage")
def test_enemy_damage_types(t):
    raw = dump()
    types = set()
    for unit in raw.get("unit", {}).values():
        types |= collect_damage(raw, unit.get("attack_parameters"))
    for name, turret in raw.get("turret", {}).items():
        if "worm" in name:
            types |= collect_damage(raw, turret.get("attack_parameters"))

    print("      (enemy damage types found: %s)" % ", ".join(sorted(types)))
    t.true(types, "enemy damage types were actually extracted")
    # This is the premise behind carrying fire and explosion resistance at all:
    # they are there for friendly fire, not for the biters.
    t.true("fire" not in types, "no enemy deals fire damage")
    t.true("explosion" not in types, "no enemy deals explosion damage")
    t.contains(types, "physical", "enemies do deal physical damage")
    t.contains(types, "acid", "enemies do deal acid damage")


@test(SUITE, "the README combat table matches the shipped prototypes")
def test_readme_table(t):
    raw = dump()
    armored, express = _armored(raw), _express(raw)
    units = raw.get("unit", {})

    for name, damage, express_hits, armored_hits in README_TABLE:
        unit = units.get(name)
        if not t.true(unit is not None, "%s exists in the game data" % name):
            continue
        specs = list(ctx.walk_damage(unit.get("attack_parameters")))
        physical = next((d["amount"] for d in specs if d["type"] == "physical"), None)
        t.eq(physical, damage, "%s: physical damage per bite" % name)

        exp_final = ctx.final_damage(damage, "physical", express.get("resistances"))
        arm_final = ctx.final_damage(damage, "physical", armored.get("resistances"))

        if t.true(exp_final is not None, "%s: express belt is damageable" % name):
            t.eq(round(express["max_health"] / exp_final), express_hits,
                 "%s: hits vs express belt" % name)

        if armored_hits is None:
            t.is_none(arm_final, "%s: armored belt is immune" % name)
        elif t.true(arm_final is not None, "%s: armored belt is damageable" % name):
            t.eq(round(armored["max_health"] / arm_final), armored_hits,
                 "%s: hits vs armored belt" % name)


@test(SUITE, "armored belts hold ~10x longer against the enemies that matter")
def test_durability_factor(t):
    raw = dump()
    armored, express = _armored(raw), _express(raw)

    arm_final = ctx.final_damage(90, "physical", armored.get("resistances"))
    exp_final = ctx.final_damage(90, "physical", express.get("resistances"))
    factor = ((armored["max_health"] / arm_final)
              / (express["max_health"] / exp_final))
    print("      (behemoth biter durability factor: %.2fx)" % factor)
    # The README claims ~9.7x; this is the number the whole mod stands on.
    t.near(factor, 9.7, 0.15, "behemoth durability factor")

    # And it must never come out worse than express against anything.
    worse = []
    for unit_name, unit in raw.get("unit", {}).items():
        for spec in ctx.walk_damage(unit.get("attack_parameters")):
            kind, amount = spec["type"], spec["amount"]
            arm = ctx.final_damage(amount, kind, armored.get("resistances"))
            exp = ctx.final_damage(amount, kind, express.get("resistances"))
            if arm is None:
                continue
            if exp is None or (armored["max_health"] / arm) <= (express["max_health"] / exp):
                worse.append("%s (%s %s)" % (unit_name, amount, kind))
    t.empty(worse, "armored survives longer than express against every enemy attack")


@test(SUITE, "the small-biter immunity is a deliberate, bounded outcome")
def test_small_biter_immunity(t):
    raw = dump()
    armored = _armored(raw)
    physical = next(r for r in armored["resistances"] if r["type"] == "physical")
    decrease = physical.get("decrease", 0)

    def bite(name):
        return next(d["amount"] for d in ctx.walk_damage(
            raw["unit"][name].get("attack_parameters")) if d["type"] == "physical")

    t.true(bite("small-biter") <= decrease,
           "small biters cannot dent an armored belt",
           "bite %s vs decrease %s" % (bite("small-biter"), decrease))
    # Acceptable only because the tech lands late; if the flat decrease ever
    # climbed past a medium biter the trade would stop being defensible.
    t.true(bite("medium-biter") > decrease, "medium biters are NOT immune-blocked",
           "bite %s vs decrease %s" % (bite("medium-biter"), decrease))


@test(SUITE, "the vanilla premise the mod is built on still holds")
def test_vanilla_premise(t):
    raw = dump()
    belts = raw.get("transport-belt", {})

    def fire(name):
        entity = belts.get(name) or {}
        return next((r.get("percent") for r in entity.get("resistances") or []
                     if r["type"] == "fire"), None)

    # README 3.1: upgrading your belts actually makes them more flammable.
    t.eq(fire("transport-belt"), 90, "yellow belt fire resistance")
    t.eq(fire("fast-transport-belt"), 50, "red belt fire resistance")
    t.eq(fire("express-transport-belt"), 50, "blue belt fire resistance")

    # README 3.1: no vanilla belt has any explosion resistance at all.
    with_explosion = [
        name for name, entity in belts.items()
        if not name.startswith("armored-")
        and any(r["type"] == "explosion" for r in entity.get("resistances") or [])
    ]
    t.empty(with_explosion, "no vanilla belt has explosion resistance")
