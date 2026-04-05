# vizzy_tool.py — Vizzy XML Builder & Editor for Juno: New Origins

A Python tool for reading, writing, validating and building Vizzy programs
for SimpleRockets 2 / Juno: New Origins, without opening the game editor.

---

## Requirements

- Python 3.8 or newer (no extra packages needed)
- Works from any terminal/command prompt

---

## Quick Start

```bash
# From the UserData directory:
cd "C:\Users\<you>\AppData\LocalLow\Jundroo\SimpleRockets 2\UserData"

python vizzy_tool.py list                       # list all programs
python vizzy_tool.py read SimpleLaunch          # display a program
python vizzy_tool.py validate                   # validate all programs
python vizzy_tool.py validate "MFD Stats"       # validate one program
python vizzy_tool.py new "My Program"           # create blank program
python vizzy_tool.py new "My MfD"  --mfd        # create blank MfD program
```

---

## CLI Reference

| Command | Description |
|---------|-------------|
| `list` | Lists all `.xml` files in `FlightPrograms/`, their block count, and any embedded programs in craft files |
| `read <name>` | Pretty-prints the block structure of a program. Name can be partial (e.g. `read Orion`) |
| `validate [name]` | Checks XML structure, duplicate IDs, missing sections. Without a name, validates all programs |
| `new <name> [--mfd]` | Creates a blank program with an `on_start` event and saves it to `FlightPrograms/` |

---

## Library Usage

Import the tool from your own scripts or use it interactively:

```python
from vizzy_tool import VizzyProgram, E
```

### `VizzyProgram` — build a complete program

```python
prog = VizzyProgram("My Program")           # normal program
prog = VizzyProgram("My MfD", requires_mfd=True)  # MfD program
```

#### Declare variables first

```python
prog.var("altitude", 0)          # numeric variable, initial value 0
prog.var("speed", 0)
prog.var("altitudes", is_list=True)   # list variable
prog.var("names", is_list=True)
```

#### Build instructions

All instruction methods return an `xml.etree.ElementTree.Element`.
Add them to `prog.root_instructions`:

```python
instr = prog.root_instructions

instr.append(prog.on_start())
instr.append(prog.comment("Start engine"))
instr.append(prog.set_input("throttle", E.num(1)))
instr.append(prog.activate_stage())
instr.append(prog.display(E.text("Launched!")))
```

#### Loops and conditionals

```python
# while loop
wh = prog.while_loop(E.TRUE())
body = wh.find("Instructions")
body.append(prog.wait_seconds(E.num(1)))
body.append(prog.display(E.join(E.text("Alt: "), E.prop("Altitude.ASL", "prop-altitude"))))
instr.append(wh)

# for loop (i from 1 to 10 step 1)
fl = prog.for_loop("i", 1, 10, 1)
body = fl.find("Instructions")
body.append(prog.display(E.join(E.text("Step "), E.local_var("i"))))
instr.append(fl)

# if / else if / else
ifb = prog.if_block(E.gt(E.prop("Altitude.ASL", "prop-altitude"), E.num(10000)))
ifb.find("Instructions").append(prog.set_pitch(E.num(45)))
instr.append(ifb)
eib = prog.else_if_block(E.gt(E.prop("Altitude.ASL", "prop-altitude"), E.num(5000)))
eib.find("Instructions").append(prog.set_pitch(E.num(70)))
instr.append(eib)
eb = prog.else_block()
eb.find("Instructions").append(prog.set_pitch(E.num(90)))
instr.append(eb)
```

#### Save

```python
prog.save()                      # saves as "My Program.xml" in FlightPrograms/
prog.save("custom_name.xml")     # custom filename
xml_string = prog.to_xml()       # get XML as string without saving
```

---

## E — Expression Helpers

`E` is a factory class for building expression nodes (values, operators, data).
These are used as arguments to instruction methods.

### Constants

```python
E.num(1)          # number
E.num(3.14)
E.text("hello")   # string / text
E.TRUE()          # boolean true
E.FALSE()         # boolean false
```

### Variables

```python
E.var("myVar")            # global variable
E.local_var("i")          # local variable (inside for/custom function)
E.list_var("myList")      # list variable reference
```

### Craft Properties (sensor data)

```python
E.prop("Altitude.ASL", "prop-altitude")
E.prop("Orbit.Apoapsis", "prop-orbit")
E.prop("Vel.SurfaceVelocity", "prop-velocity")
E.prop("Performance.Mass", "prop-performance")
E.prop("Input.Throttle", "prop-input")
E.prop("Misc.Grounded", "prop-misc")
E.prop("Time.TimeSinceLaunch", "prop-time")
E.prop("Nav.Position", "prop-nav")
E.prop("Fuel.FuelInStage", "prop-fuel")
```

See **PROP_STYLES table** in the tool's docstring for the complete list.

### Part and Craft lookups

```python
E.part_id("EngineName")                          # get part ID by name
E.craft_id("CraftName")                          # get craft ID by name
E.part_prop("Part.Mass", E.part_id("Engine1"))   # read part property
E.craft_prop("Craft.Position", E.craft_id("Ship2"))  # read craft property
E.planet_prop("radius", E.prop("Orbit.Planet", "prop-name"))   # read planet radius (current planet)
E.planet_prop("atmosphereHeight", E.text("Droo"))               # read a named planet's property
E.activation_group(1)                             # true if AG1 is active
```

### Arithmetic

```python
E.add(a, b)    # a + b
E.sub(a, b)    # a - b
E.mul(a, b)    # a * b
E.div(a, b)    # a / b
E.pow(a, b)    # a ^ b
E.mod(a, b)    # a % b
E.rand(a, b)   # random number between a and b
E.min2(a, b)   # min of a and b
E.max2(a, b)   # max of a and b
E.atan2(y, x)  # atan2(y, x) in radians
E.sum(a, b, c, ...)  # sum of any number of values
```

### Comparisons

```python
E.eq(a, b)   # a = b
E.lt(a, b)   # a < b
E.lte(a, b)  # a <= b
E.gt(a, b)   # a > b
E.gte(a, b)  # a >= b
```

### Boolean

```python
E.and_(a, b)  # a AND b
E.or_(a, b)   # a OR b
E.not_(a)     # NOT a
```

### Math functions

```python
E.math("abs", x)       E.math("sqrt", x)
E.math("floor", x)     E.math("sin", x)
E.math("ceiling", x)   E.math("cos", x)
E.math("round", x)     E.math("tan", x)
E.math("ln", x)        E.math("asin", x)
E.math("log", x)       E.math("acos", x)
E.math("deg2rad", x)   E.math("atan", x)
E.math("rad2deg", x)
```

### Ternary

```python
E.cond(condition, then_value, else_value)
# equivalent to: if condition then then_value else else_value
```

### Strings

```python
E.join(E.text("Speed: "), E.var("speed"), E.text(" m/s"))
E.length_str(s)              # length of string s
E.letter(E.num(1), s)        # first letter of s  (1-indexed)
E.substr(E.num(2), E.num(4), s)  # letters 2 to 4
E.contains(s, E.text("hello"))
E.format(E.text("{0:n2}"), val)  # C# String.Format
E.friendly("distance", val)     # human-readable distance
E.hex_color("#FF8800")          # hex string -> RGB vector
```

### Vectors

```python
E.vec(E.num(1), E.num(0), E.num(0))   # create vector (1,0,0)
E.vec(x, y, z)                         # x/y/z can be any expressions

E.vec1("x", v)          # x component of vector v
E.vec1("y", v)          # y component
E.vec1("z", v)          # z component
E.vec1("length", v)     # magnitude
E.vec1("norm", v)       # normalized (unit vector)

E.vec2("dot",     v1, v2)   # dot product
E.vec2("cross",   v1, v2)   # cross product
E.vec2("dist",    v1, v2)   # distance between points
E.vec2("angle",   v1, v2)   # angle in degrees
E.vec2("project", v1, v2)   # project v1 onto v2
E.vec2("scale",   v1, v2)   # component-wise multiply
E.vec2("min",     v1, v2)   # component-wise min
E.vec2("max",     v1, v2)   # component-wise max
E.vec2("clamp",   v1, v2)   # clamp v1 by v2
```

### Lists (read-only, return a value)

```python
E.list_get(E.list_var("alts"), E.num(1))        # item at index (1-based)
E.list_get(E.list_var("alts"), E.var("i"))       # item at variable index
E.list_length(E.list_var("myList"))             # number of items
E.list_index(E.list_var("names"), E.text("Bob"))# position of "Bob" (or -1)
E.list_create("10,20,30")                       # inline list creation
```

### Coordinate conversions

```python
E.to_lat_long_agl(pci_vec)   # PCI position -> lat/long/AGL vector
E.to_lat_long_asl(pci_vec)   # PCI position -> lat/long/ASL vector
E.to_position(ll_vec)         # lat/long/AGL -> PCI position vector
E.terrain_height(ll_vec)      # terrain height at lat/long
E.terrain_color(ll_vec)       # terrain color at lat/long
```

### Custom and special

```python
E.call_expr("MyExpr", arg1, arg2)    # call custom expression
E.funk("FlightData.CurrentMassUnscaled * 9.81")  # raw inline expression
E.note_frequency("C#", 4)            # musical note frequency
```

---

## Instruction Reference

### Events (standalone trigger blocks)

```python
prog.on_start()
prog.on_collision(part_var, other_var, vel_var, impulse_var)
prog.on_explode(part_var)
prog.on_docked(craft_a_var, craft_b_var)
prog.on_enter_soi(planet_var)
prog.receive_message("myMessage", "dataVar")
```

> **Note on `receive_message`**: This creates a standalone event block.
> Its handler instructions go as siblings AFTER it, not inside it.
> Use `prog.next_thread()` to separate it visually from the main thread.

### Control flow

```python
prog.while_loop(condition)           # body: el.find("Instructions")
prog.if_block(condition)
prog.else_if_block(condition)
prog.else_block()
prog.for_loop("i", start, end, step)
prog.repeat_loop(count)
prog.break_loop()
prog.wait_seconds(E.num(2))          # wait 2 seconds
prog.wait_seconds(E.num(0))          # wait one frame
prog.wait_until(condition)
```

### Output

```python
prog.display(E.text("Hello!"), duration=7)   # show on screen for 7s
prog.flight_log(E.text("message"))           # write to flight log
prog.local_log(E.text("debug"))              # write to local part log
prog.comment("This is a comment")
```

### Craft control

```python
prog.activate_stage()
prog.set_input("throttle", E.num(1))       # 0.0 to 1.0
prog.set_input("pitch", E.num(0))          # -1.0 to 1.0
prog.set_input("yaw", E.num(0))
prog.set_input("roll", E.num(0))
prog.set_input("brake", E.TRUE())
prog.set_input("slider1", E.num(0.5))
prog.set_input("slider2", E.num(0))
prog.set_pitch(E.num(45))                  # set pitch degrees
prog.set_heading(E.num(90))                # set heading degrees
prog.lock_heading("Prograde")              # Current|None|Prograde|Retrograde
prog.lock_heading_vector(vec_expr)
prog.set_activation_group(1, E.TRUE())
prog.set_target(E.text("Mun"))
prog.set_time_mode("FastForward")          # Normal|Paused|FastForward|SlowMotion
prog.set_camera("zoom", E.num(100))
prog.set_part(E.part_id("Engine1"), "Part.SetActivated", E.TRUE())
prog.switch_craft(E.craft_id("Probe"))
prog.play_beep(E.num(440), E.num(1), E.num(0.5))
```

### Variables

```python
prog.set_var("myVar", E.num(42))
prog.set_var("myVar", E.prop("Altitude.ASL", "prop-altitude"))
prog.change_var("counter", E.num(1))       # counter += 1
prog.user_input("myVar", "Enter value:")
```

### List instructions (mutate a list)

```python
prog.list_add("myList", E.text("item"))
prog.list_remove("myList", E.num(1))
prog.list_clear("myList")
prog.list_init_from_csv("altitudes", "0,5000,10000,50000")

# These may not exist in all game versions:
prog.list_insert("myList", E.num(2), E.text("item"))
prog.list_set("myList", E.num(1), E.text("new"))
prog.list_sort("myList")
prog.list_reverse("myList")
```

### Broadcasting

```python
prog.broadcast("myMessage", E.num(42))                 # within this vizzy
prog.broadcast("myMessage", E.var("data"), "craft")    # all craft vizzys
prog.broadcast("myMessage", E.var("data"), "nearby")   # all nearby crafts
```

---

## MfD (Multi-function Display) Programs

MfD programs require `requires_mfd=True` and access a special screen widget.
The root widget `"_Screen"` always exists and represents the display area.

```python
prog = VizzyProgram("My Display", requires_mfd=True)
prog.var("value", 0)
instr = prog.root_instructions

instr.append(prog.on_start())

# Create a label widget
instr.append(prog.mfd_create("Label", "myLabel"))

# Size it relative to screen
instr.append(prog.mfd_set_size("myLabel",
    E.vec2("scale",
        E.prop("Mfd.Size", "prop-mfd-widget"),  # _Screen size
        E.vec(0.9, 0.9, 0)
    )
))

instr.append(prog.mfd_set_color("myLabel", "#00FF88"))
instr.append(prog.mfd_set_autosize("myLabel", True))
instr.append(prog.mfd_set_alignment("myLabel", "TopLeft"))

# Update in a loop
wh = prog.while_loop(E.TRUE())
wh.find("Instructions").append(
    prog.mfd_set_text("myLabel",
        E.join(E.text("Alt: "), E.prop("Altitude.ASL", "prop-altitude"))
    )
)
wh.find("Instructions").append(prog.wait_seconds(E.num(0.1)))
instr.append(wh)
```

### Widget types

| Type | Description |
|------|-------------|
| `Label` | Text display |
| `Ellipse` | Circle or ellipse shape |
| `Rectangle` | Rectangle shape |
| `Line` | Line segment |
| `Texture` | Programmable pixel texture |
| `Navball` | Attitude indicator |
| `Map` | Planet map |
| `RadialGauge` | Circular gauge |

### Widget events

```python
# Make widget broadcast a message when clicked
instr.append(prog.mfd_event("btn1", "Click", "button_pressed", E.text("btn1")))

# Handle the message in a second thread
prog.next_thread()
instr.append(prog.receive_message("button_pressed", "btnData"))
instr.append(prog.display(E.join(E.text("Pressed: "), E.var("btnData"))))
```

---

## Multiple Event Handlers (Threads)

In the Vizzy canvas, event handlers are separate visual threads at different
X positions. Call `prog.next_thread()` before each additional event handler
to offset it correctly:

```python
instr = prog.root_instructions

# Thread 1 — main loop
instr.append(prog.on_start())
instr.append(prog.set_input("throttle", E.num(1)))
wh = prog.while_loop(E.TRUE())
wh.find("Instructions").append(prog.wait_seconds(E.num(1)))
instr.append(wh)

# Thread 2 — message receiver
prog.next_thread()
instr.append(prog.receive_message("abort", "data"))
instr.append(prog.set_input("throttle", E.num(0)))
instr.append(prog.display(E.text("ABORT!")))

# Thread 3 — SOI change
prog.next_thread()
instr.append(prog.on_enter_soi("planet"))
instr.append(prog.display(E.join(E.text("Entered: "), E.var("planet"))))
```

---

## Custom Expressions and Instructions

```python
# Custom expression: round to N decimal places
n = E.local_var("n")
x = E.local_var("x")
round_expr = E.div(
    E.math("round", E.mul(x, E.pow(E.num(10), n))),
    E.pow(E.num(10), n)
)
prog.add_custom_expression("roundTo", ["x", "n"], round_expr)

# Use it
instr.append(prog.set_var("result", E.call_expr("roundTo", E.var("speed"), E.num(2))))

# Custom instruction: display and log
prog.add_custom_instruction("logShow", ["msg"], [
    prog.display(E.local_var("msg")),
    prog.flight_log(E.local_var("msg")),
])

# Call it
instr.append(prog.call_instruction("logShow", E.text("Hello!")))
```

---

## File Locations

| Path | Purpose |
|------|---------|
| `FlightPrograms/*.xml` | Standalone flight programs (loaded directly in game) |
| `FlightPrograms/_backups/` | Original backups (safe to ignore in game) |
| `CraftDesigns/*.xml` | Craft files with Vizzy embedded inside `<FlightProgram>` elements |

---

## Validation

```python
python vizzy_tool.py validate               # validate all programs
python vizzy_tool.py validate SimpleLaunch  # validate one
```

Checks:
- Valid XML syntax
- `<Variables>`, `<Instructions>`, `<Expressions>` sections present
- No duplicate block IDs

> **Note**: `orion-unified.xml` has pre-existing duplicate IDs (IDs 200–206).
> This is a known issue in that file, not caused by this tool.

---

## Craft File Utilities

From Python you can extract and display programs embedded in craft files:

```python
from vizzy_tool import extract_craft_program, list_craft_programs

# List all embedded programs
for craft, part_id, prog_name in list_craft_programs():
    print(craft, part_id, prog_name)

# Print a specific program's XML
extract_craft_program("Altair")        # first match
extract_craft_program("Altair", "3")   # specific part
```

---

## Critical: Known XML Bugs That Break Loading

> **If the game shows "Unable to load flight program" — one of these is the cause.**
> The game's `CraftPropertyExpression.OnDeserialized` throws an
> `InvalidOperationException` for any unrecognised property name or wrong tag,
> and the error message is the exact property string that failed.
> Check `Player.log` (`AppData\LocalLow\Jundroo\SimpleRockets 2\Player.log`)
> to see the full stack trace and property name.

### Bug 1 — UTF-8 BOM required

Every file written by Juno starts with the UTF-8 BOM (`\xef\xbb\xbf`).
Files saved without it load silently as an **empty program** (no error).

**Fix:** always write with `encoding="utf-8-sig"`.
`VizzyProgram.save()` does this automatically.
If you write XML directly (e.g. `path.write_text(...)`), use `utf-8-sig`.

```python
path.write_text(xml_string, encoding="utf-8-sig")   # correct
path.write_text(xml_string, encoding="utf-8")        # wrong — no BOM, empty in game
```

### Bug 2 — Planet properties use `<Planet op="...">`, NOT `<CraftProperty>`

To read a planet property (radius, mass, atmosphereHeight, etc.) you **must**
use the `<Planet>` XML tag with an `op=` attribute.
Using `<CraftProperty style="planet">` causes "Unable to load".

```xml
<!-- CORRECT -->
<Planet op="atmosphereHeight" style="planet">
  <CraftProperty property="Orbit.Planet" style="prop-name" />
</Planet>

<!-- WRONG — causes "Could not find property atmosphereHeight" -->
<CraftProperty property="atmosphereHeight" style="planet">
  <CraftProperty property="Orbit.Planet" style="prop-name" />
</CraftProperty>
```

In Python, always use `E.planet_prop(op, planet_expr)`:

```python
E.planet_prop("atmosphereHeight", E.prop("Orbit.Planet", "prop-name"))  # correct
E.prop_with("atmosphereHeight", "planet", ...)                           # WRONG
```

Valid `Planet op=` values confirmed from game files:
`mass`, `radius`, `atmosphereHeight`, `soiRadius`, `day`, `parent`,
`velocity`, `period`, `periapsis`, `eccentricity`, `inclination`,
`semiMajorAxis`, `crafts`, `craftIDs`, `solarPosition`, `childPlanets`,
`rightAscension`, `meanAnomaly`, `meanMotion`, `periapsisArgument`, `lengthOfDay`

### Bug 3 — `Name.Planet` does not exist

The property `Name.Planet` does not exist in the game registry and causes
"Could not find property Name.Planet".

To get the current planet's name as a string, use `Orbit.Planet` with
`prop-name` style:

```python
E.prop("Orbit.Planet", "prop-name")   # returns planet name string — CORRECT
E.prop("Name.Planet",  "prop-name")   # does NOT exist — causes load failure
```

### Summary table

| Symptom | Cause | Fix |
|---------|-------|-----|
| Program loads as empty (no blocks) | Missing UTF-8 BOM | Use `encoding="utf-8-sig"` |
| "Unable to load" on any file with `Planet` op | `<CraftProperty style="planet">` | Use `<Planet op="...">` / `E.planet_prop()` |
| "Unable to load" — log says `Name.Planet` | `property="Name.Planet"` | Use `property="Orbit.Planet"` |
| Custom expressions silently broken in editor | `id=` attribute on `<CustomExpression>` blocks in `<Expressions>` | Never add `id=` to custom expressions; the game ignores them in execution but the block ID 1–N range shifts |

### Bug 4 — `id=` on `<CustomExpression>` in `<Expressions>` section

When appending new custom expressions to an existing library, the tool's internal
`_id` counter assigns `id=` attributes to `CustomExpression` blocks.
**Original game-created expressions never have `id=`.**

The game tolerates this (no crash) but it pollutes the block ID registry and
shifts the ID range, which can confuse the editor's block-counting logic.

**Fix:** after generating custom expressions with `prog.add_custom_expression()`,
strip any `id=` attributes before saving, or build them using raw `ET.Element`
calls that don't go through `_instr()`. The `add_custom_expression` method in
`vizzy_tool.py` does NOT call `_instr()` so it produces id-free nodes — only
expressions built with lower-level builder methods are affected.

### Running the validator

```bash
python vizzy_tool.py validate                  # validates all files
python vizzy_tool.py validate "My Program"     # validates one file
```

The validator catches BOM issues, duplicate IDs, and the known-bad property names.

---

## Tips for Writing Vizzy Programs

1. **IDs are auto-managed** — never set them manually; the program builder
   assigns unique sequential IDs automatically.

2. **Positions are auto-managed** — canvas positions are assigned top-to-bottom
   at 150px spacing. Call `prog.next_thread()` to start a new visual column.

3. **Read before writing** — use `vizzy_tool.py read <name>` to study
   the structure of existing programs before writing new ones.

4. **Validate after generating** — always run `validate` on generated files
   before loading them in-game.

5. **Lists are 1-indexed** — `E.list_get(list, E.num(1))` returns the first item.

6. **join() auto-pads** — the `join` block always needs at least 3 child slots;
   `E.join()` adds empty string slots automatically.

7. **SetTargetHeading vs SetInput** — use `prog.set_pitch()` / `prog.set_heading()`
   for autopilot-style heading, and `prog.set_input("pitch", ...)` for raw control axis.

---

## Example: Complete Orbit Program

```python
from vizzy_tool import VizzyProgram, E

prog = VizzyProgram("Auto Orbit")

instr = prog.root_instructions
instr.append(prog.on_start())
instr.append(prog.lock_heading("Current"))
instr.append(prog.set_input("throttle", E.num(1)))
instr.append(prog.activate_stage())
instr.append(prog.display(E.text("Launching...")))

# Gravity turn at 8km
instr.append(prog.wait_until(
    E.gt(E.prop("Altitude.ASL", "prop-altitude"), E.num(8000))
))
instr.append(prog.set_pitch(E.num(45)))

# Wait for apoapsis > 120km
instr.append(prog.wait_until(
    E.gt(E.prop("Orbit.Apoapsis", "prop-orbit"), E.num(120000))
))
instr.append(prog.set_input("throttle", E.num(0)))
instr.append(prog.lock_heading("Prograde"))

# Coast to apoapsis, then circularize
instr.append(prog.wait_until(
    E.lt(E.prop("Orbit.TimeToApoapsis", "prop-orbit"), E.num(30))
))
instr.append(prog.set_input("throttle", E.num(1)))
instr.append(prog.wait_until(
    E.gt(E.prop("Orbit.Periapsis", "prop-orbit"), E.num(100000))
))
instr.append(prog.set_input("throttle", E.num(0)))
instr.append(prog.display(E.text("Orbit achieved!")))

prog.save()
```
