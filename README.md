# Armored Transport Belts (`armored-belts`)

Mod for **Factorio 2.0** (Space Age compatible). An armored side-branch of the
express belt line, built for frontline combat zones against Biters.

- **Version:** 0.2.3
- **Tested on:** Factorio 2.0.77 (build 84539, win64, steam, space-age)
- **Dependencies:** `base >= 2.0`

---

## 1. What it is

Three new entities — belt, underground belt and splitter — with **exactly the
same throughput as express** but heavily armored. It's not a higher-speed
tier: it's a defensive variant you choose, not an upgrade that replaces
anything.

| | Armored | Express (vanilla) |
|---|---|---|
| Speed | 0.09375 | 0.09375 |
| Belt / underground HP | **600** | 170 |
| Splitter HP | **670** | 190 |
| Fire resistance | **95%** | 50% |
| Explosion resistance | **80% / −15** | none |
| Physical resistance | **60% / −8** | none |
| Acid resistance | **60% / −5** | none |

Resistances are **merged** onto whatever the cloned entity already has,
not replaced: express underground belts carry 30% impact resistance in
vanilla, and the armored one keeps it. The higher value wins per damage type,
so armored can never end up worse than express at anything.

### Recipe and unlock

`pressing` category, **no lubricant**: hand-craftable, and matches vanilla
belt recipes so the Foundry on Vulcanus can produce them too. Repairing the
line mid-attack shouldn't require a trip back to the chemical plant.

| Recipe | Ingredients | Yields |
|---|---|---|
| Armored belt | 1 express belt + 4 steel | 1 |
| Armored underground belt | 2 express underground belts + 10 steel | 2 |
| Armored splitter | 1 express splitter + 8 steel | 1 |

Technology `armored-belts`: **200 × 30 s**, prerequisites `logistics-3` +
`military-3`, automation / logistic / military / chemical / production packs.

---

## 2. Prior research: did this already exist?

The portal's full API index (**22,942 mods**) was downloaded and filtered
locally. The portal's web search is rendered with JS and can't be queried
over plain HTTP; the API's `query` endpoint ignores it and returns the full
alphabetical listing instead. Hence the dump + local filter.

**No mod combines a new belt tier with combat resistances.** The closest
matches:

| Mod | Downloads | What it does | Why it doesn't cover this |
|---|---|---|---|
| `Invulnerable-Belts` | 129 | All belts indestructible | On/off switch, no gradation or cost. Factorio 1.1, abandoned |
| `biterproof` | 3.18K | Invincibility via entity filters | Same problem: binary, not something you earn |
| `UltimateBelts` / `AdvancedBelts` / `BetterBelts` | 54K / 21K / 15K | Extra belt tiers | **Speed only.** None touch `max_health` or `resistances` |

The niche is wide open: nobody has treated the belt as a **piece of
defensive infrastructure** rather than a throughput pipe.

---

## 3. Two findings in the vanilla data

Read from the local install's `base/prototypes/entity/transport-belts.lua`.

### 3.1 Upgrading your belts makes them MORE flammable

```
transport-belt          150 HP    fire 90%
fast-transport-belt     160 HP    fire 50%   <- drops
express-transport-belt  170 HP    fire 50%
turbo-transport-belt    170 HP    fire 50%   (Space Age)
```

The yellow belt resists fire at 90%. The moment you move to red it falls to
50% and stays there forever. On top of that, **no belt in the game has any
explosion resistance**: the field simply doesn't exist at any tier.

### 3.2 Biters deal no fire or explosion damage

Verified by pulling the actual offensive damage out of `enemies.lua` and
`enemy-projectiles.lua`: enemies only deal **physical** (melee bite) and
**acid** (spitter/worm spit) damage. Zero fire, zero explosion.

Design consequence: fire and explosion resistance do **not** protect against
biters — they protect against **your own friendly fire**: flamethrower
turrets torching your line, artillery, rockets, tree fires. That's why the mod
carries all four resistances instead of just the two the original idea called
for.

---

## 4. Real combat effect

Hits needed to destroy a belt segment, applying the game's actual formula
`final_damage = (damage − decrease) × (1 − percent)`:

| Enemy | Damage | Type | Express | Armored | Factor |
|---|---|---|---|---|---|
| Small / medium wriggler | 3.75 / 5.5 | physical | 45 / 31 | **immune** | ∞ |
| Small biter | 7 | physical | 24 | **immune** | ∞ |
| Big wriggler | 9 | physical | 19 | 1500 | 79.4× |
| Medium biter | 15 | physical | 11 | 214 | 18.9× |
| Big biter | 30 | physical | 6 | 68 | 12.0× |
| Behemoth biter | 90 | physical | 2 | 18 | **9.7×** |

The physical `decrease = 8` means small biters **can't damage it at all**.
Since the technology requires `logistics-3` + `military-3` + production
science, by the time you have it small biters are no longer a threat, so in
practice this breaks nothing. If it still feels excessive, dropping
`decrease` to 4 puts them back in the game.

Against behemoths — the number that actually matters — it's still **~10×**.

---

## 5. Design decisions

### Side-branch, not a higher tier

With Space Age installed, the turbo belt sits above express. Making armored
faster than turbo would have obsoleted a whole expansion tier. Instead:

- Same speed as express.
- **`next_upgrade = nil`**, so upgrade planners leave it alone.
- **`fast_replaceable_group = "transport-belt"` kept**, so an existing
  frontline can be retrofitted by laying armored over it, without tearing
  anything down.

Those two properties together are the key to the mod's ergonomics: it drops
on top of what you already have, and nothing moves it afterward.

### Cloning instead of rewriting

All three entities come from a `table.deepcopy` of their express
counterparts. Connection points, sounds, animation timings and circuit
connector definitions come along for free and correct. Only name, icons,
health, resistances, corpse and sprite paths get swapped.

Cloning also brings along things that need checking, not just the ones you
expect. The express item carries `color_hint.text = "3"` — the belt tier
number vanilla uses for a number-based accessibility display in place of
color — and the `deepcopy` inherits it unchanged. Since armored isn't a speed
tier, leaving it would have tagged the armored belt as "tier 3", the same as
express. It's set to explicit `nil` in `items.lua` so that display mode
doesn't label it with a number that doesn't apply.

---

## 6. Graphics: steel gray / titanium

### Why a tint alone wasn't enough

Factorio's `tint` field **multiplies** over the base sprite, and multiplying
can only darken channels, never lift them. Starting from a saturated cyan (low
R, high B), **no tint value produces neutral gray**. A first attempt with a
gunmetal tint still read as blueish, for exactly this reason.

### The finding that simplified everything

Analyzing the sprites showed they're **already mostly metallic gray**:
between 44% and 59% of opaque pixels have saturation < 0.1. What makes them
read as blue is a **cyan accent (hue ≈ 180°)** on top of dark metal.

So there was no need to push anything to grayscale — that would have
flattened the tread and killed the sense of motion. It was enough to **strip
the chroma while keeping luminance intact**.

### Measured result

| | Before | After |
|---|---|---|
| Mean saturation | 0.159 | **0.013** |
| Pixels with saturation > 0.3 | 11.8% | **0.1%** |
| Mean luminance | 0.277 | 0.294 *(+6%)* |
| Mean RGB | (76, 68, 65) | **(74, 74, 76)** |

Neutral with a minimal cool cast. Steel, not blue or dirty gray. And the
mechanical detail stays intact, because luminance was never touched.

### The pipeline

`tools/recolor.py` generates **17 sprites** from the vanilla PNGs: belt,
underground belt (structure + 2 patches), splitter (4 directions + 2 top
patches), 3 item icons, the technology icon, and **the 3 corpse
prototypes** — without those, a destroyed armored belt would leave blue
express wreckage on the ground.

Tunable constants at the top of the script:

```python
DESAT    = 0.92                   # 1.0 = fully neutral gray
CONTRAST = 0.12                   # smoothstep, keeps plating crisp
LIFT     = 1.10                   # midtone gamma; bare metal reads brighter
TINT     = (0.965, 0.978, 1.000)  # faint cool cast -> steel, not warm
```

**HSL lightness** `(max+min)/2` is used instead of perceptual luma
`0.21/0.72/0.07`: with luma, a saturated cyan would collapse to dark gray and
lose the apparent brightness of the chevrons.

Re-tuning the color is just a matter of tweaking the constants and running:

```
python tools/recolor.py
```

### Fail-proof syncing

The script writes `prototypes/graphics-map.lua` **from the files it actually
produced**. The Lua remaps paths against that map while walking the cloned
prototype: a path not in the map is left untouched, and one that is in it is
guaranteed to exist on disk.

Consequence: **a prototype can never point at a sprite that doesn't exist**.
Add a sprite to the script, and the Lua picks it up on its own.

---

## 7. Bugs found during development

The first three were silent: none of them failed the load.

1. **Inherited `next_upgrade`.** The express `deepcopy` carried over
   `next_upgrade = "turbo-transport-belt"` from Space Age. It would have
   pulled armored belts into the automatic upgrade chain, exactly the
   opposite of what was intended. → set to `nil`.

2. **Wreckage with a blue icon.** `corpse` prototypes carry their own `icon`
   field, independent of the entity's. Without fixing it, the wreckage entry
   in Factoriopedia kept showing the express's cyan icon. → `corpse.icons`
   reassigned.

3. **Dangling `shared.tint`.** Rewriting `shared.lua` for the remap approach
   removed `shared.tint`, but `technology.lua` still referenced it. In Lua
   that doesn't fail: it evaluates to `nil`. **The research icon was
   quietly staying untinted blue** and `--dump-data` passed without a
   complaint. → fixed by folding `logistics-3.png` into the recolor pipeline
   itself.

4. **Resistances overwritten wholesale.** Assigning `entity.resistances`
   outright discarded whatever the cloned entity already had. Express
   underground belts carry **30% impact resistance** in vanilla, so the
   armored underground belt ended up *more* fragile than express against
   vehicle collisions — exactly the opposite of what an armored side-branch
   promises. `tools/run_tests.py` caught it, not a code read. →
   `shared.apply_resistances()` merges and keeps the higher value per damage
   type.

The third is the argument for verifying the result and not just the absence
of errors. The fourth is the argument for having tests: nothing failed,
nothing looked wrong, and the mod still broke its own premise.

---

## 8. Automated verification

```
python tools/run_tests.py            # everything, against the current dump
python tools/run_tests.py --dump     # relaunches the data stage, then tests
python tools/run_tests.py -k balance # a single suite
python tools/run_tests.py -v         # lists every assertion
```

**333 assertions across 30 tests**, four suites, no dependencies beyond
Pillow and numpy (already required by `recolor.py`). No pytest: the harness
is 133 lines in `tools/tests/harness.py`, so the suite runs with a bare
`python`. Assertions are recorded rather than raised, so one bad value
reports a failure instead of aborting the rest.

| Suite | What it covers |
|---|---|
| `manifest` | `info.json`, every `require()` resolves, locale keys in both languages (no orphans, no duplicates, no Spanish left copied from English), the junction and its activation in `mod-list.json` |
| `graphics` | all 17 sprites in both directions (nothing in the map without a PNG, no PNG outside the map), **the vanilla source still exists**, identical dimensions, alpha channel intact bit-for-bit, and the §6 color figures recomputed |
| `data stage` | health, speed, resistances, `next_upgrade`, corpses, items, recipes, technology, that every referenced sprite exists on disk, and that **vanilla is left untouched** |
| `balance` | enemy damage pulled from the dump by following streams and projectiles, the §4 table recomputed, and the §3 premise re-validated against the game's own data |

Two tests deserve a separate mention because they check the mod's
**assumptions**, not the mod itself: one verifies that the express sprite
each recolor starts from still exists in `base` — if Factorio renames it, the
remap doesn't fail, it stays silent and the belt goes back to being blue —
and another that no vanilla belt has gained explosion resistance, which is
the mod's entire reason for existing.

The suite runs the same from the directory linked into `mods/` as from a
plain clone: the two tests that describe the *installation* rather than the
mod — the junction and dump freshness — skip themselves outside the live
copy instead of failing and masking a real failure.

The suite was validated by **mutation**: six fields were sabotaged in a copy
of the dump (health, `next_upgrade`, resistances, an ingredient, a
prerequisite, and a corpse icon), and all six were caught, several by more
than one test.

### The real data stage

```
Factorio.exe --dump-data
```

Boots the game, processes every prototype from every active mod, writes
`script-output/data-raw-dump.json`, and exits. It's the real data-stage check
without opening a save.

Against that 29 MB dump, the following was checked programmatically:

- Final health, speed, resistance and `next_upgrade` values for the three
  entities.
- Ingredients, results and enabled state of the three recipes.
- Prerequisites, effects and cost of the technology.
- That the 4 icon definitions have the expected shape.
- That **the 17 referenced sprites exist on disk**.
- That **not a single graphical reference to express survives** across the 6
  entities and corpses (only the `.ogg` files remain, intentionally: the
  express sound matches that speed).

Final result: `exit 0`, `Factorio initialised` → `Goodbye`, zero errors,
loading alongside Space Age and 30 other mods.

> Note: `--dump-icon-sprites` exists but writes nothing without graphical
> context. The comparison previews were generated by replicating Factorio's
> icon-layer math in Python (32px reference space, default `scale` of
> `32/icon_size`, `shift` in pixels from center).

---

## 9. Project structure

```
armored-belts/
├── info.json
├── data.lua
├── README.md
├── prototypes/
│   ├── shared.lua           resistances, health, sprite remapping, icons
│   ├── graphics-map.lua     GENERATED by recolor.py -- do not edit by hand
│   ├── entities.lua         clones the 3 entities + 3 corpses
│   ├── items.lua
│   ├── recipes.lua
│   └── technology.lua
├── locale/
│   ├── en/strings.cfg
│   └── es-ES/strings.cfg
├── graphics/
│   ├── entity/              belt, underground belt, splitter (+ remnants)
│   ├── icons/               3 item icons
│   └── technology/
└── tools/
    ├── recolor.py           generates graphics/ and graphics-map.lua
    ├── run_tests.py         runner; --dump relaunches the data stage
    └── tests/
        ├── harness.py       test registration and assertions
        ├── context.py       paths, loaders, damage formula
        ├── test_manifest.py
        ├── test_graphics.py
        ├── test_data_stage.py
        └── test_balance.py
```

### Development environment

The mod lives at `C:\Users\<user>\test\armored-belts` and is linked into the
mods folder via a **directory junction**:

```
mklink /J "%APPDATA%\Factorio\mods\armored-belts" "C:\Users\<user>\test\armored-belts"
```

You edit it in the working directory and the game sees it instantly, no
copying needed. Enabled in `mods/mod-list.json`.

---

## 10. Ideas for later

- **Balance:** `decrease = 8` on physical makes small biters unable to damage
  it. Justifiable given how late the tech unlocks, but dropping it to 4 would
  bring them back into play if more tension is wanted.
- **Space Age:** an armored variant of the turbo belt, so endgame players
  don't have to trade speed for armor.
- **Tungsten plates** as an alternate ingredient when Space Age is active —
  more thematic than steel for armor plating.
- **Original art** instead of recoloring: rivets, welded plating, worn edges.
  The recolor holds up well, but original art is what separates a mod that
  looks like a reskin from one that looks like its own thing.
