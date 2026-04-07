# Analisis del proyecto y del generador Vizzy

## 1. Estructura real del proyecto

El repositorio es pequeno y esta centrado en una sola herramienta:

- `vizzy_tool.py`: libreria principal y CLI.
- `README.md`: documentacion funcional y advertencias de compatibilidad.
- `Example/Vizzy/Universal Vizzy Mission 2 - Enhanced.xml`: ejemplo grande con mecanicas orbitales avanzadas.
- `Example/Craft/USP-01 Universal Space Probe AI Improved.xml`: craft con Vizzy embebido.

No hay dependencias externas. Todo se basa en `xml.etree.ElementTree` y en escritura de XML compatible con Juno: New Origins.

## 2. Que hace realmente `vizzy_tool.py`

La herramienta mezcla tres roles:

1. Builder:
   construye programas Vizzy desde Python con la clase `VizzyProgram`.
2. DSL de expresiones:
   la clase `E` fabrica nodos XML para constantes, variables, operadores, propiedades de craft, propiedades planetarias y vectores.
3. Utilidades:
   lectura, listado, validacion y extraccion de programas embebidos en crafts.

### 2.1 Builder

`VizzyProgram` encapsula:

- declaracion de variables con `var(...)`
- eventos como `on_start()`
- instrucciones de control (`while_loop`, `if_block`, `for_loop`)
- control de nave (`set_input`, `set_pitch`, `set_heading`, `lock_heading`, `activate_stage`)
- persistencia con `save()`

El builder autogestiona:

- IDs de bloques
- posiciones visuales del canvas
- serializacion XML

### 2.2 DSL `E`

`E` es el punto clave para generar Vizzy sin abrir el editor:

- constantes: `num`, `text`, `TRUE`, `FALSE`
- variables: `var`, `local_var`, `list_var`
- propiedades: `prop`, `planet_prop`, `part_prop`, `craft_prop`
- matematica: `add`, `sub`, `mul`, `div`, `pow`, `min2`, `max2`, `math`
- logica: `eq`, `lt`, `gt`, `and_`, `or_`, `not_`, `cond`
- vectores: `vec`, `vec1`, `vec2`

Esto permite construir programas autopilotados con formulas orbitales sin editar XML a mano.

### 2.3 Validacion

La validacion incorporada comprueba:

- XML bien formado
- presencia de `Variables` e `Instructions`
- ausencia de IDs duplicados
- propiedades invalidas conocidas

Es importante porque Juno falla de forma bastante fragil con XML ligeramente incorrecto.

## 3. Reglas criticas de compatibilidad detectadas

Del `README.md` y del codigo salen varias restricciones importantes:

- Los archivos deben escribirse con UTF-8 BOM (`utf-8-sig`).
- Las propiedades planetarias no usan `CraftProperty style="planet"` sino nodos `<Planet op="...">`.
- `Orbit.Planet` es la propiedad correcta para el nombre del planeta actual.
- La estructura del programa debe incluir `Variables`, `Instructions` y normalmente `Expressions`.

Estas reglas son materialmente importantes. Un XML "casi correcto" puede cargar vacio o romper el programa en juego.

## 4. Que aporta el ejemplo grande

`Universal Vizzy Mission 2 - Enhanced.xml` demuestra que el formato generado por la herramienta soporta:

- instrucciones custom
- solucion numerica tipo RK4
- calculos de anomalia universal
- heading/azimuth dinamico
- transferencias, encuentros y logica orbital compleja

Para la tarea pedida no conviene reutilizarlo entero porque:

- es demasiado grande
- mezcla navegacion interplanetaria con lanzamiento
- aumenta mucho la superficie de error

Lo util del ejemplo para esta tarea es confirmar que el juego y el builder soportan:

- calculo de rotacion planetaria con `Planet day`
- guiado por `SetTargetHeading`
- uso intensivo de `Orbit.Apoapsis`, `Orbit.Periapsis`, `Vel.OrbitVelocity`
- custom instructions para encapsular logica

## 5. Diseno del autopiloto 200 km

Se ha generado un programa nuevo y mas corto en `generate_universal_200km_orbit.py`.

Objetivo del programa:

- cuenta atras de 5 segundos
- despegue automatico
- ascenso orbital progrado
- objetivo de apoapsis 200 km
- costa hasta apoapsis
- circularizacion hasta periapsis 200 km

### 5.1 Filosofia

En vez de intentar modelar todo el lanzamiento con un solver complejo, el nuevo Vizzy usa un enfoque mas robusto para "muchos cohetes":

- gravity turn por progresion de altura
- control de throttle segun error de apoapsis
- autostaging basico
- circularizacion cerrando el error de periapsis

Esto no garantiza exito matematico para cualquier vehiculo imposible, pero si es una estrategia razonable y portable para cohetes con:

- TWR inicial suficiente para despegar
- delta-v suficiente para orbitar
- staging convencional

## 6. Calculos fisicos usados

### 6.1 Parametro gravitacional

Se calcula:

`mu = G * M`

donde:

- `G = 6.67430e-11`
- `M = planet.mass`

### 6.2 Velocidad circular

Para un radio orbital `r`:

`v_circular = sqrt(mu / r)`

Se usa:

- durante la preparacion de la circularizacion
- durante el quemado final para comparar con la velocidad orbital actual

### 6.3 Velocidad requerida en apoapsis para circularizar

Partiendo de apoapsis `ra` y periapsis `rp`:

- `a = (ra + rp) / 2`
- `v_apo = sqrt(mu * (2/ra - 1/a))`
- `dv_circularize = sqrt(mu / ra) - v_apo`

Esto permite estimar el delta-v de la maniobra final.

### 6.4 Tiempo de inicio del quemado de circularizacion

El tiempo se estima de forma pragmatica:

`burn_time_est = BurnTime * clamp(dv / StageDeltaV, 0, 1)`

y luego:

`burn_lead = max(3, burn_time_est / 2)`

No es una solucion exacta tipo ecuacion del cohete, pero usa propiedades confirmadas disponibles en Vizzy y evita depender de funciones no documentadas del evaluador inline.

## 7. Como se adapta a distintos cohetes

La universalidad buscada viene de tres decisiones:

1. Los parametros del planeta se leen en runtime:
   radio, masa, altura de atmosfera y sentido de rotacion.
2. El gravity turn es dinamico:
   `TurnStart` y `TurnEnd` dependen de atmosfera y objetivo orbital.
3. El control de potencia no es fijo:
   se modula por error de apoapsis y luego por error de periapsis/delta-v.

Ademas:

- el heading objetivo se pone a 90 o 270 segun el signo del dia planetario
- el staging se intenta automaticamente cuando baja el thrust o se vacia el stage actual

## 8. Limites tecnicos honestos

Hay que dejar claro lo siguiente:

- Ningun autopiloto puede ser literalmente universal para cualquier cohete si el vehiculo no tiene rendimiento suficiente.
- Cohetes extremadamente inestables, con TWR marginal o staging exotico pueden necesitar ajustes.
- La estimacion del tiempo de circularizacion es aproximada, aunque la correccion por error de periapsis cierra bien la maniobra final.

## 9. Archivos generados para esta tarea

- `generate_universal_200km_orbit.py`: generador del nuevo programa.
- `FlightPrograms/Universal Orbit 200km - Auto.xml`: XML Vizzy listo para cargar tras ejecutar el script.

## 10. Flujo recomendado de uso

1. Ejecutar:
   `python generate_universal_200km_orbit.py`
2. Validar:
   `python vizzy_tool.py validate "Universal Orbit 200km - Auto"`
3. Cargar el programa en Juno.
4. Probar primero con un cohete convencional de 2 o 3 etapas y TWR > 1.3.

