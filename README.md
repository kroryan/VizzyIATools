# VizzyIATools

Python tooling for reading, validating, generating, and editing Vizzy XML for Juno: New Origins without using the in-game editor.

The repository now uses a project-local layout. Generators write into the repository's own `FlightPrograms/` folder, and examples and docs live alongside the tool instead of depending on a separate global `UserData` layout.

Source examples are based on:
https://www.simplerockets.com/c/iM9KjM/Auto-Vizzy-USP-01-Universal-Space-Probe

## Project layout

| Path | Purpose |
|------|---------|
| `vizzy_tool.py` | Main library and CLI |
| `Generators/` | Python generators for ready-to-use Vizzy programs |
| `FlightPrograms/` | Generated standalone Vizzy XML files |
| `Example/Vizzy/` | Reference Vizzy XML programs |
| `Example/Craft/` | Example craft files with embedded Vizzy |
| `Docs/` | Project notes, investigations, and technical analysis |

## Requirements

- Python 3.8 or newer
- No third-party packages required

## Quick start

Run commands from the repository root:

```bash
python vizzy_tool.py list
python vizzy_tool.py read "Universal Orbit 200km - Auto"
python vizzy_tool.py validate
python vizzy_tool.py new "My Program"
python vizzy_tool.py new "My Mfd" --mfd
```

Generate the bundled programs:

```bash
python Generators/generate_universal_200km_orbit.py
python Generators/generate_target_transfer_scratch.py
python Generators/generate_target_transfer_vizzy.py
```

## What `vizzy_tool.py` provides

`vizzy_tool.py` serves three roles:

1. XML builder:
   create Vizzy programs from Python with `VizzyProgram`.
2. Expression DSL:
   build values and operators with `E`.
3. Utilities:
   list, read, validate, and inspect standalone or embedded Vizzy programs.

### Example

```python
from vizzy_tool import VizzyProgram, E

prog = VizzyProgram("My Program")
instr = prog.root_instructions

prog.var("speed", 0)

instr.append(prog.on_start())
instr.append(prog.set_input("throttle", E.num(1)))
instr.append(prog.activate_stage())
instr.append(prog.display(E.text("Launching...")))

loop = prog.while_loop(E.TRUE())
body = loop.find("Instructions")
body.append(prog.wait_seconds(E.num(1)))
body.append(prog.set_var("speed", E.prop("Vel.SurfaceVelocity", "prop-velocity")))
body.append(prog.display(E.join(E.text("Speed: "), E.var("speed"))))
instr.append(loop)

prog.save()
```

## Generator outputs

The repository currently includes these generated programs:

- `FlightPrograms/Universal Orbit 200km - Auto.xml`
- `FlightPrograms/Universal Target Transfer Scratch.xml`
- `FlightPrograms/Universal Target Transfer Auto.xml`

Their source generators are:

- `Generators/generate_universal_200km_orbit.py`
- `Generators/generate_target_transfer_scratch.py`
- `Generators/generate_target_transfer_vizzy.py`

## Validation

Validate every standalone program in `FlightPrograms/`:

```bash
python vizzy_tool.py validate
```

Validate a single program:

```bash
python vizzy_tool.py validate "Universal Target Transfer Scratch"
```

The validator checks:

- XML syntax
- required root sections
- duplicate block IDs
- known invalid craft and planet property usage

## Embedded craft programs

The tool can also inspect Vizzy embedded inside craft XML files.

```python
from vizzy_tool import extract_craft_program, list_craft_programs

for craft, part_id, program_name in list_craft_programs():
    print(craft, part_id, program_name)

extract_craft_program("Altair")
extract_craft_program("Altair", "3")
```

With the current repository layout, craft lookups use `Example/Craft/` when `CraftDesigns/` is not present.

## Important compatibility rules

These are the main XML rules that matter in practice:

### UTF-8 BOM is required

Juno-generated files use UTF-8 with BOM. Files written without BOM may load as empty programs.

Use:

```python
path.write_text(xml_string, encoding="utf-8-sig")
```

### Planet properties must use `<Planet op="...">`

Do not represent planet properties as `CraftProperty style="planet"`.

Correct:

```python
E.planet_prop("radius", E.prop("Orbit.Planet", "prop-name"))
```

### Use `Orbit.Planet`, not `Name.Planet`

To get the current planet name, use:

```python
E.prop("Orbit.Planet", "prop-name")
```

### Custom instructions and custom expressions must be serialized differently

- `CustomInstruction` blocks belong in separate root-level `<Instructions>` sections.
- `CustomExpression` blocks belong in `<Expressions>`.

This distinction is critical for the Vizzy editor to load generated XML correctly.

## Repository notes after the reorganization

- Generators are now meant to be executed from `Generators/`, but they automatically add the repository root to `sys.path`.
- `vizzy_tool.py` now prefers the repository-local `FlightPrograms/` directory when present.
- The example mission file is now stored as `Example/Vizzy/Universal Vizzy Mission 2.xml`.
- Documentation and investigations were moved into `Docs/`.

## Additional documentation

See:

- `Docs/ANALISIS_VIZZY_TOOL_Y_AUTOPILOTO_200KM.md`
- `Docs/INVESTIGACION_CARGA_VACIA_VIZZY.md`
- `Docs/SCRATCH_TRANSFER_ANALYSIS.md`
- `Docs/Mastering Vizzy _ A Complete Guide - Early Access 08.07.25.md`

## Recommended workflow

1. Study an existing program with `read`.
2. Generate or edit a program.
3. Run `validate`.
4. Load the resulting XML in Juno.
5. If Juno rejects a file, check `Player.log` for the exact failing property or node.
