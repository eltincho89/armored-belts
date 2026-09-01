-- Category "pressing" (no lubricant) so armored belts stay hand-craftable AND
-- match the vanilla belt/underground-belt/splitter recipes, which Space Age
-- moved off the default "crafting" category specifically so the Foundry
-- (Vulcanus) can produce them. Leaving this unset defaults to "crafting",
-- which the Foundry doesn't support -- the character can still hand-craft it,
-- but it disappears from the Foundry's recipe list.
--
-- "pressing" is a Space Age recipe-category: it doesn't exist without the
-- expansion, and referencing an undefined category by name is a hard crash
-- at data stage ("Error in assignID: recipe-category with name 'pressing'
-- does not exist"), not a graceful no-op -- this crashed for anyone running
-- the mod without Space Age (or with it disabled). Vanilla itself never
-- hits this: it defines transport-belt/underground-belt/splitter with the
-- plain default category in base, and space-age/base-data-updates.lua only
-- *reassigns* them to "pressing" from data-updates.lua, a script that
-- simply never runs when the expansion is off. We can't reuse that trick
-- (our recipes don't exist for space-age to reassign), so this checks
-- presence directly instead.
--
-- Deliberately NOT declaring space-age as a dependency in info.json for
-- this: an optional dependency would force space-age to load before us,
-- and its own data-updates.lua directly mutates the *shared* express
-- prototypes (e.g. frozen_patch graphics for Gleba) before our clone runs,
-- leaking an express sprite reference into the armored entities. The
-- `mods` table reflects every enabled mod regardless of load order, so the
-- category check below is safe without that dependency; only a mod that
-- reads or mutates space-age's own prototypes would need one.
local category = mods["space-age"] and "pressing" or "crafting"

data:extend
{
  {
    type = "recipe",
    name = "armored-transport-belt",
    category = category,
    enabled = false,
    energy_required = 1,
    ingredients =
    {
      {type = "item", name = "express-transport-belt", amount = 1},
      {type = "item", name = "steel-plate", amount = 4}
    },
    results = {{type = "item", name = "armored-transport-belt", amount = 1}}
  },
  {
    type = "recipe",
    name = "armored-underground-belt",
    category = category,
    enabled = false,
    energy_required = 2,
    ingredients =
    {
      {type = "item", name = "express-underground-belt", amount = 2},
      {type = "item", name = "steel-plate", amount = 10}
    },
    results = {{type = "item", name = "armored-underground-belt", amount = 2}}
  },
  {
    type = "recipe",
    name = "armored-splitter",
    category = category,
    enabled = false,
    energy_required = 2,
    ingredients =
    {
      {type = "item", name = "express-splitter", amount = 1},
      {type = "item", name = "steel-plate", amount = 8}
    },
    results = {{type = "item", name = "armored-splitter", amount = 1}}
  }
}
