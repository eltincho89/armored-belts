-- Shared constants and helpers for the armored belt line.

local graphics_map = require("prototypes.graphics-map")

local shared = {}

-- Enemies only ever deal physical (biter melee) and acid (spitter/worm spit).
-- Fire and explosion cover friendly fire: your own flamethrower turret line,
-- artillery, rockets and burning trees, which is what usually eats a frontline
-- belt in practice.
shared.resistances =
{
  {type = "fire",      percent = 95},
  {type = "explosion", percent = 80, decrease = 15},
  {type = "physical",  percent = 60, decrease = 8},
  {type = "acid",      percent = 60, decrease = 5}
}

shared.belt_health = 600
-- Splitters scale up the same way vanilla does (190/170 of a belt).
shared.splitter_health = 670

-- A cloned prototype can carry resistances the armor set says nothing about:
-- underground belts ship with 30% impact against vehicle collisions. Replacing
-- the list wholesale would silently drop those and make the armored variant
-- worse than the express belt it replaces at something, which a side-grade must
-- never be. So merge instead, and let the higher value win per damage type.
function shared.apply_resistances(entity)
  local merged, index = {}, {}

  local function put(resistance)
    local existing = index[resistance.type]
    if existing then
      existing.percent = math.max(existing.percent or 0, resistance.percent or 0)
      local decrease = math.max(existing.decrease or 0, resistance.decrease or 0)
      existing.decrease = decrease > 0 and decrease or nil
    else
      local copy = table.deepcopy(resistance)
      index[resistance.type] = copy
      merged[#merged + 1] = copy
    end
  end

  for _, resistance in pairs(entity.resistances or {}) do put(resistance) end
  for _, resistance in pairs(shared.resistances) do put(resistance) end

  entity.resistances = merged
  return entity
end

-- Repoints every sprite in a cloned prototype at its recolored counterpart.
--
-- Walking the whole prototype is safe because graphics-map.lua is generated
-- from the files that were actually written to disk and contains nothing but
-- express belt sprites: an unlisted filename is left untouched, and a listed
-- one is guaranteed to exist.
local function remap(node, seen)
  if type(node) ~= "table" then return end
  if seen[node] then return end
  seen[node] = true

  local replacement = node.filename and graphics_map[node.filename]
  if replacement then
    node.filename = replacement
  end

  for _, child in pairs(node) do
    remap(child, seen)
  end
end

function shared.remap_graphics(prototype)
  remap(prototype, {})
  return prototype
end

-- The recolored sprite is gray enough to read as its own tier at a glance, so
-- the icon needs no badge on top of it.
function shared.icons(name)
  return
  {
    {
      icon = "__armored-belts__/graphics/icons/" .. name .. ".png",
      icon_size = 64
    }
  }
end

return shared
