-- The armored line is a side-grade of express: identical throughput, heavily
-- reinforced. Cloning the express prototypes means all the connection points,
-- sounds and animation timings come along for free; only the sprite filenames
-- are swapped for the recolored steel ones.

local shared = require("prototypes.shared")

-- Remnants are separate prototypes referenced by name, so they need cloning too
-- or a destroyed armored belt would leave blue express wreckage behind.
local function clone_corpse(source_name, new_name, icon_name)
  local corpse = table.deepcopy(data.raw.corpse[source_name])
  corpse.name = new_name
  -- Corpses carry their own icon for Factoriopedia; without this the wreckage
  -- entry would still show the blue express icon.
  corpse.icons = shared.icons(icon_name)
  corpse.icon = nil
  shared.remap_graphics(corpse)
  data:extend{corpse}
  return new_name
end

local function clone_express(source_type, source_name, new_name, health)
  local entity = table.deepcopy(data.raw[source_type][source_name])

  entity.name = new_name
  entity.icons = shared.icons(new_name)
  entity.icon = nil
  entity.minable = {mining_time = 0.1, result = new_name}
  entity.max_health = health
  shared.apply_resistances(entity)
  entity.corpse = clone_corpse(source_name .. "-remnants",
                               new_name .. "-remnants", new_name)

  -- Inherited from express: in Space Age this points at the turbo variants.
  -- Armored belts are a dead end on purpose, so upgrade planners leave them be.
  entity.next_upgrade = nil

  -- The inherited simulation would show express belts in Factoriopedia.
  entity.factoriopedia_simulation = nil

  -- Deliberately keeping fast_replaceable_group = "transport-belt" so an
  -- existing frontline can be retrofitted in place without tearing it down.

  shared.remap_graphics(entity)

  return entity
end

local belt = clone_express("transport-belt", "express-transport-belt",
                           "armored-transport-belt", shared.belt_health)
belt.related_underground_belt = "armored-underground-belt"

local underground = clone_express("underground-belt", "express-underground-belt",
                                  "armored-underground-belt", shared.belt_health)

local splitter = clone_express("splitter", "express-splitter",
                               "armored-splitter", shared.splitter_health)
splitter.related_transport_belt = "armored-transport-belt"

data:extend{belt, underground, splitter}
