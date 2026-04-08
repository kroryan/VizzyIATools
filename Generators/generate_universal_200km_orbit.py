import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


from vizzy_tool import E, PROGRAMS_DIR, VizzyProgram, validate_program


TARGET_ALTITUDE = 200_000.0
G = 6.67430e-11
PROGRAM_NAME = "Universal Orbit 200km - Auto"
FALLBACK_PROGRAM_NAME = "Universal Orbit 200km - Auto FIXED"


def n(value):
    return E.num(value)


def v(name):
    return E.var(name)


def clamp(expr, low, high):
    return E.cond(
        E.lt(expr, n(low)),
        n(low),
        E.cond(E.gt(expr, n(high)), n(high), expr),
    )


def maximum(a, b):
    return E.max2(a, b)


def minimum(a, b):
    return E.min2(a, b)


def ratio(num_expr, den_expr, fallback=0):
    return E.cond(E.eq(den_expr, n(0)), n(fallback), E.div(num_expr, den_expr))


def current_planet():
    return E.prop("Orbit.Planet", "prop-name")


def build_program():
    prog = VizzyProgram(PROGRAM_NAME)
    instr = prog.root_instructions

    for name, initial in [
        ("TargetAltitude", TARGET_ALTITUDE),
        ("TargetAltitudeTolerance", 250),
        ("PlanetRadius", 0),
        ("PlanetMass", 0),
        ("Mu", 0),
        ("AtmosphereHeight", 0),
        ("TurnStart", 0),
        ("TurnEnd", 0),
        ("TargetHeading", 90),
        ("TargetRadius", 0),
        ("CurrentAltitude", 0),
        ("CurrentApoapsis", 0),
        ("CurrentPeriapsis", 0),
        ("CurrentOrbitVelocity", 0),
        ("CurrentSurfaceVelocity", 0),
        ("CurrentVerticalVelocity", 0),
        ("CurrentTWR", 0),
        ("TurnProgress", 0),
        ("PitchTarget", 90),
        ("ApoapsisError", 0),
        ("PeriapsisError", 0),
        ("SafeOrbitAltitude", 0),
        ("ThrottleCommand", 1),
        ("LastStageTime", -10),
        ("ApoapsisRadius", 0),
        ("PeriapsisRadius", 0),
        ("SemiMajorAxis", 0),
        ("CircularVelocity", 0),
        ("CurrentVelocityAtApoapsis", 0),
        ("CircularizeDeltaV", 0),
        ("CircularizeBurnTime", 0),
        ("BurnLeadTime", 0),
        ("StageDeltaV", 0),
        ("StageBurnTime", 0),
        ("DebugValue", 0),
    ]:
        prog.var(name, initial)

    auto_stage_body = []
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
                        E.lt(
                            E.prop("Performance.CurrentEngineThrust", "prop-performance"),
                            n(1),
                        ),
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
    auto_stage_body.append(auto_stage_if)
    prog.add_custom_instruction("Auto Stage", [], auto_stage_body)

    update_orbit_body = [
        prog.set_var("CurrentAltitude", E.prop("Altitude.ASL", "prop-altitude")),
        prog.set_var("CurrentApoapsis", E.prop("Orbit.Apoapsis", "prop-orbit")),
        prog.set_var("CurrentPeriapsis", E.prop("Orbit.Periapsis", "prop-orbit")),
        prog.set_var("CurrentOrbitVelocity", E.prop("Vel.OrbitVelocity", "prop-velocity")),
        prog.set_var("CurrentSurfaceVelocity", E.prop("Vel.SurfaceVelocity", "prop-velocity")),
        prog.set_var(
            "CurrentVerticalVelocity",
            E.prop("Vel.VerticalSurfaceVelocity", "prop-velocity"),
        ),
        prog.set_var("CurrentTWR", E.prop("Performance.TWR", "prop-performance")),
        prog.set_var(
            "ApoapsisRadius",
            E.add(v("PlanetRadius"), v("CurrentApoapsis")),
        ),
        prog.set_var(
            "PeriapsisRadius",
            E.add(v("PlanetRadius"), v("CurrentPeriapsis")),
        ),
        prog.set_var(
            "SemiMajorAxis",
            E.div(E.add(v("ApoapsisRadius"), v("PeriapsisRadius")), n(2)),
        ),
        prog.set_var(
            "CircularVelocity",
            E.math("sqrt", ratio(v("Mu"), E.add(v("PlanetRadius"), v("CurrentAltitude")), 0)),
        ),
        prog.set_var(
            "CurrentVelocityAtApoapsis",
            E.math(
                "sqrt",
                maximum(
                    n(0),
                    E.mul(
                        v("Mu"),
                        E.sub(
                            ratio(n(2), v("ApoapsisRadius"), 0),
                            ratio(n(1), v("SemiMajorAxis"), 0),
                        ),
                    ),
                ),
            ),
        ),
        prog.set_var(
            "CircularizeDeltaV",
            maximum(
                n(0),
                E.sub(
                    E.math("sqrt", ratio(v("Mu"), v("ApoapsisRadius"), 0)),
                    v("CurrentVelocityAtApoapsis"),
                ),
            ),
        ),
        prog.set_var("StageDeltaV", E.prop("Performance.StageDeltaV", "prop-performance")),
        prog.set_var("StageBurnTime", E.prop("Performance.BurnTime", "prop-performance")),
        prog.set_var(
            "CircularizeBurnTime",
            maximum(
                n(5),
                E.mul(
                    v("StageBurnTime"),
                    clamp(ratio(v("CircularizeDeltaV"), maximum(v("StageDeltaV"), n(1)), 0), 0, 1),
                ),
            ),
        ),
        prog.set_var(
            "BurnLeadTime",
            clamp(E.div(v("CircularizeBurnTime"), n(2)), 5, 25),
        ),
        prog.set_var("ApoapsisError", E.sub(v("TargetAltitude"), v("CurrentApoapsis"))),
        prog.set_var("PeriapsisError", E.sub(v("TargetAltitude"), v("CurrentPeriapsis"))),
    ]
    prog.add_custom_instruction("Update Orbit State", [], update_orbit_body)

    instr.append(prog.on_start())
    instr.append(prog.comment("Universal ascent to a nominal 200 km circular orbit"))
    instr.append(prog.set_input("throttle", n(0)))
    instr.append(prog.set_var("TargetAltitude", n(TARGET_ALTITUDE)))
    instr.append(prog.set_var("TargetAltitudeTolerance", n(250)))
    instr.append(prog.set_var("PlanetRadius", E.planet_prop("radius", current_planet())))
    instr.append(prog.set_var("PlanetMass", E.planet_prop("mass", current_planet())))
    instr.append(prog.set_var("Mu", E.mul(n(G), v("PlanetMass"))))
    instr.append(
        prog.set_var("AtmosphereHeight", E.planet_prop("atmosphereHeight", current_planet()))
    )
    instr.append(
        prog.set_var(
            "TurnStart",
            clamp(E.mul(v("AtmosphereHeight"), n(0.015)), 300, 2500),
        )
    )
    instr.append(
        prog.set_var(
            "TurnEnd",
            clamp(
                E.add(E.mul(v("TargetAltitude"), n(0.45)), E.mul(v("AtmosphereHeight"), n(0.15))),
                25_000,
                90_000,
            ),
        )
    )
    instr.append(
        prog.set_var(
            "SafeOrbitAltitude",
            maximum(
                n(10_000),
                minimum(
                    E.add(v("AtmosphereHeight"), n(15_000)),
                    n(120_000),
                ),
            ),
        )
    )
    instr.append(
        prog.set_var(
            "TargetHeading",
            E.cond(E.gte(E.planet_day(current_planet()), n(0)), n(90), n(270)),
        )
    )
    instr.append(prog.set_var("TargetRadius", E.add(v("PlanetRadius"), v("TargetAltitude"))))
    instr.append(
        prog.display(
            E.format(
                E.text(
                    "Auto-orbit initialized. Target orbit: {0:n0} km. Countdown started."
                ),
                E.div(v("TargetAltitude"), n(1000)),
            ),
            duration=5,
        )
    )

    for i in range(5, 0, -1):
        instr.append(
            prog.display(
                E.format(E.text("Launch in {0:n0}"), n(i)),
                duration=1,
            )
        )
        instr.append(prog.wait_seconds(n(1)))

    instr.append(prog.set_pitch(n(90)))
    instr.append(prog.set_heading(v("TargetHeading")))
    instr.append(prog.set_input("throttle", n(1)))
    instr.append(prog.activate_stage())
    instr.append(prog.set_var("LastStageTime", E.prop("Time.TimeSinceLaunch", "prop-time")))
    instr.append(prog.wait_seconds(n(0.5)))
    instr.append(prog.call_instruction("Update Orbit State"))

    ascent = prog.while_loop(E.gt(v("ApoapsisError"), v("TargetAltitudeTolerance")))
    ascent_body = ascent.find("Instructions")
    ascent_body.append(prog.call_instruction("Update Orbit State"))
    ascent_body.append(prog.call_instruction("Auto Stage"))
    ascent_body.append(
        prog.set_var(
            "TurnProgress",
            clamp(
                ratio(
                    E.sub(v("CurrentAltitude"), v("TurnStart")),
                    maximum(E.sub(v("TurnEnd"), v("TurnStart")), n(1)),
                    0,
                ),
                0,
                1,
            ),
        )
    )
    ascent_body.append(
        prog.set_var(
            "PitchTarget",
            maximum(
                n(8),
                E.sub(n(90), E.mul(v("TurnProgress"), n(82))),
            ),
        )
    )
    steepen = prog.if_block(
        E.and_(
            E.lt(v("CurrentVerticalVelocity"), n(20)),
            E.lt(v("CurrentAltitude"), E.mul(v("TargetAltitude"), n(0.45))),
        )
    )
    steepen.find("Instructions").append(
        prog.set_var(
            "PitchTarget",
            maximum(v("PitchTarget"), n(20)),
        )
    )
    ascent_body.append(steepen)
    ascent_body.append(prog.set_heading(v("TargetHeading")))
    ascent_body.append(prog.set_pitch(v("PitchTarget")))
    ascent_body.append(
        prog.set_var(
            "ThrottleCommand",
            E.cond(
                E.gt(v("ApoapsisError"), n(60_000)),
                n(1),
                E.cond(
                    E.gt(v("ApoapsisError"), n(20_000)),
                    n(0.65),
                    E.cond(
                        E.gt(v("ApoapsisError"), n(5_000)),
                        n(0.35),
                        E.cond(
                            E.gt(v("ApoapsisError"), n(1_000)),
                            n(0.15),
                            n(0.05),
                        ),
                    ),
                ),
            ),
        )
    )
    ascent_body.append(prog.set_input("throttle", v("ThrottleCommand")))
    ascent_body.append(prog.wait_seconds(n(0.1)))
    instr.append(ascent)

    instr.append(prog.set_input("throttle", n(0)))
    instr.append(prog.call_instruction("Update Orbit State"))
    instr.append(
        prog.display(
            E.format(
                E.text("Apoapsis target reached. Coasting. Stable orbit threshold {0:n0} km."),
                E.div(v("SafeOrbitAltitude"), n(1000)),
            ),
            duration=4,
        )
    )

    coast = prog.while_loop(E.gt(E.prop("Orbit.TimeToApoapsis", "prop-orbit"), v("BurnLeadTime")))
    coast_body = coast.find("Instructions")
    coast_body.append(prog.call_instruction("Update Orbit State"))
    coast_body.append(prog.lock_heading("Prograde"))
    coast_body.append(prog.wait_seconds(n(0.1)))
    instr.append(coast)

    instr.append(
        prog.display(
            E.format(
                E.text("Circularizing. Burn lead {0:n0} s, safe orbit above {1:n0} km."),
                v("BurnLeadTime"),
                E.div(v("SafeOrbitAltitude"), n(1000)),
            ),
            duration=4,
        )
    )

    circularize = prog.while_loop(E.lt(v("CurrentPeriapsis"), v("SafeOrbitAltitude")))
    circ_body = circularize.find("Instructions")
    circ_body.append(prog.call_instruction("Update Orbit State"))
    circ_body.append(prog.call_instruction("Auto Stage"))
    circ_body.append(prog.lock_heading("Prograde"))
    circ_body.append(
        prog.set_var(
            "CircularVelocity",
            E.math("sqrt", ratio(v("Mu"), E.add(v("PlanetRadius"), v("CurrentAltitude")), 0)),
        )
    )
    circ_body.append(
        prog.set_var(
            "CircularizeDeltaV",
            maximum(
                n(0),
                E.sub(v("CircularVelocity"), v("CurrentOrbitVelocity")),
            ),
        )
    )
    circ_body.append(
        prog.set_var(
            "ThrottleCommand",
            E.cond(
                E.lt(v("CurrentPeriapsis"), E.sub(v("SafeOrbitAltitude"), n(40_000))),
                n(0.7),
                E.cond(
                    E.lt(v("CurrentPeriapsis"), E.sub(v("SafeOrbitAltitude"), n(10_000))),
                    n(0.35),
                    E.cond(
                        E.lt(v("CurrentPeriapsis"), E.sub(v("SafeOrbitAltitude"), n(2_000))),
                        n(0.15),
                        E.cond(
                            E.lt(v("CurrentPeriapsis"), v("SafeOrbitAltitude")),
                            n(0.06),
                            n(0),
                        ),
                    ),
                ),
            ),
        )
    )
    circ_body.append(prog.set_input("throttle", v("ThrottleCommand")))
    circ_body.append(prog.wait_seconds(n(0.1)))
    instr.append(circularize)

    instr.append(prog.set_input("throttle", n(0)))
    instr.append(prog.lock_heading("Prograde"))
    instr.append(prog.call_instruction("Update Orbit State"))
    refine = prog.if_block(
        E.and_(
            E.gte(v("CurrentPeriapsis"), v("SafeOrbitAltitude")),
            E.lt(v("CurrentPeriapsis"), E.sub(v("TargetAltitude"), n(5_000))),
        )
    )
    refine.find("Instructions").append(
        prog.display(
            E.text("Stable orbit achieved. Exact 200 km correction skipped to avoid overburn."),
            duration=4,
        )
    )
    instr.append(refine)
    instr.append(
        prog.display(
            E.format(
                E.text("Stable orbit achieved. Apoapsis {0:n1} km, Periapsis {1:n1} km"),
                E.div(v("CurrentApoapsis"), n(1000)),
                E.div(v("CurrentPeriapsis"), n(1000)),
            ),
            duration=10,
        )
    )
    instr.append(
        prog.flight_log(
            E.format(
                E.text(
                    "Universal 200 km orbit complete. Apoapsis {0:n1} km, Periapsis {1:n1} km."
                ),
                E.div(v("CurrentApoapsis"), n(1000)),
                E.div(v("CurrentPeriapsis"), n(1000)),
            )
        )
    )

    return prog


def main():
    PROGRAMS_DIR.mkdir(parents=True, exist_ok=True)
    prog = build_program()
    try:
        path = prog.save(f"{PROGRAM_NAME}.xml")
    except PermissionError:
        path = prog.save(f"{FALLBACK_PROGRAM_NAME}.xml")
    validate_program(path)


if __name__ == "__main__":
    main()
