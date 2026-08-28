-- Gated behind both branches it draws from: express belts (logistics-3) and
-- combat hardening (military-3).

data:extend
{
  {
    type = "technology",
    name = "armored-belts",
    icon = "__armored-belts__/graphics/technology/armored-belts.png",
    icon_size = 256,
    effects =
    {
      {type = "unlock-recipe", recipe = "armored-transport-belt"},
      {type = "unlock-recipe", recipe = "armored-underground-belt"},
      {type = "unlock-recipe", recipe = "armored-splitter"}
    },
    prerequisites = {"logistics-3", "military-3"},
    unit =
    {
      count = 200,
      ingredients =
      {
        {"automation-science-pack", 1},
        {"logistic-science-pack", 1},
        {"military-science-pack", 1},
        {"chemical-science-pack", 1},
        {"production-science-pack", 1}
      },
      time = 30
    }
  }
}
