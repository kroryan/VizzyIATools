import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


from vizzy_tool import E, PROGRAMS_DIR, VizzyProgram, validate_program


PROGRAM_NAME = "Universal Target Transfer Scratch"
G = 6.67430e-11
PI = 3.141592653589793


def n(value):
    return E.num(value)


def v(name):
    return E.var(name)


def maximum(a, b):
    return E.max2(a, b)


def minimum(a, b):
    return E.min2(a, b)


def clamp(expr, low, high):
    return E.cond(
        E.lt(expr, n(low)),
        n(low),
        E.cond(E.gt(expr, n(high)), n(high), expr),
    )


def ratio(num_expr, den_expr, fallback=0):
    return E.cond(E.eq(den_expr, n(0)), n(fallback), E.div(num_expr, den_expr))


def abs_expr(expr):
    return E.math("abs", expr)


def current_planet():
    return E.prop("Orbit.Planet", "prop-name")


def wrap360(expr):
    return E.cond(
        E.lt(expr, n(0)),
        E.add(expr, n(360)),
        E.cond(E.gte(expr, n(360)), E.sub(expr, n(360)), expr),
    )


def wrap180(expr):
    return E.cond(
        E.gt(expr, n(180)),
        E.sub(expr, n(360)),
        E.cond(E.lt(expr, n(-180)), E.add(expr, n(360)), expr),
    )


def burn_throttle(remaining_dv):
    return E.cond(
        E.gt(remaining_dv, n(120)),
        n(1),
        E.cond(
            E.gt(remaining_dv, n(40)),
            n(0.55),
            E.cond(
                E.gt(remaining_dv, n(12)),
                n(0.22),
                n(0.08),
            ),
        ),
    )


def build_program():
    prog = VizzyProgram(PROGRAM_NAME)
    instr = prog.root_instructions

    variables = [
        ("TargetName", 0),
        ("TargetBody", 0),
        ("CurrentParent", 0),
        ("PlanetRadius", 0),
        ("PlanetMass", 0),
        ("Mu", 0),
        ("AtmosphereHeight", 0),
        ("ParkingAltitude", 0),
        ("SafeOrbitAltitude", 0),
        ("CurrentAltitude", 0),
        ("CurrentApoapsis", 0),
        ("CurrentPeriapsis", 0),
        ("CurrentOrbitVelocity", 0),
        ("CurrentVerticalVelocity", 0),
        ("CurrentRadius", 0),
        ("ApoapsisRadius", 0),
        ("PeriapsisRadius", 0),
        ("TargetRadius", 0),
        ("TargetAltitude", 0),
        ("ApoapsisError", 0),
        ("PeriapsisError", 0),
        ("TurnStart", 0),
        ("TurnEnd", 0),
        ("Pct", 0),
        ("PitchTarget", 90),
        ("ThrottleCommand", 0),
        ("LastStageTime", -10),
        ("LaunchHeading", 90),
        ("Accel", 0),
        ("BurnLeadTime", 0),
        ("CircularSpeed", 0),
        ("ApoSpeedNow", 0),
        ("CurrentSMA", 0),
        ("TransferSemiMajorAxis", 0),
        ("TransferTime", 0),
        ("TargetAngularRate", 0),
        ("RequiredPhase", 0),
        ("CurrentPhase", 0),
        ("PhaseError", 0),
        ("TransferDirection", 1),
        ("PhaseTolerance", 2),
        ("RemainingDV", 0),
        ("TargetDepartureSpeed", 0),
        ("TransferDV", 0),
        ("BurnDeadline", 0),
        ("CoastLead", 0),
        ("SupportedTarget", 0),
    ]
    for name, initial in variables:
        prog.var(name, initial)

    auto_stage_if = prog.if_block(
        E.and_(
            E.gt(E.prop("Input.Throttle", "prop-input"), n(0.05)),
            E.and_(
                E.lt(E.prop("Misc.Stage", "prop-misc"), E.prop("Misc.NumStages", "prop-misc")),
                E.and_(
                    E.gt(
                        E.sub(E.prop("Time.TimeSinceLaunch", "prop-time"), v("LastStageTime")),
                        n(1.2),
                    ),
                    E.or_(
                        E.lt(E.prop("Fuel.FuelInStage", "prop-fuel"), n(0.01)),
                        E.lt(E.prop("Performance.CurrentEngineThrust", "prop-performance"), n(1)),
                    ),
                ),
            ),
        )
    )
    auto_stage_if.find("Instructions").append(prog.activate_stage())
    auto_stage_if.find("Instructions").append(
        prog.set_var("LastStageTime", E.prop("Time.TimeSinceLaunch", "prop-time"))
    )
    auto_stage_if.find("Instructions").append(prog.wait_seconds(n(0.3)))
    prog.add_custom_instruction("Auto Stage", [], [auto_stage_if])

    update_orbit_body = [
        prog.set_var("CurrentAltitude", E.prop("Altitude.ASL", "prop-altitude")),
        prog.set_var("CurrentApoapsis", E.prop("Orbit.Apoapsis", "prop-orbit")),
        prog.set_var("CurrentPeriapsis", E.prop("Orbit.Periapsis", "prop-orbit")),
        prog.set_var("CurrentOrbitVelocity", E.prop("Vel.OrbitVelocity", "prop-velocity")),
        prog.set_var(
            "CurrentVerticalVelocity",
            E.prop("Vel.VerticalSurfaceVelocity", "prop-velocity"),
        ),
        prog.set_var("CurrentRadius", E.vec1("length", E.prop("Nav.Position", "prop-nav"))),
        prog.set_var("ApoapsisRadius", E.add(v("PlanetRadius"), v("CurrentApoapsis"))),
        prog.set_var("PeriapsisRadius", E.add(v("PlanetRadius"), v("CurrentPeriapsis"))),
        prog.set_var("ApoapsisError", E.sub(v("ParkingAltitude"), v("CurrentApoapsis"))),
        prog.set_var("PeriapsisError", E.sub(v("ParkingAltitude"), v("CurrentPeriapsis"))),
    ]
    prog.add_custom_instruction("Update Orbit State", [], update_orbit_body)

    local_phase_angle = wrap360(
        E.math(
            "rad2deg",
            E.atan2(
                E.vec2(
                    "dot",
                    E.vec1(
                        "norm",
                        E.vec2(
                            "cross",
                            E.prop("Nav.Position", "prop-nav"),
                            E.prop("Vel.OrbitVelocity", "prop-velocity"),
                        ),
                    ),
                    E.vec2(
                        "cross",
                        E.vec1("norm", E.prop("Nav.Position", "prop-nav")),
                        E.vec1("norm", E.prop("Target.Position", "prop-nav")),
                    ),
                ),
                E.vec2(
                    "dot",
                    E.vec1("norm", E.prop("Nav.Position", "prop-nav")),
                    E.vec1("norm", E.prop("Target.Position", "prop-nav")),
                ),
            ),
        )
    )

    update_transfer_body = [
        prog.call_instruction("Update Orbit State"),
        prog.set_var("TargetBody", E.prop("Target.Planet", "prop-name")),
        prog.set_var("SupportedTarget", E.eq(E.prop("Target.Planet", "prop-name"), current_planet())),
        prog.set_var("TargetRadius", E.vec1("length", E.prop("Target.Position", "prop-nav"))),
        prog.set_var("TargetAltitude", E.sub(v("TargetRadius"), v("PlanetRadius"))),
        prog.set_var(
            "TransferDirection",
            E.cond(E.gt(v("TargetRadius"), v("CurrentRadius")), n(1), n(-1)),
        ),
        prog.set_var(
            "TransferSemiMajorAxis",
            E.div(E.add(v("CurrentRadius"), v("TargetRadius")), n(2)),
        ),
        prog.set_var(
            "TransferTime",
            E.mul(
                n(PI),
                E.math("sqrt", ratio(E.pow(v("TransferSemiMajorAxis"), n(3)), v("Mu"), 0)),
            ),
        ),
        prog.set_var(
            "TargetAngularRate",
            E.math("sqrt", ratio(v("Mu"), E.pow(v("TargetRadius"), n(3)), 0)),
        ),
        prog.set_var(
            "RequiredPhase",
            wrap360(
                E.cond(
                    E.gt(v("TransferDirection"), n(0)),
                    E.sub(
                        n(180),
                        E.math("rad2deg", E.mul(v("TargetAngularRate"), v("TransferTime"))),
                    ),
                    E.add(
                        n(180),
                        E.math("rad2deg", E.mul(v("TargetAngularRate"), v("TransferTime"))),
                    ),
                )
            ),
        ),
        prog.set_var("CurrentPhase", local_phase_angle),
        prog.set_var("PhaseError", wrap180(E.sub(v("CurrentPhase"), v("RequiredPhase")))),
        prog.set_var(
            "TargetDepartureSpeed",
            E.math(
                "sqrt",
                E.mul(
                    v("Mu"),
                    E.sub(
                        ratio(n(2), v("CurrentRadius"), 0),
                        ratio(n(1), v("TransferSemiMajorAxis"), 0),
                    ),
                ),
            ),
        ),
        prog.set_var(
            "TransferDV",
            abs_expr(E.sub(v("TargetDepartureSpeed"), v("CurrentOrbitVelocity"))),
        ),
        prog.set_var(
            "Accel",
            maximum(n(0.1), E.vec1("length", E.prop("Vel.Acceleration", "prop-velocity"))),
        ),
        prog.set_var(
            "CoastLead",
            clamp(E.add(E.div(E.div(v("TransferDV"), v("Accel")), n(2)), n(2)), 2, 40),
        ),
    ]
    prog.add_custom_instruction("Update Transfer State", [], update_transfer_body)

    instr.append(prog.on_start())
    instr.append(
        prog.display(
            E.text("Select a target first. This scratch Vizzy only transfers safely to targets orbiting the current body."),
            duration=9,
        )
    )
    instr.append(
        prog.wait_until(
            E.gt(E.length_str(E.prop("Target.Name", "prop-name")), n(0))
        )
    )
    instr.append(prog.set_var("TargetName", E.prop("Target.Name", "prop-name")))
    instr.append(prog.set_var("TargetBody", E.prop("Target.Planet", "prop-name")))
    instr.append(prog.set_var("CurrentParent", E.planet_prop("parent", current_planet())))
    instr.append(prog.set_var("PlanetRadius", E.planet_prop("radius", current_planet())))
    instr.append(prog.set_var("PlanetMass", E.planet_prop("mass", current_planet())))
    instr.append(prog.set_var("Mu", E.mul(n(G), v("PlanetMass"))))
    instr.append(prog.set_var("AtmosphereHeight", E.planet_prop("atmosphereHeight", current_planet())))
    instr.append(
        prog.set_var(
            "SafeOrbitAltitude",
            maximum(
                n(50_000),
                minimum(
                    E.add(v("AtmosphereHeight"), n(20_000)),
                    n(150_000),
                ),
            ),
        )
    )
    instr.append(prog.call_instruction("Update Transfer State"))
    instr.append(
        prog.set_var(
            "ParkingAltitude",
            maximum(
                v("SafeOrbitAltitude"),
                minimum(
                    n(180_000),
                    maximum(n(120_000), E.mul(v("TargetAltitude"), n(0.35))),
                ),
            ),
        )
    )
    instr.append(prog.set_var("LaunchHeading", n(90)))
    instr.append(
        prog.set_var("TurnStart", clamp(E.mul(v("AtmosphereHeight"), n(0.015)), 1000, 3000))
    )
    instr.append(
        prog.set_var(
            "TurnEnd",
            maximum(
                E.add(v("AtmosphereHeight"), n(5000)),
                clamp(E.mul(v("ParkingAltitude"), n(0.55)), 25_000, 90_000),
            ),
        )
    )
    instr.append(
        prog.display(
            E.format(
                E.text("Target {0} detected. Parking orbit {1:n0} km."),
                v("TargetName"),
                E.div(v("ParkingAltitude"), n(1000)),
            ),
            duration=8,
        )
    )

    instr.append(prog.set_heading(v("LaunchHeading")))
    instr.append(prog.set_pitch(n(90)))
    instr.append(prog.set_input("throttle", n(1)))
    instr.append(prog.activate_stage())
    instr.append(prog.set_var("LastStageTime", E.prop("Time.TimeSinceLaunch", "prop-time")))
    instr.append(prog.wait_seconds(n(0.5)))

    vertical = prog.while_loop(E.lt(E.prop("Altitude.ASL", "prop-altitude"), v("TurnStart")))
    vertical_body = vertical.find("Instructions")
    vertical_body.append(prog.call_instruction("Auto Stage"))
    vertical_body.append(prog.wait_seconds(n(0.25)))
    instr.append(vertical)

    gravity_turn = prog.while_loop(E.lt(E.prop("Altitude.ASL", "prop-altitude"), v("TurnEnd")))
    gt_body = gravity_turn.find("Instructions")
    gt_body.append(
        prog.set_var(
            "Pct",
            maximum(
                n(0),
                minimum(
                    n(1),
                    ratio(
                        E.sub(E.prop("Altitude.ASL", "prop-altitude"), v("TurnStart")),
                        maximum(E.sub(v("TurnEnd"), v("TurnStart")), n(1)),
                        0,
                    ),
                ),
            ),
        )
    )
    gt_body.append(
        prog.set_var(
            "PitchTarget",
            maximum(n(3), E.mul(n(90), E.math("sqrt", E.sub(n(1), v("Pct"))))),
        )
    )
    gt_body.append(prog.set_pitch(v("PitchTarget")))
    gt_body.append(prog.call_instruction("Auto Stage"))
    gt_body.append(prog.wait_seconds(n(0.25)))
    instr.append(gravity_turn)

    instr.append(prog.lock_heading("Prograde"))
    instr.append(prog.display(E.text("Gravity turn complete. Raising apoapsis."), duration=5))

    raise_apo = prog.while_loop(E.lt(E.prop("Orbit.Apoapsis", "prop-orbit"), v("ParkingAltitude")))
    raise_body = raise_apo.find("Instructions")
    raise_body.append(
        prog.set_var(
            "ThrottleCommand",
            E.cond(
                E.lt(E.prop("Orbit.Apoapsis", "prop-orbit"), E.sub(v("ParkingAltitude"), n(10_000))),
                n(1),
                n(0.35),
            ),
        )
    )
    raise_body.append(prog.set_input("throttle", v("ThrottleCommand")))
    raise_body.append(prog.call_instruction("Auto Stage"))
    raise_body.append(prog.wait_seconds(n(0.25)))
    instr.append(raise_apo)

    instr.append(prog.set_input("throttle", n(0)))
    instr.append(prog.call_instruction("Update Orbit State"))
    instr.append(
        prog.set_var(
            "CurrentSMA",
            E.add(
                v("PlanetRadius"),
                E.div(E.add(v("CurrentApoapsis"), v("CurrentPeriapsis")), n(2)),
            ),
        )
    )
    instr.append(prog.set_var("ApoapsisRadius", E.add(v("PlanetRadius"), v("CurrentApoapsis"))))
    instr.append(
        prog.set_var(
            "CircularSpeed",
            E.math("sqrt", ratio(v("Mu"), v("ApoapsisRadius"), 0)),
        )
    )
    instr.append(
        prog.set_var(
            "ApoSpeedNow",
            E.math(
                "sqrt",
                E.mul(
                    v("Mu"),
                    E.sub(ratio(n(2), v("ApoapsisRadius"), 0), ratio(n(1), v("CurrentSMA"), 0)),
                ),
            ),
        )
    )
    instr.append(
        prog.set_var(
            "Accel",
            maximum(n(0.1), E.vec1("length", E.prop("Vel.Acceleration", "prop-velocity"))),
        )
    )
    instr.append(
        prog.set_var(
            "BurnLeadTime",
            clamp(
                E.add(E.div(E.div(E.sub(v("CircularSpeed"), v("ApoSpeedNow")), v("Accel")), n(2)), n(4)),
                3,
                45,
            ),
        )
    )
    instr.append(
        prog.display(E.text("Coasting to apoapsis for circularization."), duration=4)
    )
    instr.append(
        prog.wait_until(E.lt(E.prop("Orbit.TimeToApoapsis", "prop-orbit"), v("BurnLeadTime")))
    )

    instr.append(prog.lock_heading("Prograde"))
    instr.append(prog.call_instruction("Update Orbit State"))
    instr.append(prog.set_var("BurnDeadline", E.add(E.prop("Time.TimeSinceLaunch", "prop-time"), n(240))))
    instr.append(prog.display(E.text("Circularizing parking orbit."), duration=4))

    circularize = prog.while_loop(
        E.and_(
            E.lt(E.prop("Time.TimeSinceLaunch", "prop-time"), v("BurnDeadline")),
            E.and_(
                E.gt(E.sub(v("CircularSpeed"), E.prop("Vel.OrbitVelocity", "prop-velocity")), n(2)),
                E.lt(E.prop("Orbit.Periapsis", "prop-orbit"), v("SafeOrbitAltitude")),
            ),
        )
    )
    circ_body = circularize.find("Instructions")
    circ_body.append(prog.call_instruction("Update Orbit State"))
    circ_body.append(
        prog.set_var(
            "RemainingDV",
            maximum(n(0), E.sub(v("CircularSpeed"), v("CurrentOrbitVelocity"))),
        )
    )
    circ_body.append(prog.set_input("throttle", burn_throttle(v("RemainingDV"))))
    circ_body.append(prog.call_instruction("Auto Stage"))
    circ_body.append(prog.wait_seconds(n(0.1)))
    instr.append(circularize)

    instr.append(prog.set_input("throttle", n(0)))
    instr.append(prog.call_instruction("Update Orbit State"))
    instr.append(
        prog.display(
            E.format(
                E.text("Parking orbit reached. Apoapsis {0:n0} km, periapsis {1:n0} km."),
                E.div(v("CurrentApoapsis"), n(1000)),
                E.div(v("CurrentPeriapsis"), n(1000)),
            ),
            duration=8,
        )
    )

    unsupported_if = prog.if_block(E.not_(v("SupportedTarget")))
    unsupported_body = unsupported_if.find("Instructions")
    unsupported_body.append(
        prog.display(
            E.format(
                E.text("Scratch transfer stopped safely. Target {0} does not orbit the current body {1}."),
                v("TargetName"),
                current_planet(),
            ),
            duration=10,
        )
    )
    unsupported_body.append(
        prog.flight_log(
            E.format(
                E.text(
                    "Transfer skipped. This scratch Vizzy only supports targets orbiting {0}; selected target {1} orbits {2}."
                ),
                current_planet(),
                v("TargetName"),
                v("TargetBody"),
            )
        )
    )
    instr.append(unsupported_if)

    supported_else = prog.else_block()
    supported_body = supported_else.find("Instructions")
    supported_body.append(prog.call_instruction("Update Transfer State"))
    supported_body.append(
        prog.display(
            E.format(
                E.text("Target shares the current body. Waiting Hohmann phase for {0}."),
                v("TargetName"),
            ),
            duration=8,
        )
    )

    phase_wait = prog.while_loop(E.gt(abs_expr(v("PhaseError")), v("PhaseTolerance")))
    phase_body = phase_wait.find("Instructions")
    phase_body.append(prog.call_instruction("Update Transfer State"))
    phase_body.append(prog.lock_heading("Prograde"))
    phase_body.append(prog.wait_seconds(n(0.5)))
    supported_body.append(phase_wait)

    supported_body.append(prog.call_instruction("Update Transfer State"))
    supported_body.append(
        prog.set_var("BurnDeadline", E.add(E.prop("Time.TimeSinceLaunch", "prop-time"), n(180))))
    supported_body.append(
        prog.display(
            E.format(
                E.text("Transfer window reached. Burn to {0}."),
                v("TargetName"),
            ),
            duration=5,
        )
    )

    outward_if = prog.if_block(E.gt(v("TransferDirection"), n(0)))
    outward_body = outward_if.find("Instructions")
    outward_body.append(prog.lock_heading("Prograde"))
    outward_burn = prog.while_loop(
        E.and_(
            E.lt(E.prop("Time.TimeSinceLaunch", "prop-time"), v("BurnDeadline")),
            E.gt(E.sub(v("TargetDepartureSpeed"), E.prop("Vel.OrbitVelocity", "prop-velocity")), n(2)),
        )
    )
    outward_burn_body = outward_burn.find("Instructions")
    outward_burn_body.append(prog.call_instruction("Update Transfer State"))
    outward_burn_body.append(
        prog.set_var(
            "RemainingDV",
            maximum(n(0), E.sub(v("TargetDepartureSpeed"), v("CurrentOrbitVelocity"))),
        )
    )
    outward_burn_body.append(prog.set_input("throttle", burn_throttle(v("RemainingDV"))))
    outward_burn_body.append(prog.call_instruction("Auto Stage"))
    outward_burn_body.append(prog.wait_seconds(n(0.1)))
    outward_body.append(outward_burn)
    outward_body.append(prog.set_input("throttle", n(0)))
    supported_body.append(outward_if)

    inward_else = prog.else_block()
    inward_body = inward_else.find("Instructions")
    inward_body.append(prog.lock_heading("Retrograde"))
    inward_burn = prog.while_loop(
        E.and_(
            E.lt(E.prop("Time.TimeSinceLaunch", "prop-time"), v("BurnDeadline")),
            E.gt(E.sub(E.prop("Vel.OrbitVelocity", "prop-velocity"), v("TargetDepartureSpeed")), n(2)),
        )
    )
    inward_burn_body = inward_burn.find("Instructions")
    inward_burn_body.append(prog.call_instruction("Update Transfer State"))
    inward_burn_body.append(
        prog.set_var(
            "RemainingDV",
            maximum(n(0), E.sub(v("CurrentOrbitVelocity"), v("TargetDepartureSpeed"))),
        )
    )
    inward_burn_body.append(prog.set_input("throttle", burn_throttle(v("RemainingDV"))))
    inward_burn_body.append(prog.call_instruction("Auto Stage"))
    inward_burn_body.append(prog.wait_seconds(n(0.1)))
    inward_body.append(inward_burn)
    inward_body.append(prog.set_input("throttle", n(0)))
    supported_body.append(inward_else)

    supported_body.append(prog.lock_heading("None"))
    supported_body.append(prog.call_instruction("Update Orbit State"))
    supported_body.append(
        prog.display(
            E.format(
                E.text("Transfer burn complete. Apoapsis {0:n0} km, periapsis {1:n0} km."),
                E.div(v("CurrentApoapsis"), n(1000)),
                E.div(v("CurrentPeriapsis"), n(1000)),
            ),
            duration=10,
        )
    )
    supported_body.append(
        prog.flight_log(
            E.format(
                E.text(
                    "Scratch same-body transfer complete toward {0}. Apoapsis {1:n0} km, periapsis {2:n0} km."
                ),
                v("TargetName"),
                E.div(v("CurrentApoapsis"), n(1000)),
                E.div(v("CurrentPeriapsis"), n(1000)),
            )
        )
    )
    instr.append(supported_else)

    return prog


def main():
    PROGRAMS_DIR.mkdir(parents=True, exist_ok=True)
    prog = build_program()
    path = prog.save(f"{PROGRAM_NAME}.xml")
    validate_program(path)


if __name__ == "__main__":
    main()
