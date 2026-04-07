# Investigacion del bug: Juno carga el XML pero el editor Vizzy aparece vacio

## Resultado

El problema principal no era el BOM ni la declaracion XML. La causa real era estructural:

- el generador estaba escribiendo los `CustomInstruction` dentro de `<Expressions>`
- Juno espera que los `CustomInstruction` vivan en bloques `<Instructions>` adicionales al nivel raiz
- `<Expressions>` debe reservarse para `CustomExpression`

Esto provocaba:

- XML parseable
- validacion local aparentemente correcta
- `NullReferenceException` interno del editor Vizzy al intentar reconstruir los nodos

## Evidencia recogida

### 1. El archivo tenia BOM correcto

Se verifico que el XML generado empezaba por:

- `EF BB BF`

Esto descarta el bug clasico de archivo vacio por falta de BOM.

### 2. La declaracion XML no era el problema

Se comparo contra archivos originales de `UserData/FlightPrograms` y varios tambien empiezan con:

- `<?xml version="1.0" encoding="utf-8"?>`

Por tanto, la cabecera XML no explica el fallo.

### 3. `Player.log` mostro un fallo del editor, no del parser XML

En `Player.log` aparecio:

```text
NullReferenceException: Object reference not set to an instance of an object
at Assets.Scripts.Vizzy.UI.VizzyUIScript.LoadFlightProgram
```

Eso indica que:

- el XML se abre
- pero el editor Vizzy no sabe reconstruir su estructura interna

### 4. Comparacion clave con un XML original valido

En el archivo original `Universal Vizzy Mission 2 - Enhanced.xml` los `CustomInstruction` estan serializados asi:

```xml
<Instructions>
  <CustomInstruction ... />
  <SetVariable ... />
  <If ... />
</Instructions>
<Instructions>
  <CustomInstruction ... />
  <For ... />
</Instructions>
<Expressions>
  <CustomExpression ... />
</Expressions>
```

En la version rota generada por la herramienta, el patron era:

```xml
<Instructions>
  ... hilo principal ...
</Instructions>
<Expressions>
  <CustomInstruction ... />
  <If ... />
  <SetVariable ... />
</Expressions>
```

Ese formato no coincide con el usado por Juno para programas editables.

## Segundo problema detectado

La herramienta asumía:

```python
USERDATA = Path(__file__).parent
```

Pero en este repo `vizzy_tool.py` esta dentro de:

- `UserData/VizzyIATools`

no dentro de:

- `UserData`

Consecuencia:

- la herramienta podia leer y escribir en `VizzyIATools/FlightPrograms`
- pero Juno usa `UserData/FlightPrograms`

Se corrigio para detectar automaticamente si el `UserData` real es el directorio padre.

## Cambios aplicados

### 1. Correccion en `vizzy_tool.py`

Se cambio la serializacion de `VizzyProgram`:

- `add_custom_instruction(...)` ya no mete esos bloques en `_expressions`
- ahora guarda cada custom instruction como un hilo propio
- `to_element()` emite:
  - un `<Instructions>` para el hilo principal
  - un `<Instructions>` extra por cada `CustomInstruction`
  - un `<Expressions>` final solo para expresiones custom

### 2. Correccion de rutas

`vizzy_tool.py` ahora detecta:

- si `FlightPrograms` y `CraftDesigns` estan en el directorio actual
- o si estan en el directorio padre

Con eso la herramienta apunta al `UserData` real del juego.

### 3. Generador con fallback si el archivo esta bloqueado

Si `Universal Orbit 200km - Auto.xml` esta bloqueado por Juno, el generador guarda:

- `Universal Orbit 200km - Auto FIXED.xml`

Esto evita que el archivo viejo roto impida escribir la version corregida.

## Estado despues del arreglo

La estructura correcta del programa nuevo queda asi:

- `Variables`
- `Instructions` principal
- `Instructions` para `Auto Stage`
- `Instructions` para `Update Orbit State`
- `Expressions` vacio

Ese patron coincide con los XML originales de Juno que usan `CustomInstruction`.

## Conclusiones

Los dos fallos reales eran:

1. Serializacion incorrecta de `CustomInstruction`
2. Resolucion incorrecta de la carpeta `UserData`

El primer fallo rompe el editor Vizzy aunque el XML sea parseable.
El segundo provoca confusion porque la herramienta puede escribir una copia en una carpeta que el juego no usa.

## Siguiente paso practico

Ejecutar:

```bash
python generate_universal_200km_orbit.py
```

Y en Juno abrir:

- `Universal Orbit 200km - Auto FIXED.xml` si el archivo antiguo seguia bloqueado
- o `Universal Orbit 200km - Auto.xml` si pudo sobrescribirse

