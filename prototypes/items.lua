local shared = require("prototypes.shared")

local function clone_item(source_name, new_name, order)
  local item = table.deepcopy(data.raw.item[source_name])

  item.name = new_name
  item.icons = shared.icons(new_name)
  item.icon = nil
  item.place_result = new_name
  item.order = order
  item.color_hint = {text = "A"}

  return item
end

data:extend
{
  clone_item("express-transport-belt", "armored-transport-belt",
             "a[transport-belt]-e[armored-transport-belt]"),
  clone_item("express-underground-belt", "armored-underground-belt",
             "b[underground-belt]-e[armored-underground-belt]"),
  clone_item("express-splitter", "armored-splitter",
             "c[splitter]-e[armored-splitter]")
}
