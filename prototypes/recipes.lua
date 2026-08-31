-- Category "pressing" (no lubricant) so armored belts stay hand-craftable AND
-- match the vanilla belt/underground-belt/splitter recipes, which Space Age
-- moved off the default "crafting" category specifically so the Foundry
-- (Vulcanus) can produce them. Leaving this unset defaults to "crafting",
-- which the Foundry doesn't support -- the character can still hand-craft it,
-- but it disappears from the Foundry's recipe list.
-- Repairing a frontline mid-fight shouldn't require walking back to a chem plant.

data:extend
{
  {
    type = "recipe",
    name = "armored-transport-belt",
    category = "pressing",
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
    category = "pressing",
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
    category = "pressing",
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
