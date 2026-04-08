import copy
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


from vizzy_tool import CRAFTS_DIR, E, PROGRAMS_DIR, USERDATA, _pretty_xml, validate_program


SOURCE_CANDIDATES = [
    PROGRAMS_DIR / "Universal Vizzy Mission 2 - Enhanced.xml",
    ROOT / "Example" / "Vizzy" / "Universal Vizzy Mission 2.xml",
    ROOT / "Example" / "Vizzy" / "Universal Vizzy Mission 2 - Enhanced.xml",
]
PROGRAM_NAME = "Universal Target Transfer Auto"


def find_source() -> Path:
    for path in SOURCE_CANDIDATES:
        if path.exists():
            return path
    raise FileNotFoundError("No se encontro un XML base de Universal Vizzy Mission 2.")


def clone(el: ET.Element) -> ET.Element:
    return copy.deepcopy(el)


def next_id_factory(root: ET.Element):
    next_id = max(int(el.get("id")) for el in root.iter() if el.get("id") is not None) + 1

    def alloc() -> str:
        nonlocal next_id
        value = str(next_id)
        next_id += 1
        return value

    return alloc


def instr(alloc, tag: str, style: str, **attrs) -> ET.Element:
    el = ET.Element(tag)
    el.set("id", alloc())
    el.set("style", style)
    for key, value in attrs.items():
        el.set(key, value)
    return el


def make_broadcast(alloc, message: str, data: ET.Element, scope: str = "local") -> ET.Element:
    style_map = {
        "local": ("broadcast-msg", "false", "true"),
        "craft": ("broadcast-msg-craft", "false", "false"),
        "nearby": ("broadcast-msg-nearby", "true", "false"),
    }
    style, global_flag, local_flag = style_map[scope]
    el = instr(alloc, "BroadcastMessage", style)
    el.set("global", global_flag)
    el.set("local", local_flag)
    msg = ET.SubElement(el, "Constant")
    msg.set("text", message)
    el.append(data)
    return el


def make_wait_until_target_selected(alloc) -> ET.Element:
    el = instr(alloc, "WaitUntil", "wait-until")
    cmp_el = E.gt(
        E.length_str(E.prop("Target.Name", "prop-name")),
        E.num(0),
    )
    el.append(cmp_el)
    return el


def make_set_var(alloc, name: str, value: ET.Element) -> ET.Element:
    el = instr(alloc, "SetVariable", "set-variable")
    var = ET.SubElement(el, "Variable")
    var.set("list", "false")
    var.set("local", "false")
    var.set("variableName", name)
    el.append(value)
    return el


def make_list_clear(alloc, name: str) -> ET.Element:
    el = instr(alloc, "SetList", "list-clear", op="clear")
    var = ET.SubElement(el, "Variable")
    var.set("list", "true")
    var.set("local", "false")
    var.set("variableName", name)
    return el


def make_list_add(alloc, name: str, value: ET.Element) -> ET.Element:
    el = instr(alloc, "SetList", "list-add", op="add")
    var = ET.SubElement(el, "Variable")
    var.set("list", "true")
    var.set("local", "false")
    var.set("variableName", name)
    el.append(value)
    return el


def make_call(alloc, name: str, *args: ET.Element) -> ET.Element:
    el = instr(alloc, "CallCustomInstruction", "call-custom-instruction", call=name)
    for arg in args:
        el.append(arg)
    return el


def make_if(alloc, condition: ET.Element) -> ET.Element:
    el = instr(alloc, "If", "if")
    el.append(condition)
    ET.SubElement(el, "Instructions")
    return el


def make_else(alloc) -> ET.Element:
    el = instr(alloc, "ElseIf", "else")
    const = ET.SubElement(el, "Constant")
    const.set("bool", "true")
    ET.SubElement(el, "Instructions")
    return el


def make_display(alloc, text: str, seconds: float = 7) -> ET.Element:
    el = instr(alloc, "DisplayMessage", "display")
    t = ET.SubElement(el, "Constant")
    t.set("text", text)
    d = ET.SubElement(el, "Constant")
    d.set("number", str(seconds))
    return el


def patch_startup(root: ET.Element):
    alloc = next_id_factory(root)

    flight_thread = None
    for instructions in root.findall("Instructions"):
        first = instructions[0] if len(instructions) else None
        if first is not None and first.tag == "Event" and first.get("event") == "FlightStart":
            flight_thread = instructions
            break
    if flight_thread is None:
        raise ValueError("No se encontro el hilo FlightStart en el XML base.")

    flight_thread.append(make_display(
        alloc,
        "Select a target in map or nav sphere. Launch will wait until a target exists.",
        10,
    ))
    flight_thread.append(make_broadcast(alloc, "Planet_List", E.num(0), "local"))

    wait_planet = instr(alloc, "WaitUntil", "wait-until")
    wait_planet.append(E.eq(E.var("Count"), E.text("1")))
    flight_thread.append(wait_planet)

    flight_thread.append(make_wait_until_target_selected(alloc))
    flight_thread.append(
        make_set_var(alloc, "Target", E.prop("Target.Name", "prop-name"))
    )
    flight_thread.append(
        make_set_var(
            alloc,
            "Periapsis",
            E.max2(
                E.add(
                    E.text("50000"),
                    E.mul(
                        E.text("0.15"),
                        E.planet_prop("atmosphereHeight", E.var("Target")),
                    ),
                ),
                E.mul(E.text("0.03"), E.planet_prop("soiRadius", E.var("Target"))),
            ),
        )
    )
    flight_thread.append(make_set_var(alloc, "Inclination", E.text("random")))
    flight_thread.append(make_set_var(alloc, "RightAscension", E.text("random")))
    flight_thread.append(make_list_clear(alloc, "Planet"))
    flight_thread.append(make_list_add(alloc, "Planet", E.var("Target")))
    flight_thread.append(make_list_add(alloc, "Planet", E.var("Periapsis")))
    flight_thread.append(make_list_add(alloc, "Planet", E.var("RightAscension")))
    flight_thread.append(make_list_add(alloc, "Planet", E.var("Inclination")))
    flight_thread.append(make_call(alloc, "Target Name", E.var("Target")))

    condition = E.call_expr(
        "String Input",
        E.prop("Orbit.Planet", "prop-name"),
        E.list_get(E.list_var("Target_Name"), E.text("1")),
    )
    if_block = make_if(alloc, condition)
    if_block.find("Instructions").append(make_list_add(alloc, "Planet", E.text("interorbit")))
    flight_thread.append(if_block)

    else_block = make_else(alloc)
    else_block.find("Instructions").append(make_list_add(alloc, "Planet", E.text("interplanet")))
    flight_thread.append(else_block)

    flight_thread.append(make_display(
        alloc,
        "Target acquired. Starting launch and transfer sequence.",
        6,
    ))
    flight_thread.append(make_broadcast(alloc, "Vizzy_Run", E.num(0), "craft"))


def patch_rocket_engine_data(root: ET.Element):
    alloc = next_id_factory(root)
    target_thread = None
    for instructions in root.findall("Instructions"):
        first = instructions[0] if len(instructions) else None
        if (
            first is not None
            and first.tag == "CustomInstruction"
            and first.get("name") == "Rocket Engine Data"
        ):
            target_thread = instructions
            break

    if target_thread is None:
        raise ValueError("No se encontro la custom instruction 'Rocket Engine Data'.")

    custom_def = clone(target_thread[0])
    target_thread.clear()
    target_thread.append(custom_def)
    target_thread.append(make_display(
        alloc,
        "Using generic engine detection from Performance.* for universal compatibility.",
        5,
    ))

    if_no_thrust = make_if(
        alloc,
        E.lt(E.prop("Performance.MaxActiveEngineThrust", "prop-performance"), E.text("1")),
    )
    if_no_thrust.find("Instructions").append(instr(alloc, "ActivateStage", "activate-stage"))
    target_thread.append(if_no_thrust)

    wait_for_thrust = instr(alloc, "WaitUntil", "wait-until")
    wait_for_thrust.append(
        E.gt(E.prop("Performance.MaxActiveEngineThrust", "prop-performance"), E.text("1"))
    )
    target_thread.append(wait_for_thrust)

    target_thread.append(
        make_set_var(alloc, "ThrustVacuum", E.prop("Performance.MaxActiveEngineThrust", "prop-performance"))
    )
    target_thread.append(
        make_set_var(alloc, "Thrust", E.prop("Performance.MaxActiveEngineThrust", "prop-performance"))
    )
    target_thread.append(make_set_var(alloc, "EngineNumber", E.text("1")))
    target_thread.append(make_set_var(alloc, "ExitArea", E.text("1")))
    target_thread.append(make_set_var(alloc, "m0", E.prop("Performance.Mass", "prop-performance")))
    target_thread.append(make_set_var(alloc, "Isp", E.prop("Performance.CurrentIsp", "prop-performance")))

    mdot_expr = E.max2(
        E.text("0.001"),
        E.div(
            E.prop("Performance.MaxActiveEngineThrust", "prop-performance"),
            E.max2(
                E.text("0.1"),
                E.mul(
                    E.max2(E.text("0.1"), E.prop("Performance.CurrentIsp", "prop-performance")),
                    E.var("g0"),
                ),
            ),
        ),
    )
    target_thread.append(make_set_var(alloc, "mdot", mdot_expr))

    wait_for_burn = instr(alloc, "WaitUntil", "wait-until")
    wait_for_burn.append(
        E.gt(E.prop("Performance.BurnTime", "prop-performance"), E.text("1"))
    )
    target_thread.append(wait_for_burn)

    target_thread.append(make_set_var(alloc, "BurnOut", E.prop("Performance.BurnTime", "prop-performance")))
    target_thread.append(
        make_set_var(alloc, "mprop", E.mul(E.var("mdot"), E.var("BurnOut")))
    )
    target_thread.append(
        make_set_var(
            alloc,
            "mfinal",
            E.max2(E.text("0.1"), E.sub(E.var("m0"), E.var("mprop"))),
        )
    )
    target_thread.append(make_set_var(alloc, "TWR", E.prop("Performance.TWR", "prop-performance")))


def generate():
    src = find_source()
    root = ET.parse(src).getroot()
    root.set("name", PROGRAM_NAME)
    patch_startup(root)
    patch_rocket_engine_data(root)
    PROGRAMS_DIR.mkdir(parents=True, exist_ok=True)
    path = PROGRAMS_DIR / f"{PROGRAM_NAME}.xml"
    path.write_text(_pretty_xml(root), encoding="utf-8-sig")
    return path


def main():
    path = generate()
    print(f"Saved: {path}")
    validate_program(path)


if __name__ == "__main__":
    main()
