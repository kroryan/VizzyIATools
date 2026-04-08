# Universal Target Transfer Scratch

## Problem detected

The previous `Scratch` version mixed two incompatible approaches:

- Orbital insertion based on `Orbit.Periapsis < ParkingAltitude`.
- Transfer based on "raising or lowering an apsis" until it got close to the target radius.

That was too weak for real flight. If the periapsis did not respond as expected, the program had no reliable physical cutoff criterion and kept pushing indefinitely.

## What the large reference XML does

In [`Example/Vizzy/Universal Vizzy Mission 2.xml`](./Example/Vizzy/Universal%20Vizzy%20Mission%202.xml), the important parts do not simply watch apoapsis and periapsis:

- `Transfer Window to`: decides the correct orbital frame before calculating the window.
- `Target Node`: ensures the active target is the expected one before reading its properties.
- `Circular Orbit`: computes the desired orbital state and delegates the burn to an impulsive burn block.
- `Impulsive Burn`: does not burn "until an apsis reaches a number"; it computes a burn vector and stops when the remaining delta-v falls.

The practical consequence is that the large XML:

- waits for the correct time,
- burns in a specific direction,
- and has an exit condition based on remaining delta-v.

## Change applied to Scratch

Without reusing the large XML directly, the new version adopts only those principles:

- it first secures a parking orbit,
- circularization stops on `remaining delta-v` instead of "keep chasing periapsis",
- the transfer only runs if the target orbits the same current body,
- for targets outside that case, the program stops and reports it.

## Real scope of this version

The new `Universal Target Transfer Scratch` handles the simple and physically coherent case well:

- craft already in orbit or launching from a body,
- target orbiting that same body,
- outward or inward Hohmann transfer.

It does not yet attempt to solve, in a universal way:

- interplanetary escape,
- encounters across different SOIs,
- heliocentric escape vectors,
- Lambert-style corrections.

Those do appear in the large XML, but they require a complete vector transfer autopilot, not a simple `Scratch` variant.
