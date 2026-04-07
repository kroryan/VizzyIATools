#!/usr/bin/env python3
"""
vizzy_tool.py  -  Vizzy XML builder, reader, and editor for Juno: New Origins
==============================================================================

CLI
---
  python vizzy_tool.py list                     list all flight programs
  python vizzy_tool.py read <name_or_file>      pretty-print a program
  python vizzy_tool.py validate <name_or_file>  check XML structure
  python vizzy_tool.py new <name> [--mfd]       create blank program

LIBRARY QUICK-START
-------------------
  from vizzy_tool import VizzyProgram, E

  prog = VizzyProgram("My Launch")
  prog.var("speed", 0)
  instr = prog.root_instructions

  instr.append(prog.on_start())
  instr.append(prog.display(E.text("3, 2, 1...")))
  instr.append(prog.set_input("throttle", E.num(1)))
  instr.append(prog.activate_stage())

  wh = prog.while_loop(E.TRUE())
  inner = wh.find("Instructions")
  inner.append(prog.wait_seconds(E.num(1)))
  inner.append(prog.set_var("speed", E.prop("Vel.SurfaceVelocity", "prop-velocity")))
  inner.append(prog.display(E.join(E.text("Speed: "), E.var("speed"))))
  instr.append(wh)

  prog.save("My Launch.xml")

=============================================================================
EXPRESSION HELPERS  (class E)
=============================================================================

CONSTANTS
  E.num(1)                       <Constant number="1"/>
  E.text("hello")                <Constant text="hello"/>
  E.TRUE()                       boolean true constant
  E.FALSE()                      boolean false constant

VARIABLES
  E.var("name")                  global variable reference
  E.local_var("i")               local (loop/function) variable reference
  E.list_var("lst")              list variable reference

CRAFT PROPERTIES  -- E.prop(property, style)
  See PROP_STYLES table below for the full list.
  For properties that need a part/craft/planet argument, use E.prop_with():
    E.prop_with("Part.Mass", "part", E.part_id("EngineName"))
    E.prop_with("Craft.Position", "craft", E.craft_id("CraftName"))
    NOTE: planet ops use E.planet_prop(), NOT E.prop_with()
    E.planet_prop("radius", E.text("Droo"))           -- <Planet op="radius">
    E.planet_prop("atmosphereHeight", E.prop("Orbit.Planet","prop-name"))

SHORTCUT PROPERTY HELPERS
  E.part_id(name_expr)           CraftProperty Part.NameToID (style="part-id")
  E.craft_id(name_expr)          CraftProperty Craft.NameToID (style="craft-id")
  E.part_prop(property, id_expr) CraftProperty for a specific part
  E.craft_prop(property, id_expr)CraftProperty for a specific craft
  E.planet_prop(property, name)  CraftProperty for a planet by name
  E.activation_group(n)          ActivationGroup block - returns bool

ARITHMETIC
  E.add(a, b)   E.sub(a, b)   E.mul(a, b)   E.div(a, b)
  E.pow(a, b)   E.mod(a, b)   E.rand(a, b)
  E.min2(a, b)  E.max2(a, b)  E.atan2(y, x)
  E.sum(*values)                 Sum block (adds any number of values)

COMPARISONS
  E.eq(a,b)  E.lt(a,b)  E.lte(a,b)  E.gt(a,b)  E.gte(a,b)

BOOLEAN
  E.and_(a, b)  E.or_(a, b)  E.not_(a)

MATH FUNCTIONS  E.math(fn, a)
  abs | floor | ceiling | round | sqrt | sin | cos | tan |
  asin | acos | atan | ln | log | deg2rad | rad2deg

TERNARY
  E.cond(condition, then_val, else_val)

STRINGS
  E.join(*parts)                 concatenate (auto-pads to 3 args if needed)
  E.length_str(s)                string length
  E.letter(idx, s)               letter at 1-based index
  E.substr(from_idx, to_idx, s)  letters from-to
  E.contains(s, sub)             string contains
  E.format(fmt_expr, *args)      C# String.Format
  E.friendly(kind, val)          human-readable value (e.g. "distance")
  E.hex_color(hex_str)           "#FF0000" -> RGB vector

VECTORS
  E.vec(x, y, z)
  E.vec1(op, v)         op: x | y | z | length | norm
  E.vec2(op, v1, v2)    op: dot | cross | dist | angle | min | max |
                             project | scale | clamp

LISTS (read-only expressions)
  E.list_get(list_expr, index_expr)     item at index (1-based)
  E.list_length(list_expr)              number of items
  E.list_index(list_expr, item_expr)    index of item (or -1)
  E.list_create(csv_string)             create list from comma-separated string

SPECIAL
  E.funk(expr_str)               fUNk() inline expression string
  E.call_expr(name, *args)       call a custom expression
  E.note_frequency(note, octave) note: "C#", octave: 3

PLANET / COORDINATE EXPRESSIONS
  E.to_lat_long_agl(pci_vec)     PCI vector -> lat/long/AGL vector
  E.to_lat_long_asl(pci_vec)     PCI vector -> lat/long/ASL vector
  E.to_position(lat_long_vec)    lat/long/AGL -> PCI vector
  E.planet_day(planet_expr)      planet day length
  E.terrain_height(lat_long_expr) terrain height at lat/long
  E.terrain_color(lat_long_expr)  terrain color at lat/long
  E.cast_ray(from_vec, dir_vec)  ray cast

=============================================================================
PROP_STYLES for E.prop(property, style)
=============================================================================

  style            property examples
  -----------------------------------------------------------------------
  prop-altitude    Altitude.AGL | Altitude.ASL | Altitude.ASF
  prop-orbit       Orbit.Apoapsis | Orbit.Periapsis | Orbit.Period |
                   Orbit.TimeToApoapsis | Orbit.TimeToPeriapsis |
                   Orbit.Eccentricity | Orbit.Inclination
  prop-atmosphere  Atmosphere.AirDensity | Atmosphere.AirPressure |
                   Atmosphere.SpeedOfSound | Atmosphere.Temperature
  prop-performance Performance.Mass | Performance.CurrentEngineThrust |
                   Performance.MaxActiveEngineThrust | Performance.StageDeltaV |
                   Performance.BurnTime | Performance.TWR | Performance.CurrentIsp |
                   Performance.DryMass | Performance.FuelMass
  prop-fuel        Fuel.FuelInStage | Fuel.AllStages | Fuel.Battery | Fuel.Mono
  prop-velocity    Vel.SurfaceVelocity | Vel.OrbitVelocity | Vel.TargetVelocity |
                   Vel.Gravity | Vel.Drag | Vel.Acceleration | Vel.Angular |
                   Vel.LateralSurfaceVelocity | Vel.VerticalSurfaceVelocity |
                   Vel.MachNumber
  prop-input       Input.Throttle | Input.Pitch | Input.Yaw | Input.Roll |
                   Input.Slider1 | Input.Slider2 | Input.TranslationMode |
                   Input.Brake
  prop-misc        Misc.Stage | Misc.NumStages | Misc.Grounded |
                   Misc.SolarRadiation | Misc.PitchPID | Misc.RollPID
  prop-time        Time.TimeSinceLaunch | Time.TotalTime | Time.FrameDeltaTime |
                   Time.WarpAmount | Time.RealTime
  prop-name        Orbit.Planet | Target.Name | Target.Planet
                   NOTE: use Orbit.Planet (not Name.Planet) to get the current planet's name
  prop-nav         Nav.Position | Nav.North | Nav.East | Nav.CraftDirection |
                   Nav.AutopilotPitch | Nav.BankAngle | Target.Position
  part             Part.Mass | Part.DryMass | Part.Activated | Part.Temperature |
                   Part.PciToLocal | Part.LocalToPci | Part.ThisPartID |
                   Part.MinPartID | Part.MaxPartID | Part.UnderWater |
                   Part.PartType | Part.Name | Part.Drag
  part-id          Part.NameToID    (takes name string child)
  part-transform   Part.PciToLocal | Part.LocalToPci  (takes part_id + vec child)
  craft            Craft.Position | Craft.Planet | Craft.Periapsis |
                   Craft.Velocity | Craft.Altitude | Craft.Destroyed |
                   Craft.Grounded | Craft.Mass | Craft.Name | Craft.PartCount |
                   Craft.IsPlayer | Craft.BoundingBoxMin | Craft.BoundingBoxMax |
                   Craft.Apoapsis | Craft.Eccentricity | Craft.Inclination |
                   Craft.Period | Craft.TimeToApoapsis
  craft-id         Craft.NameToID   (takes name string child)
  planet           planet.Radius | planet.Mass | planet.AtmosphereHeight |
                   planet.SoiRadius | planet.SolarPosition | planet.ChildPlanets |
                   planet.Crafts | planet.CraftIDs | planet.Velocity |
                   planet.Period | planet.Periapsis | planet.Eccentricity |
                   planet.Inclination | planet.SemiMajorAxis |
                   planet.RightAscension | planet.MeanAnomaly | planet.MeanMotion |
                   planet.PeriapsisArgument | planet.Parent | planet.LengthOfDay
  prop-mfd-widget  Mfd.Size | Mfd.Position | Mfd.Color | Mfd.Opacity |
                   Mfd.Visible | Mfd.Scale | Mfd.Rotation | Mfd.Parent |
                   Mfd.ClickMessage | Mfd.DragMessage | Mfd.AnchoredPosition |
                   Mfd.AnchorMin | Mfd.AnchorMax | Mfd.Pivot
  prop-mfd-label   Mfd.Label.Text | Mfd.Label.FontSize | Mfd.Label.AutoSize |
                   Mfd.Label.Alignment
  prop-mfd-sprite  Mfd.Sprite.Icon | Mfd.Sprite.FillAmount | Mfd.Sprite.FillMethod

=============================================================================
INSTRUCTION REFERENCE (VizzyProgram methods)
=============================================================================

EVENTS (standalone top-level blocks)
  prog.on_start()
  prog.on_collision(part_var, other_var, vel_var, impulse_var)
  prog.on_explode(part_var)
  prog.on_docked(craft_a_var, craft_b_var)
  prog.on_enter_soi(planet_var)
  prog.receive_message(message_str, data_var)
    NOTE: receive_message returns a standalone Event block. Its handler
    instructions are siblings in root_instructions at a different X position.
    Use prog.thread_x to offset subsequent blocks into a new thread.

CONTROL FLOW
  prog.while_loop(condition)     -> add body to el.find("Instructions")
  prog.if_block(condition)       -> add body to el.find("Instructions")
  prog.else_if_block(condition)
  prog.else_block()
  prog.for_loop(var, start, end, step=1)
  prog.repeat_loop(count)
  prog.break_loop()
  prog.wait_seconds(duration)
  prog.wait_until(condition)

OUTPUT
  prog.display(text_el, duration=7)
  prog.flight_log(text_el, show_in_log=True)
  prog.local_log(text_el)
  prog.comment(text_str)

CRAFT CONTROL
  prog.activate_stage()
  prog.set_input(input_name, value)
    inputs: throttle | pitch | yaw | roll | brake | slider1 | slider2 |
            translateForward | translateRight | translateUp | translationMode
  prog.set_pitch(degrees)        set craft pitch (SetTargetHeading property="pitch")
  prog.set_heading(degrees)      set heading degrees (SetTargetHeading property="heading")
  prog.lock_heading(indicator)   indicator: Current | None | Prograde | Retrograde
  prog.lock_heading_vector(vec)
  prog.set_activation_group(group_num, state)
  prog.set_target(name_el)
  prog.set_time_mode(mode)       Normal | Paused | FastForward | SlowMotion |
                                 TimeWarp1 ... TimeWarp10
  prog.set_camera(property, value)
    properties: modeIndex | cameraIndex | zoom | xRot | yRot | tilt | targetOffset
  prog.set_part(part_id, property, value)
    properties: Part.SetActivated | Part.SetFocused | Part.SetName |
                Part.Explode | Part.SetFuelTransfer
  prog.switch_craft(craft_id)
  prog.play_beep(freq, volume, duration)

VARIABLES
  prog.set_var(name, value)
  prog.change_var(name, amount)
  prog.user_input(var_name, prompt_str)

LIST INSTRUCTIONS (mutate a list variable)
  prog.list_add(list_name, item)
  prog.list_remove(list_name, index)
  prog.list_clear(list_name)
  prog.list_insert(list_name, index, item)   *may not exist in all versions
  prog.list_set(list_name, index, item)      *may not exist in all versions
  prog.list_sort(list_name)                  *may not exist in all versions
  prog.list_reverse(list_name)               *may not exist in all versions
  prog.list_init_from_csv(list_name, csv)    set list from "a,b,c" string

BROADCASTING
  prog.broadcast(message, data, scope="local")
    scope: "local" (within vizzy) | "craft" | "nearby"

CUSTOM CALLS
  prog.call_instruction(name, *args)

MFD INSTRUCTIONS
  prog.mfd_create(widget_type, name)
    widget_type: Label | Ellipse | Rectangle | Line | Texture |
                 Navball | Map | RadialGauge
  prog.mfd_destroy(name)
  prog.mfd_destroy_all()
  prog.mfd_set(property, widget_name, value, style="set-mfd-widget")
  prog.mfd_set_text(widget_name, text)
  prog.mfd_set_color(widget_name, color)  color: "#RRGGBB" or vec expression
  prog.mfd_set_visible(widget_name, visible)
  prog.mfd_set_size(widget_name, size_vec)
  prog.mfd_set_position(widget_name, pos_vec)
  prog.mfd_set_autosize(widget_name, bool_val)
  prog.mfd_set_alignment(widget_name, alignment)
    alignment: Left | Center | Right | TopLeft | TopCenter | TopRight |
               BottomLeft | BottomCenter | BottomRight
  prog.mfd_set_icon(widget_name, icon_path)
  prog.mfd_event(widget_name, event_type, message, data)
    event_type: Click | Drag | PointerDown | PointerUp
  prog.mfd_front(widget_name, target_name)
  prog.mfd_back(widget_name, target_name)
  prog.mfd_texture_init(widget_name, width, height)
  prog.mfd_texture_pixel(widget_name, x, y, color_vec)

CUSTOM DEFINITIONS
  prog.add_custom_expression(name, params, return_el)
  prog.add_custom_instruction(name, params, body_els)

THREADING (multiple event handlers)
  prog.thread_x                  current X offset for new thread
  prog.next_thread()             advance to a new thread column (call before
                                 adding a new event handler's blocks)
"""

import xml.etree.ElementTree as ET
import os
import sys
from pathlib import Path

# UTF-8 stdout for Windows terminals
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

_HERE = Path(__file__).resolve().parent
if (_HERE / "FlightPrograms").exists() and (_HERE / "CraftDesigns").exists():
    USERDATA = _HERE
elif (_HERE.parent / "FlightPrograms").exists() and (_HERE.parent / "CraftDesigns").exists():
    USERDATA = _HERE.parent
else:
    USERDATA = _HERE

PROGRAMS_DIR = USERDATA / "FlightPrograms"
CRAFTS_DIR   = USERDATA / "CraftDesigns"


# ============================================================
#  EXPRESSION HELPERS
# ============================================================

class E:
    """Factory for Vizzy expression XML elements."""

    # -- constants -------------------------------------------
    @staticmethod
    def num(value):
        el = ET.Element("Constant")
        el.set("number", str(value))
        return el

    @staticmethod
    def text(value):
        el = ET.Element("Constant")
        el.set("text", str(value))
        return el

    @staticmethod
    def TRUE():
        el = ET.Element("Constant")
        el.set("style", "true")
        el.set("bool", "true")
        return el

    @staticmethod
    def FALSE():
        el = ET.Element("Constant")
        el.set("style", "false")
        el.set("bool", "false")
        return el

    # -- variables -------------------------------------------
    @staticmethod
    def var(name):
        el = ET.Element("Variable")
        el.set("list", "false")
        el.set("local", "false")
        el.set("variableName", name)
        return el

    @staticmethod
    def local_var(name):
        el = ET.Element("Variable")
        el.set("list", "false")
        el.set("local", "true")
        el.set("variableName", name)
        return el

    @staticmethod
    def list_var(name):
        el = ET.Element("Variable")
        el.set("list", "true")
        el.set("local", "false")
        el.set("variableName", name)
        return el

    # -- craft properties ------------------------------------
    @staticmethod
    def prop(property_name, style):
        """<CraftProperty property="..." style="..."/>"""
        el = ET.Element("CraftProperty")
        el.set("property", property_name)
        el.set("style", style)
        return el

    @staticmethod
    def prop_with(property_name, style, *children):
        """CraftProperty with child arguments (part ID, craft ID, planet name...)."""
        el = ET.Element("CraftProperty")
        el.set("property", property_name)
        el.set("style", style)
        for c in children:
            el.append(c)
        return el

    @staticmethod
    def part_id(name_expr):
        """Get part ID by name. name_expr: E.text("PartName") or expression."""
        el = ET.Element("CraftProperty")
        el.set("property", "Part.NameToID")
        el.set("style", "part-id")
        el.append(name_expr if isinstance(name_expr, ET.Element) else E.text(name_expr))
        return el

    @staticmethod
    def craft_id(name_expr):
        """Get craft ID by name."""
        el = ET.Element("CraftProperty")
        el.set("property", "Craft.NameToID")
        el.set("style", "craft-id")
        el.append(name_expr if isinstance(name_expr, ET.Element) else E.text(name_expr))
        return el

    @staticmethod
    def part_prop(property_name, part_id_expr):
        """Read a part property by part ID.
        property_name: Part.Mass | Part.Activated | Part.Temperature | etc.
        """
        el = ET.Element("CraftProperty")
        el.set("property", property_name)
        el.set("style", "part")
        el.append(part_id_expr)
        return el

    @staticmethod
    def craft_prop(property_name, craft_id_expr):
        """Read a craft property by craft ID.
        property_name: Craft.Position | Craft.Velocity | Craft.Altitude | etc.
        """
        el = ET.Element("CraftProperty")
        el.set("property", property_name)
        el.set("style", "craft")
        el.append(craft_id_expr)
        return el

    @staticmethod
    def planet_prop(op_name, planet_name_expr):
        """Read a planet property using the <Planet op="..."> tag.
        op_name (case-sensitive): radius | mass | atmosphereHeight | soiRadius |
          day | parent | velocity | period | periapsis | eccentricity |
          inclination | semiMajorAxis | crafts | craftIDs | solarPosition |
          childPlanets | rightAscension | meanAnomaly | meanMotion |
          periapsisArgument | lengthOfDay
        planet_name_expr: E.prop("Orbit.Planet","prop-name") or E.text("Droo")
        """
        el = ET.Element("Planet")
        el.set("op", op_name)
        el.set("style", "planet")
        el.append(planet_name_expr if isinstance(planet_name_expr, ET.Element)
                  else E.text(planet_name_expr))
        return el

    @staticmethod
    def activation_group(group_num):
        el = ET.Element("ActivationGroup")
        el.set("style", "activation-group")
        el.append(E.num(group_num) if not isinstance(group_num, ET.Element) else group_num)
        return el

    # -- arithmetic ------------------------------------------
    @staticmethod
    def _binop(op, style, a, b):
        el = ET.Element("BinaryOp")
        el.set("op", op)
        el.set("style", style)
        el.append(a)
        el.append(b)
        return el

    @staticmethod
    def add(a, b):   return E._binop("+",    "op-add",   a, b)
    @staticmethod
    def sub(a, b):   return E._binop("-",    "op-sub",   a, b)
    @staticmethod
    def mul(a, b):   return E._binop("*",    "op-mul",   a, b)
    @staticmethod
    def div(a, b):   return E._binop("/",    "op-div",   a, b)
    @staticmethod
    def pow(a, b):   return E._binop("^",    "op-exp",   a, b)
    @staticmethod
    def mod(a, b):   return E._binop("%",    "op-mod",   a, b)
    @staticmethod
    def rand(a, b):  return E._binop("rand", "op-rand",  a, b)
    @staticmethod
    def min2(a, b):  return E._binop("min",  "op-min",   a, b)
    @staticmethod
    def max2(a, b):  return E._binop("max",  "op-max",   a, b)
    @staticmethod
    def atan2(y, x): return E._binop("atan2","op-atan-2",y, x)

    @staticmethod
    def sum(*values):
        """Sum block: adds any number of values together.
        In the game editor this is a special block that extends to N inputs.
        """
        el = ET.Element("Sum")
        el.set("style", "sum")
        for v in values:
            el.append(v)
        return el

    # -- comparisons -----------------------------------------
    @staticmethod
    def _cmp(op, style, a, b):
        el = ET.Element("Comparison")
        el.set("op", op)
        el.set("style", style)
        el.append(a)
        el.append(b)
        return el

    @staticmethod
    def eq(a, b):  return E._cmp("=",  "op-eq",  a, b)
    @staticmethod
    def lt(a, b):  return E._cmp("l",  "op-lt",  a, b)
    @staticmethod
    def lte(a, b): return E._cmp("le", "op-lte", a, b)
    @staticmethod
    def gt(a, b):  return E._cmp("g",  "op-gt",  a, b)
    @staticmethod
    def gte(a, b): return E._cmp("ge", "op-gte", a, b)

    # -- boolean ---------------------------------------------
    @staticmethod
    def and_(a, b):
        el = ET.Element("BoolOp")
        el.set("op", "and")
        el.set("style", "op-and")
        el.append(a)
        el.append(b)
        return el

    @staticmethod
    def or_(a, b):
        el = ET.Element("BoolOp")
        el.set("op", "or")
        el.set("style", "op-or")
        el.append(a)
        el.append(b)
        return el

    @staticmethod
    def not_(a):
        el = ET.Element("Not")
        el.set("style", "op-not")
        el.append(a)
        return el

    # -- math functions --------------------------------------
    @staticmethod
    def math(fn, a):
        """Single-arg math.  fn: abs|floor|ceiling|round|sqrt|sin|cos|tan|
        asin|acos|atan|ln|log|deg2rad|rad2deg"""
        el = ET.Element("MathFunction")
        el.set("function", fn)
        el.set("style", "op-math")
        el.append(a)
        return el

    # -- ternary ---------------------------------------------
    @staticmethod
    def cond(condition, then_val, else_val):
        el = ET.Element("Conditional")
        el.set("style", "conditional")
        el.append(condition)
        el.append(then_val)
        el.append(else_val)
        return el

    # -- strings ---------------------------------------------
    @staticmethod
    def join(*parts):
        """Concatenate values. Auto-pads to at least 3 children (game requirement)."""
        el = ET.Element("StringOp")
        el.set("op", "join")
        el.set("style", "join")
        for p in parts:
            el.append(p)
        while sum(1 for _ in el) < 3:
            el.append(E.text(""))
        return el

    @staticmethod
    def length_str(s):
        el = ET.Element("StringOp")
        el.set("op", "length")
        el.set("style", "length")
        el.append(s)
        return el

    @staticmethod
    def letter(idx, s):
        el = ET.Element("StringOp")
        el.set("op", "letter")
        el.set("style", "letter")
        el.append(idx if isinstance(idx, ET.Element) else E.num(idx))
        el.append(s)
        return el

    @staticmethod
    def substr(from_idx, to_idx, s):
        el = ET.Element("StringOp")
        el.set("op", "substring")
        el.set("style", "substring")
        el.append(from_idx if isinstance(from_idx, ET.Element) else E.num(from_idx))
        el.append(to_idx   if isinstance(to_idx,   ET.Element) else E.num(to_idx))
        el.append(s)
        return el

    @staticmethod
    def contains(s, sub):
        el = ET.Element("StringOp")
        el.set("op", "contains")
        el.set("style", "contains")
        el.append(s)
        el.append(sub if isinstance(sub, ET.Element) else E.text(sub))
        return el

    @staticmethod
    def format(fmt_expr, *args):
        """C# String.Format. fmt_expr is a Constant or expression."""
        el = ET.Element("StringOp")
        el.set("op", "format")
        el.set("style", "format")
        el.append(fmt_expr if isinstance(fmt_expr, ET.Element) else E.text(fmt_expr))
        for a in args:
            el.append(a)
        return el

    @staticmethod
    def friendly(kind, val):
        """Human-readable. kind: "distance" | "speed" | etc."""
        el = ET.Element("StringOp")
        el.set("op", "friendly")
        el.set("style", "friendly")
        el.append(E.text(kind) if not isinstance(kind, ET.Element) else kind)
        el.append(val)
        return el

    @staticmethod
    def hex_color(hex_str):
        """Convert hex string to RGB vector. hex_str: e.g. "#FF0000" """
        el = ET.Element("StringOp")
        el.set("op", "hexcolor")
        el.set("style", "hex-color")
        el.append(E.text(hex_str) if not isinstance(hex_str, ET.Element) else hex_str)
        return el

    # -- vectors ---------------------------------------------
    @staticmethod
    def vec(x, y, z):
        el = ET.Element("Vector")
        el.set("style", "vec")
        el.append(x if isinstance(x, ET.Element) else E.num(x))
        el.append(y if isinstance(y, ET.Element) else E.num(y))
        el.append(z if isinstance(z, ET.Element) else E.num(z))
        return el

    @staticmethod
    def vec1(op, v):
        """Single-vec ops. op: x | y | z | length | norm"""
        el = ET.Element("VectorOp")
        el.set("op", op)
        el.set("style", "vec-op-1")
        el.append(v)
        return el

    @staticmethod
    def vec2(op, v1, v2):
        """Two-vec ops. op: dot|cross|dist|angle|min|max|project|scale|clamp"""
        el = ET.Element("VectorOp")
        el.set("op", op)
        el.set("style", "vec-op-2")
        el.append(v1)
        el.append(v2)
        return el

    # -- list read-only expressions --------------------------
    @staticmethod
    def list_get(list_expr, index_expr):
        """item (index) in (list)  -- 1-based index, returns item value"""
        el = ET.Element("ListOp")
        el.set("op", "get")
        el.set("style", "list-get")
        el.append(list_expr if isinstance(list_expr, ET.Element) else E.list_var(list_expr))
        el.append(index_expr if isinstance(index_expr, ET.Element) else E.num(index_expr))
        return el

    @staticmethod
    def list_length(list_expr):
        """length of (list)"""
        el = ET.Element("ListOp")
        el.set("op", "length")
        el.set("style", "list-length")
        el.append(list_expr if isinstance(list_expr, ET.Element) else E.list_var(list_expr))
        return el

    @staticmethod
    def list_index(list_expr, item_expr):
        """index of (item) in (list) -- returns 1-based position or -1"""
        el = ET.Element("ListOp")
        el.set("op", "index")
        el.set("style", "list-index")
        el.append(list_expr if isinstance(list_expr, ET.Element) else E.list_var(list_expr))
        el.append(item_expr if isinstance(item_expr, ET.Element) else E.text(item_expr))
        return el

    @staticmethod
    def list_create(csv_string):
        """Create a list from a comma-separated string (expression, not instruction).
        Use in list_init_from_csv() to set a list variable.
        """
        el = ET.Element("ListOp")
        el.set("op", "create")
        el.set("style", "list-create")
        el.append(E.text(csv_string) if not isinstance(csv_string, ET.Element) else csv_string)
        return el

    # -- planet / coordinate expressions ---------------------
    @staticmethod
    def to_lat_long_agl(pci_vec):
        """Convert PCI vector to lat/long/AGL vector."""
        el = ET.Element("Planet")
        el.set("op", "toLatLongAgl")
        el.set("style", "planet-to-lat-long-agl")
        el.append(pci_vec)
        return el

    @staticmethod
    def to_lat_long_asl(pci_vec):
        """Convert PCI vector to lat/long/ASL vector."""
        el = ET.Element("Planet")
        el.set("op", "toLatLongAsl")
        el.set("style", "planet-to-lat-long-asl")
        el.append(pci_vec)
        return el

    @staticmethod
    def to_position(lat_long_vec):
        """Convert lat/long/AGL vector to PCI position vector."""
        el = ET.Element("Planet")
        el.set("op", "toPosition")
        el.set("style", "planet-to-position")
        el.append(lat_long_vec)
        return el

    @staticmethod
    def planet_day(planet_expr):
        """Length of day for a planet."""
        el = ET.Element("Planet")
        el.set("op", "day")
        el.set("style", "planet")
        el.append(planet_expr if isinstance(planet_expr, ET.Element)
                  else E.text(planet_expr))
        return el

    @staticmethod
    def terrain_height(lat_long_expr):
        """Terrain height at lat/long."""
        el = ET.Element("CraftProperty")
        el.set("property", "Terrain.Height")
        el.set("style", "terrain-query")
        el.append(lat_long_expr)
        return el

    @staticmethod
    def terrain_color(lat_long_expr):
        """Terrain color at lat/long."""
        el = ET.Element("CraftProperty")
        el.set("property", "Terrain.Color")
        el.set("style", "terrain-query")
        el.append(lat_long_expr)
        return el

    @staticmethod
    def cast_ray(from_vec, dir_vec):
        """Cast a ray from PCI position in direction."""
        el = ET.Element("CraftProperty")
        el.set("property", "Ray.Cast")
        el.set("style", "cast-ray")
        el.append(from_vec)
        el.append(dir_vec)
        return el

    # -- special ---------------------------------------------
    @staticmethod
    def funk(expr_str):
        """fUNk() - evaluate inline expression string at runtime."""
        el = ET.Element("EvaluateExpression")
        el.set("style", "evaluate-expression")
        el.append(E.text(expr_str))
        return el

    @staticmethod
    def call_expr(name, *args):
        """Call a custom expression by name."""
        el = ET.Element("CallCustomExpression")
        el.set("call", name)
        el.set("style", "call-custom-expression")
        for a in args:
            el.append(a)
        return el

    @staticmethod
    def note_frequency(note, octave):
        """Frequency of a musical note. note: "C#", octave: 4"""
        el = ET.Element("CraftProperty")
        el.set("property", "Sound.Frequency")
        el.set("style", "note-frequency")
        el.append(E.text(note) if not isinstance(note, ET.Element) else note)
        el.append(E.text(str(octave)) if not isinstance(octave, ET.Element) else octave)
        return el


# ============================================================
#  PROGRAM BUILDER
# ============================================================

class VizzyProgram:
    """
    Build a complete Vizzy program and save it as XML.

    Multi-thread programs (multiple event handlers):
      prog = VizzyProgram("My Program")
      instr = prog.root_instructions

      # Thread 1 - main loop
      instr.append(prog.on_start())
      instr.append(...)

      # Thread 2 - message receiver (at different canvas X)
      prog.next_thread()
      instr.append(prog.receive_message("myMsg", "data"))
      instr.append(...)   # handler blocks run after the receive event
    """

    def __init__(self, name: str, requires_mfd: bool = False):
        self.name = name
        self.requires_mfd = requires_mfd
        self._id = 0
        self._variables: list = []
        self.root_instructions: list = []
        self._expressions: list = []
        self._custom_instruction_threads: list = []
        self._thread_x = -10    # canvas X offset for current thread
        self._thread_y = -20    # canvas Y for next top-level block in thread
        self._thread_col_width = 400  # horizontal spacing between threads

    # -- internal helpers ------------------------------------
    def _next_id(self) -> int:
        i = self._id
        self._id += 1
        return i

    def _next_pos(self) -> str:
        """Return canvas position string for a new top-level block."""
        pos = f"{self._thread_x},{self._thread_y}"
        self._thread_y -= 150
        return pos

    def next_thread(self):
        """Advance to a new thread column (for a new event handler)."""
        self._thread_x += self._thread_col_width
        self._thread_y = -20

    def _instr(self, tag: str, style: str, **attrs) -> ET.Element:
        """Create a basic instruction element (id + style + extra attrs)."""
        el = ET.Element(tag)
        for k, v in attrs.items():
            el.set(k, v)
        el.set("id", str(self._next_id()))
        el.set("style", style)
        return el

    def _instr_pos(self, tag: str, style: str, **attrs) -> ET.Element:
        """Instruction with pos attribute (for top-level event-like blocks)."""
        el = self._instr(tag, style, **attrs)
        el.set("pos", self._next_pos())
        return el

    # -- variable declarations -------------------------------
    def var(self, name: str, initial=0, is_list: bool = False):
        """Declare a program variable. Chainable: prog.var("a").var("b")"""
        el = ET.Element("Variable")
        el.set("name", name)
        if is_list:
            ET.SubElement(el, "Items")
        else:
            el.set("number", str(initial))
        self._variables.append(el)
        return self

    # -- events (standalone top-level trigger blocks) --------
    def on_start(self) -> ET.Element:
        return self._instr_pos("Event", "flight-start", event="FlightStart")

    def on_collision(self, part_var="part", other_var="other",
                     vel_var="velocity", impulse_var="impulse") -> ET.Element:
        return self._instr_pos("Event", "part-collide", event="PartCollide",
                               partVar=part_var, otherVar=other_var,
                               velocityVar=vel_var, impulseVar=impulse_var)

    def on_explode(self, part_var="part") -> ET.Element:
        return self._instr_pos("Event", "part-explode",
                               event="PartExplode", partVar=part_var)

    def on_docked(self, craft_a_var="craftA", craft_b_var="craftB") -> ET.Element:
        return self._instr_pos("Event", "docked", event="Docked",
                               craftAVar=craft_a_var, craftBVar=craft_b_var)

    def on_enter_soi(self, planet_var="planet") -> ET.Element:
        return self._instr_pos("Event", "change-soi",
                               event="ChangeSoi", planetVar=planet_var)

    def receive_message(self, message: str, data_var: str = "data") -> ET.Element:
        """Receive message event. This is a STANDALONE block (not a container).
        Place handler instructions as siblings AFTER this block.
        The data variable receives the broadcast payload.
        """
        el = ET.Element("Event")
        el.set("event", "ReceiveMessage")
        el.set("id", str(self._next_id()))
        el.set("style", "receive-msg")
        el.set("pos", self._next_pos())
        c = ET.SubElement(el, "Constant")
        c.set("canReplace", "false")
        c.set("text", message)
        return el

    # -- control flow ----------------------------------------
    def while_loop(self, condition: ET.Element) -> ET.Element:
        """while (condition). Add body to el.find("Instructions")."""
        el = self._instr("While", "while")
        el.append(condition)
        ET.SubElement(el, "Instructions")
        return el

    def if_block(self, condition: ET.Element) -> ET.Element:
        el = self._instr("If", "if")
        el.append(condition)
        ET.SubElement(el, "Instructions")
        return el

    def else_if_block(self, condition: ET.Element) -> ET.Element:
        el = self._instr("ElseIf", "else-if")
        el.append(condition)
        ET.SubElement(el, "Instructions")
        return el

    def else_block(self) -> ET.Element:
        el = self._instr("Else", "else")
        ET.SubElement(el, "Instructions")
        return el

    def for_loop(self, var_name: str, start, end, step=1) -> ET.Element:
        """for (var) from (start) to (end) by (step).
        Loop condition: var < end. Step can be negative for countdown.
        """
        el = self._instr("For", "for", var=var_name)
        el.append(start if isinstance(start, ET.Element) else E.num(start))
        el.append(end   if isinstance(end,   ET.Element) else E.num(end))
        el.append(step  if isinstance(step,  ET.Element) else E.num(step))
        ET.SubElement(el, "Instructions")
        return el

    def repeat_loop(self, count) -> ET.Element:
        el = self._instr("Repeat", "repeat")
        el.append(count if isinstance(count, ET.Element) else E.num(count))
        ET.SubElement(el, "Instructions")
        return el

    def break_loop(self) -> ET.Element:
        return self._instr("Break", "break")

    def wait_seconds(self, duration) -> ET.Element:
        el = self._instr("WaitSeconds", "wait-seconds")
        el.append(duration if isinstance(duration, ET.Element) else E.num(duration))
        return el

    def wait_until(self, condition: ET.Element) -> ET.Element:
        el = self._instr("WaitUntil", "wait-until")
        el.append(condition)
        return el

    # -- output / logging ------------------------------------
    def display(self, text_el, duration=7) -> ET.Element:
        el = self._instr("DisplayMessage", "display")
        el.append(text_el if isinstance(text_el, ET.Element) else E.text(text_el))
        el.append(E.num(duration))
        return el

    def flight_log(self, text_el, show_in_log: bool = True) -> ET.Element:
        """Write to flight log. Real tag is LogFlight, not FlightLog."""
        el = self._instr("LogFlight", "flightlog")
        el.append(text_el if isinstance(text_el, ET.Element) else E.text(text_el))
        el.append(E.TRUE() if show_in_log else E.FALSE())
        return el

    def local_log(self, text_el) -> ET.Element:
        """Write to local (part) log."""
        el = self._instr("LogFlight", "flightlog")
        el.append(text_el if isinstance(text_el, ET.Element) else E.text(text_el))
        el.append(E.FALSE())
        return el

    def comment(self, text: str) -> ET.Element:
        el = ET.Element("Comment")
        el.set("id", str(self._next_id()))
        el.set("style", "comment")
        c = ET.SubElement(el, "Constant")
        c.set("style", "comment-text")
        c.set("canReplace", "false")
        c.set("text", text)
        return el

    # -- craft instructions ----------------------------------
    def activate_stage(self) -> ET.Element:
        return self._instr("ActivateStage", "activate-stage")

    def set_input(self, input_name: str, value) -> ET.Element:
        """Set a pilot input channel.
        input_name: throttle | pitch | yaw | roll | brake |
                    slider1 | slider2 | translateForward |
                    translateRight | translateUp | translationMode
        """
        el = self._instr("SetInput", "set-input", input=input_name)
        el.append(value if isinstance(value, ET.Element) else E.num(value))
        return el

    def set_pitch(self, degrees) -> ET.Element:
        """Set craft pitch in degrees. (SetTargetHeading property="pitch")"""
        el = self._instr("SetTargetHeading", "set-heading", property="pitch")
        el.append(degrees if isinstance(degrees, ET.Element) else E.num(degrees))
        return el

    def set_heading(self, degrees) -> ET.Element:
        """Set craft heading in degrees. (SetTargetHeading property="heading")"""
        el = self._instr("SetTargetHeading", "set-heading", property="heading")
        el.append(degrees if isinstance(degrees, ET.Element) else E.num(degrees))
        return el

    def lock_heading(self, indicator_type: str) -> ET.Element:
        """Lock heading on preset direction.
        indicator_type: Current | None | Prograde | Retrograde
        """
        return self._instr("LockNavSphere", "lock-nav-sphere",
                           indicatorType=indicator_type)

    def lock_heading_vector(self, vector_el: ET.Element) -> ET.Element:
        el = self._instr("LockNavSphere", "lock-nav-sphere-vector",
                         indicatorType="Vector")
        el.append(vector_el)
        return el

    def set_activation_group(self, group_num, state) -> ET.Element:
        el = self._instr("SetActivationGroup", "set-ag")
        el.append(E.num(group_num))
        el.append(state if isinstance(state, ET.Element)
                  else (E.TRUE() if state else E.FALSE()))
        return el

    def set_target(self, name_el) -> ET.Element:
        el = self._instr("SetTarget", "set-target")
        el.append(name_el if isinstance(name_el, ET.Element) else E.text(name_el))
        return el

    def set_time_mode(self, mode: str) -> ET.Element:
        """mode: Normal | Paused | FastForward | SlowMotion | TimeWarp1..TimeWarp10"""
        return self._instr("SetTimeMode", "set-time-mode", mode=mode)

    def set_camera(self, property_name: str, value) -> ET.Element:
        """property: modeIndex | cameraIndex | zoom | xRot | yRot | tilt | targetOffset"""
        el = self._instr("SetCameraProperty", "set-camera", property=property_name)
        el.append(value if isinstance(value, ET.Element) else E.num(value))
        return el

    def set_part(self, part_id_expr, property_name: str, value) -> ET.Element:
        """Set a part property.
        property_name: Part.SetActivated | Part.SetFocused | Part.SetName |
                       Part.Explode | Part.SetFuelTransfer
        """
        el = self._instr("SetCraftProperty", "set-part", property=property_name)
        el.append(part_id_expr if isinstance(part_id_expr, ET.Element)
                  else E.num(part_id_expr))
        el.append(value if isinstance(value, ET.Element) else E.num(value))
        return el

    def switch_craft(self, craft_id_expr) -> ET.Element:
        el = self._instr("SetCraftProperty", "switch-craft",
                         property="Craft.Switch")
        el.append(craft_id_expr if isinstance(craft_id_expr, ET.Element)
                  else E.num(craft_id_expr))
        return el

    def play_beep(self, freq, volume, duration) -> ET.Element:
        el = self._instr("SetCraftProperty", "play-beep",
                         property="Sound.Beep")
        el.append(freq     if isinstance(freq,     ET.Element) else E.num(freq))
        el.append(volume   if isinstance(volume,   ET.Element) else E.num(volume))
        el.append(duration if isinstance(duration, ET.Element) else E.num(duration))
        return el

    # -- variables -------------------------------------------
    def set_var(self, name: str, value) -> ET.Element:
        el = self._instr("SetVariable", "set-variable")
        ref = ET.Element("Variable")
        ref.set("list", "false")
        ref.set("local", "false")
        ref.set("variableName", name)
        el.append(ref)
        el.append(value if isinstance(value, ET.Element) else E.num(value))
        return el

    def change_var(self, name: str, amount) -> ET.Element:
        el = self._instr("ChangeVariable", "change-variable")
        ref = ET.Element("Variable")
        ref.set("list", "false")
        ref.set("local", "false")
        ref.set("variableName", name)
        el.append(ref)
        el.append(amount if isinstance(amount, ET.Element) else E.num(amount))
        return el

    def user_input(self, var_name: str, prompt: str) -> ET.Element:
        """Prompt player for input, store in variable."""
        el = self._instr("UserInput", "user-input")
        ref = ET.Element("Variable")
        ref.set("list", "false")
        ref.set("local", "false")
        ref.set("variableName", var_name)
        el.append(ref)
        el.append(E.text(prompt))
        return el

    # -- list instructions (mutate) --------------------------
    def list_add(self, list_name: str, item) -> ET.Element:
        """add (item) to (list)"""
        el = self._instr("SetList", "list-add", op="add")
        el.append(E.list_var(list_name))
        el.append(item if isinstance(item, ET.Element) else E.text(item))
        return el

    def list_remove(self, list_name: str, index) -> ET.Element:
        """remove (index) from (list)"""
        el = self._instr("SetList", "list-remove", op="remove")
        el.append(E.list_var(list_name))
        el.append(index if isinstance(index, ET.Element) else E.num(index))
        return el

    def list_clear(self, list_name: str) -> ET.Element:
        """remove all from (list)"""
        el = self._instr("SetList", "list-clear", op="clear")
        el.append(E.list_var(list_name))
        return el

    def list_insert(self, list_name: str, index, item) -> ET.Element:
        """insert (item) at (index) in (list)"""
        el = self._instr("SetList", "list-insert", op="insert")
        el.append(E.list_var(list_name))
        el.append(index if isinstance(index, ET.Element) else E.num(index))
        el.append(item  if isinstance(item,  ET.Element) else E.text(item))
        return el

    def list_set(self, list_name: str, index, item) -> ET.Element:
        """set (index) in (list) to (item)"""
        el = self._instr("SetList", "list-set", op="set")
        el.append(E.list_var(list_name))
        el.append(index if isinstance(index, ET.Element) else E.num(index))
        el.append(item  if isinstance(item,  ET.Element) else E.text(item))
        return el

    def list_sort(self, list_name: str) -> ET.Element:
        el = self._instr("SetList", "list-sort", op="sort")
        el.append(E.list_var(list_name))
        return el

    def list_reverse(self, list_name: str) -> ET.Element:
        el = self._instr("SetList", "list-reverse", op="reverse")
        el.append(E.list_var(list_name))
        return el

    def list_init_from_csv(self, list_name: str, csv_string: str) -> ET.Element:
        """Set a list variable from a comma-separated string.
        Example: prog.list_init_from_csv("altitudes", "0,5000,10000,50000")
        """
        el = self._instr("SetVariable", "list-init")
        el.append(E.list_var(list_name))
        el.append(E.list_create(csv_string))
        return el

    # -- broadcasting ----------------------------------------
    def broadcast(self, message: str, data, scope: str = "local") -> ET.Element:
        """Broadcast a message with data.
        scope: "local" (within vizzy) | "craft" (all on craft) | "nearby" (all crafts)
        """
        style_map = {
            "local":  "broadcast-msg",
            "craft":  "broadcast-msg-craft",
            "nearby": "broadcast-msg-nearby",
        }
        el = self._instr("BroadcastMessage",
                         style_map.get(scope, "broadcast-msg"),
                         message=message)
        if scope == "local":
            el.set("global", "false")
            el.set("local", "true")
        elif scope == "craft":
            el.set("global", "false")
            el.set("local", "false")
        else:
            el.set("global", "true")
            el.set("local", "false")
        el.append(data if isinstance(data, ET.Element) else E.num(data))
        return el

    # -- custom calls ----------------------------------------
    def call_instruction(self, name: str, *args) -> ET.Element:
        el = self._instr("CallCustomInstruction", "call-custom-instruction",
                         call=name)
        for a in args:
            el.append(a)
        return el

    # -- MfD instructions ------------------------------------
    def mfd_create(self, widget_type: str, name: str) -> ET.Element:
        """Create an MfD widget.
        widget_type: Label | Ellipse | Rectangle | Line | Texture |
                     Navball | Map | RadialGauge
        """
        el = self._instr("SetCraftProperty", "create-mfd-widget",
                         property=f"Mfd.Create.{widget_type}")
        el.append(E.text(name))
        return el

    def mfd_destroy(self, name: str) -> ET.Element:
        el = self._instr("SetCraftProperty", "destroy-mfd-widget",
                         property="Mfd.Destroy")
        el.append(E.text(name))
        return el

    def mfd_destroy_all(self) -> ET.Element:
        return self._instr("SetCraftProperty", "destroy-mfd-widget",
                           property="Mfd.DestroyAll")

    def mfd_set(self, property_name: str, widget_name: str,
                value, style: str = "set-mfd-widget") -> ET.Element:
        el = self._instr("SetCraftProperty", style, property=property_name)
        el.append(E.text(widget_name))
        el.append(value if isinstance(value, ET.Element) else E.text(value))
        return el

    def mfd_set_text(self, widget_name: str, text) -> ET.Element:
        return self.mfd_set("Mfd.Label.SetText", widget_name,
                            text if isinstance(text, ET.Element) else E.text(text),
                            style="set-mfd-label")

    def mfd_set_color(self, widget_name: str, color) -> ET.Element:
        """color: hex string "#RRGGBB" or an RGB vector expression."""
        return self.mfd_set("Mfd.SetColor", widget_name,
                            E.text(color) if isinstance(color, str) else color)

    def mfd_set_visible(self, widget_name: str, visible) -> ET.Element:
        return self.mfd_set(
            "Mfd.SetVisible", widget_name,
            E.TRUE()  if visible is True
            else E.FALSE() if visible is False
            else visible)

    def mfd_set_size(self, widget_name: str, size_vec) -> ET.Element:
        return self.mfd_set("Mfd.SetSize", widget_name, size_vec)

    def mfd_set_position(self, widget_name: str, pos_vec) -> ET.Element:
        return self.mfd_set("Mfd.SetPosition", widget_name, pos_vec)

    def mfd_set_autosize(self, widget_name: str, bool_val) -> ET.Element:
        return self.mfd_set("Mfd.Label.SetAutoSize", widget_name,
                            bool_val if isinstance(bool_val, ET.Element)
                            else (E.TRUE() if bool_val else E.FALSE()),
                            style="set-mfd-label")

    def mfd_set_alignment(self, widget_name: str, alignment: str) -> ET.Element:
        """alignment: Left | Center | Right | TopLeft | TopCenter | TopRight |
        BottomLeft | BottomCenter | BottomRight"""
        return self.mfd_set(f"Mfd.Label.SetAlignment.{alignment}", widget_name,
                            E.text(""),  # dummy required child
                            style="set-mfd-alignment")

    def mfd_set_icon(self, widget_name: str, icon_path: str) -> ET.Element:
        return self.mfd_set("Mfd.Sprite.SetIcon", widget_name,
                            E.text(icon_path), style="set-mfd-sprite")

    def mfd_event(self, widget_name: str, event_type: str,
                  message: str, data) -> ET.Element:
        """Set a widget event broadcast.
        event_type: Click | Drag | PointerDown | PointerUp
        """
        el = self._instr("SetCraftProperty", "set-mfd-event",
                         property="Mfd.Event.SetBroadcast", eventType=event_type)
        el.append(E.text(widget_name))
        el.append(E.text(message))
        el.append(data if isinstance(data, ET.Element) else E.text(data))
        return el

    def mfd_front(self, widget_name: str, target_name: str) -> ET.Element:
        el = self._instr("SetCraftProperty", "set-mfd-order-front",
                         property="Mfd.BringToFront")
        el.append(E.text(widget_name))
        el.append(E.text(target_name))
        return el

    def mfd_back(self, widget_name: str, target_name: str) -> ET.Element:
        el = self._instr("SetCraftProperty", "set-mfd-order-back",
                         property="Mfd.SendToBack")
        el.append(E.text(widget_name))
        el.append(E.text(target_name))
        return el

    def mfd_texture_init(self, widget_name: str, width, height) -> ET.Element:
        el = self._instr("SetCraftProperty", "set-mfd-texture-initialize",
                         property="Mfd.Texture.Initialize")
        el.append(E.text(widget_name))
        el.append(width  if isinstance(width,  ET.Element) else E.num(width))
        el.append(height if isinstance(height, ET.Element) else E.num(height))
        return el

    def mfd_texture_pixel(self, widget_name: str, x, y, color_vec) -> ET.Element:
        el = self._instr("SetCraftProperty", "set-mfd-texture-setpixel",
                         property="Mfd.Texture.SetPixel")
        el.append(E.text(widget_name))
        el.append(x if isinstance(x, ET.Element) else E.num(x))
        el.append(y if isinstance(y, ET.Element) else E.num(y))
        el.append(color_vec)
        return el

    # -- custom expression / instruction definitions ---------
    def add_custom_expression(self, name: str, params: list,
                              return_el: ET.Element) -> ET.Element:
        """Define a custom expression (returns a value).
        params: list of parameter name strings.
        return_el: the expression tree that computes the return value.
        """
        el = ET.Element("CustomExpression")
        el.set("name", name)
        el.set("style", "custom-expression")
        el.set("id", str(self._next_id()))
        el.set("pos", "400,-20")
        params_str = " ".join(f"|{p}|" for p in params)
        args_str   = " ".join(f"({i})" for i in range(len(params)))
        el.set("format",     f"{name} {params_str}  return (0)")
        el.set("callFormat", f"{name} {args_str} ")
        el.append(return_el)
        self._expressions.append(el)
        return el

    def add_custom_instruction(self, name: str, params: list,
                               body_els: list) -> ET.Element:
        """Define a custom instruction (runs code, no return value).
        params: list of parameter name strings.
        body_els: list of instruction ET.Elements that form the body.
        """
        el = ET.Element("CustomInstruction")
        el.set("name", name)
        el.set("style", "custom-instruction")
        el.set("id", str(self._next_id()))
        el.set("pos", "400,-20")
        params_str = " ".join(f"|{p}|" for p in params)
        args_str   = " ".join(f"({i})" for i in range(len(params)))
        el.set("format",     f"{name} {params_str}  ")
        el.set("callFormat", f"{name} {args_str} ")
        self._custom_instruction_threads.append([el, *body_els])
        return el

    # -- serialisation ---------------------------------------
    def to_element(self) -> ET.Element:
        prog = ET.Element("Program")
        prog.set("name", self.name)
        if self.requires_mfd:
            prog.set("requiresMfd", "true")

        vars_el = ET.SubElement(prog, "Variables")
        for v in self._variables:
            vars_el.append(v)

        instr_el = ET.SubElement(prog, "Instructions")
        for b in self.root_instructions:
            instr_el.append(b)

        for thread in self._custom_instruction_threads:
            thread_el = ET.SubElement(prog, "Instructions")
            for b in thread:
                thread_el.append(b)

        expr_el = ET.SubElement(prog, "Expressions")
        for ex in self._expressions:
            expr_el.append(ex)

        return prog

    def to_xml(self) -> str:
        return _pretty_xml(self.to_element())

    def save(self, filename: str = None) -> Path:
        """Save to FlightPrograms/. filename defaults to '<name>.xml'."""
        if filename is None:
            filename = self.name + ".xml"
        path = PROGRAMS_DIR / filename
        path.write_text(self.to_xml(), encoding="utf-8-sig")
        print(f"Saved: {path}")
        return path


# ============================================================
#  XML PRETTY-PRINTER
# ============================================================

def _indent(el, level=0):
    i = "\n" + "  " * level
    if len(el):
        if not el.text or not el.text.strip():
            el.text = i + "  "
        if not el.tail or not el.tail.strip():
            el.tail = i
        last = None
        for child in el:
            _indent(child, level + 1)
            last = child
        if last is not None and (not last.tail or not last.tail.strip()):
            last.tail = i
    else:
        if level and (not el.tail or not el.tail.strip()):
            el.tail = i


def _pretty_xml(prog_element: ET.Element) -> str:
    _indent(prog_element)
    raw = ET.tostring(prog_element, encoding="unicode")
    return '<?xml version="1.0" encoding="utf-8"?>\n' + raw + "\n"


# ============================================================
#  READER / DISPLAY
# ============================================================

def _resolve_path(name_or_path: str) -> Path:
    p = Path(name_or_path)
    if p.exists():
        return p
    candidates = list(PROGRAMS_DIR.glob(f"*{name_or_path}*"))
    if candidates:
        return candidates[0]
    raise FileNotFoundError(f"Program not found: {name_or_path!r}")


_BLOCK_LABELS = {
    "flight-start":               ">> ON START",
    "receive-msg":                "[RECEIVE]",
    "part-collide":               "[ON COLLISION]",
    "part-explode":               "[ON EXPLODE]",
    "docked":                     "[ON DOCKED]",
    "change-soi":                 "[ON ENTER SOI]",
    "while":                      "WHILE",
    "if":                         "IF",
    "else-if":                    "ELSE IF",
    "else":                       "ELSE",
    "for":                        "FOR",
    "repeat":                     "REPEAT",
    "break":                      "BREAK",
    "wait-seconds":               "WAIT SECONDS",
    "wait-until":                 "WAIT UNTIL",
    "comment":                    "#",
    "activate-stage":             "ACTIVATE STAGE",
    "set-input":                  "SET INPUT",
    "set-variable":               "SET VAR",
    "list-init":                  "LIST INIT",
    "change-variable":            "CHANGE VAR",
    "set-ag":                     "SET AG",
    "set-heading":                "SET HEADING",
    "lock-nav-sphere":            "LOCK HEADING",
    "lock-nav-sphere-vector":     "LOCK HEADING (VEC)",
    "set-target":                 "SET TARGET",
    "set-part":                   "SET PART",
    "set-time-mode":              "SET TIME MODE",
    "set-camera":                 "SET CAMERA",
    "user-input":                 "USER INPUT",
    "display":                    "DISPLAY",
    "local-log":                  "LOCAL LOG",
    "flightlog":                  "FLIGHT LOG",
    "play-beep":                  "BEEP",
    "broadcast-msg":              "BROADCAST (local)",
    "broadcast-msg-craft":        "BROADCAST (craft)",
    "broadcast-msg-nearby":       "BROADCAST (nearby)",
    "call-custom-instruction":    "CALL",
    "create-mfd-widget":          "MFD CREATE",
    "destroy-mfd-widget":         "MFD DESTROY",
    "set-mfd-widget":             "MFD SET",
    "set-mfd-label":              "MFD LABEL",
    "set-mfd-alignment":          "MFD ALIGN",
    "set-mfd-sprite":             "MFD SPRITE",
    "set-mfd-gauge":              "MFD GAUGE",
    "set-mfd-texture-initialize": "MFD TEXTURE INIT",
    "set-mfd-texture-setpixel":   "MFD TEXTURE PIXEL",
    "set-mfd-map":                "MFD MAP",
    "set-mfd-event":              "MFD EVENT",
    "set-mfd-order-front":        "MFD FRONT",
    "set-mfd-order-back":         "MFD BACK",
    "custom-expression":          "DEF EXPR",
    "custom-instruction":         "DEF INSTR",
    "switch-craft":               "SWITCH CRAFT",
    "list-add":                   "LIST ADD",
    "list-remove":                "LIST REMOVE",
    "list-clear":                 "LIST CLEAR",
    "list-insert":                "LIST INSERT",
    "list-set":                   "LIST SET",
    "list-sort":                  "LIST SORT",
    "list-reverse":               "LIST REVERSE",
}


def _el_summary(el: ET.Element, depth: int = 0) -> str:
    style = el.get("style", el.tag)
    label = _BLOCK_LABELS.get(style, style.upper())
    attrs = ""
    for attr in ("event", "input", "var", "message", "property",
                 "indicatorType", "mode", "op", "function",
                 "variableName", "call", "eventType"):
        v = el.get(attr)
        if v:
            attrs += f" [{attr}={v}]"
    # Special: show comment text
    if style == "comment":
        c = el.find("Constant")
        if c is not None:
            attrs = f"  {c.get('text', '')}"
    return "  " * depth + label + attrs


def _print_instructions(instr_el: ET.Element, depth: int = 0):
    if instr_el is None:
        return
    for child in instr_el:
        if child.tag == "Instructions":
            continue
        print(_el_summary(child, depth))
        inner = child.find("Instructions")
        if inner is not None:
            _print_instructions(inner, depth + 1)


def display_program(path: Path):
    tree = ET.parse(path)
    root = tree.getroot()
    sep = "=" * 60
    print(f"\n{sep}")
    print(f"  PROGRAM : {root.get('name', '?')}")
    if root.get("requiresMfd") == "true":
        print("  [Requires MfD]")
    print(f"  File    : {path.name}")
    print(sep)

    vars_el = root.find("Variables")
    if vars_el is not None and len(vars_el):
        print("\n-- VARIABLES --")
        for v in vars_el:
            if v.find("Items") is not None:
                print(f"  {v.get('name')} (list)")
            else:
                print(f"  {v.get('name')} = {v.get('number', 0)}")

    instr_el = root.find("Instructions")
    if instr_el is not None:
        block_count = sum(1 for _ in root.iter() if _.get("id") is not None)
        print(f"\n-- INSTRUCTIONS ({block_count} blocks) --")
        _print_instructions(instr_el)

    expr_el = root.find("Expressions")
    if expr_el is not None and len(expr_el):
        print("\n-- CUSTOM EXPRESSIONS / INSTRUCTIONS --")
        for ex in expr_el:
            st = ex.get("style", "")
            if st in ("custom-expression", "custom-instruction"):
                label = "EXPR" if st == "custom-expression" else "INSTR"
                fmt = ex.get("callFormat", ex.get("name", "?"))
                print(f"  [{label}] {fmt}")
    print()


# ============================================================
#  VALIDATOR
# ============================================================

def validate_program(path: Path) -> bool:
    try:
        tree = ET.parse(path)
        root = tree.getroot()
    except ET.ParseError as e:
        print(f"FAIL  XML parse error: {e}")
        return False

    errors = []
    warnings = []

    if root.tag != "Program":
        errors.append(f"Root must be <Program>, got <{root.tag}>")
    if root.find("Variables") is None:
        errors.append("Missing <Variables>")
    if root.find("Instructions") is None:
        errors.append("Missing <Instructions>")
    # Expressions can be missing (some real files omit it)
    if root.find("Expressions") is None:
        warnings.append("Missing <Expressions> (optional but recommended)")

    # Duplicate ID check
    all_ids = [int(el.get("id")) for el in root.iter() if el.get("id") is not None]
    dupes = {i for i in all_ids if all_ids.count(i) > 1}
    if dupes:
        errors.append(f"Duplicate block IDs: {sorted(dupes)}")

    # Validate CraftProperty style+property combinations.
    # Built from all real game-created files — only flag properties known to be INVALID
    # (i.e. that cause "Could not find property X" in CraftPropertyExpression.OnDeserialized).
    # Known invalid properties confirmed from game log:
    _invalid_props = {
        # "Name.Planet" does NOT exist — use "Orbit.Planet" with prop-name instead
        "prop-name": {"Name.Planet", "Name.Craft"},
    }
    for el in root.iter("CraftProperty"):
        style = el.get("style", "")
        prop = el.get("property", "")
        if style in _invalid_props and prop in _invalid_props[style]:
            errors.append(
                f"Invalid CraftProperty: property={prop!r} does not exist. "
                f"style={style!r} — did you mean 'Orbit.Planet'?"
            )

    # Only instruction-level blocks (direct children of <Instructions> containers)
    # should have ids. Expression nodes (operators, conditions) correctly omit ids.
    instruction_tags = {
        "Event", "WaitSeconds", "WaitUntil", "While", "If", "ElseIf", "Else",
        "For", "Repeat", "Break", "DisplayMessage", "LogFlight", "LocalLog",
        "ActivateStage", "SetInput", "SetTargetHeading", "LockNavSphere",
        "SetActivationGroup", "SetTarget", "SetTimeMode", "SetCameraProperty",
        "SetCraftProperty", "SetVariable", "ChangeVariable", "UserInput",
        "SetList", "BroadcastMessage", "CallCustomInstruction", "Comment",
        "CustomExpression", "CustomInstruction",
    }
    for instr_container in root.iter("Instructions"):
        for child in instr_container:
            if child.tag in instruction_tags and child.get("id") is None:
                warnings.append(
                    f"Instruction <{child.tag} style={child.get('style','?')}>"
                    f" has no id attribute"
                )

    if errors:
        print(f"FAIL  {path.name}")
        for e in errors:
            print(f"      ERROR   {e}")
        for w in warnings:
            print(f"      WARN    {w}")
        return False
    else:
        status = "OK"
        if warnings:
            status = "WARN"
        print(f"{status:<4}  {path.name}  ({len(all_ids)} blocks)")
        for w in warnings:
            print(f"      WARN    {w}")
        return True


# ============================================================
#  CRAFT FILE UTILITIES
# ============================================================

def list_craft_programs() -> list:
    """Return (craft_name, part_id, program_name) for all embedded programs."""
    results = []
    for craft_file in CRAFTS_DIR.glob("*.xml"):
        try:
            tree = ET.parse(craft_file)
            root = tree.getroot()
            craft_name = root.get("name", craft_file.stem)
            for part in root.iter("Part"):
                fp = part.find("FlightProgram")
                if fp is not None:
                    prog = fp.find("Program")
                    if prog is not None:
                        results.append((craft_name, part.get("id"),
                                        prog.get("name", "")))
        except Exception:
            pass
    return results


def extract_craft_program(craft_name: str, part_id: str = None) -> str:
    """Print the Vizzy XML embedded in a craft file."""
    candidates = list(CRAFTS_DIR.glob(f"*{craft_name}*"))
    if not candidates:
        raise FileNotFoundError(f"Craft not found: {craft_name!r}")
    tree = ET.parse(candidates[0])
    root = tree.getroot()
    for part in root.iter("Part"):
        if part_id and part.get("id") != str(part_id):
            continue
        fp = part.find("FlightProgram")
        if fp is not None:
            prog_el = fp.find("Program")
            if prog_el is not None:
                xml_str = _pretty_xml(prog_el)
                print(xml_str)
                return xml_str
    raise ValueError(f"No Vizzy program found in craft {craft_name!r}")


# ============================================================
#  CLI
# ============================================================

def cmd_list(_args):
    files = sorted(PROGRAMS_DIR.glob("*.xml"))
    # Skip backup folder files
    files = [f for f in files if "_backups" not in str(f)]
    if not files:
        print("No flight programs found.")
        return
    print(f"\nFlight Programs in: {PROGRAMS_DIR}\n")
    for f in files:
        try:
            tree = ET.parse(f)
            name = tree.getroot().get("name", "?")
            mfd = " [MfD]" if tree.getroot().get("requiresMfd") == "true" else ""
            block_count = sum(1 for el in tree.getroot().iter()
                              if el.get("id") is not None)
            print(f"  {f.name:<50}  {name}{mfd}  ({block_count} blocks)")
        except Exception as ex:
            print(f"  {f.name}  (ERROR: {ex})")
    print()
    craft_progs = list_craft_programs()
    if craft_progs:
        print(f"Embedded craft programs:\n")
        for craft, pid, pname in craft_progs:
            print(f"  {craft}  (part {pid})  {pname}")
        print()


def cmd_read(args):
    if not args:
        print("Usage: vizzy_tool.py read <name_or_file>")
        return
    try:
        display_program(_resolve_path(args[0]))
    except FileNotFoundError as e:
        print(e)


def cmd_validate(args):
    if not args:
        # validate all
        all_ok = True
        for f in sorted(PROGRAMS_DIR.glob("*.xml")):
            if "_backups" not in str(f):
                ok = validate_program(f)
                all_ok = all_ok and ok
        if all_ok:
            print("\nAll programs OK.")
        return
    try:
        validate_program(_resolve_path(args[0]))
    except FileNotFoundError as e:
        print(e)


def cmd_new(args):
    if not args:
        print("Usage: vizzy_tool.py new <name> [--mfd]")
        return
    name = " ".join(a for a in args if not a.startswith("--"))
    mfd = "--mfd" in args
    prog = VizzyProgram(name, requires_mfd=mfd)
    prog.root_instructions.append(prog.on_start())
    path = prog.save()
    print(f"Created: {path}")


def main():
    argv = sys.argv[1:]
    if not argv:
        print("Commands: list | read <name> | validate [name] | new <name> [--mfd]")
        return
    cmd = argv[0].lower()
    rest = argv[1:]
    dispatch = {
        "list":     cmd_list,
        "read":     cmd_read,
        "validate": cmd_validate,
        "new":      cmd_new,
    }
    if cmd in dispatch:
        dispatch[cmd](rest)
    else:
        print(f"Unknown command: {cmd!r}")
        print("Commands: list | read | validate | new")


if __name__ == "__main__":
    main()
