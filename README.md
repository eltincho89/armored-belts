# Cintas Transportadoras Blindadas (`armored-belts`)

Mod para **Factorio 2.0** (compatible con Space Age). Rama lateral blindada de la
línea exprés, pensada para zonas de combate frontal contra Biters.

- **Versión:** 0.2.1
- **Probado en:** Factorio 2.0.77 (build 84539, win64, steam, space-age)
- **Dependencias:** `base >= 2.0`

---

## 1. Qué es

Tres entidades nuevas —cinta, cinta subterránea y divisor— con **exactamente el
mismo rendimiento que las exprés** pero con blindaje pesado. No es un tier
superior de velocidad: es una variante defensiva que se elige, no una mejora que
sustituye.

| | Blindada | Exprés (vanilla) |
|---|---|---|
| Velocidad | 0.09375 | 0.09375 |
| HP cinta / subterránea | **600** | 170 |
| HP divisor | **670** | 190 |
| Resistencia fuego | **95%** | 50% |
| Resistencia explosión | **80% / −15** | ninguna |
| Resistencia física | **60% / −8** | ninguna |
| Resistencia ácido | **60% / −5** | ninguna |

Las resistencias se **fusionan** sobre las de la entidad clonada, no la
sustituyen: la subterránea exprés trae un 30% de resistencia a impacto en
vanilla y la blindada lo conserva. Por tipo gana el valor más alto, así que la
blindada nunca puede quedar peor que la exprés en nada.

### Receta y desbloqueo

Categoría `crafting` normal, **sin lubricante**: son fabricables a mano. Reparar
la línea en mitad de un ataque no debería exigir volver a la planta química.

| Receta | Ingredientes | Sale |
|---|---|---|
| Cinta blindada | 1 cinta exprés + 4 acero | 1 |
| Subterránea blindada | 2 subterráneas exprés + 10 acero | 2 |
| Divisor blindado | 1 divisor exprés + 8 acero | 1 |

Tecnología `armored-belts`: **200 × 30 s**, prerrequisitos `logistics-3` +
`military-3`, packs automation / logistic / military / chemical / production.

---

## 2. Investigación previa: ¿ya existía?

Se descargó el índice completo de la API del portal (**22.942 mods**) y se
filtró localmente. El buscador web del portal se renderiza con JS y no es
consultable por HTTP directo; el endpoint `query` de la API lo ignora y devuelve
el listado alfabético completo. De ahí el volcado + filtrado local.

**No existe ningún mod que combine un tier nuevo de cinta con resistencias de
combate.** Lo más cercano:

| Mod | Descargas | Qué hace | Por qué no cubre esto |
|---|---|---|---|
| `Invulnerable-Belts` | 129 | Todas las cintas indestructibles | Interruptor on/off, sin gradación ni coste. Factorio 1.1, abandonado |
| `biterproof` | 3,18 K | Invencibilidad por filtros de entidad | Igual: binario, no es algo que te ganes |
| `UltimateBelts` / `AdvancedBelts` / `BetterBelts` | 54 K / 21 K / 15 K | Tiers extra de cinta | **Solo velocidad.** Ninguno toca `max_health` ni `resistances` |

El nicho está libre: nadie ha tratado la cinta como **pieza de infraestructura
defensiva** en lugar de como tubo de throughput.

---

## 3. Dos hallazgos en los datos de vanilla

Leídos de `base/prototypes/entity/transport-belts.lua` de la instalación local.

### 3.1 Mejorar tus cintas las hace MÁS inflamables

```
transport-belt          150 HP    fuego 90%
fast-transport-belt     160 HP    fuego 50%   <- baja
express-transport-belt  170 HP    fuego 50%
turbo-transport-belt    170 HP    fuego 50%   (Space Age)
```

La cinta amarilla resiste el fuego al 90%. En cuanto pasas a roja cae al 50% y
ahí se queda para siempre. Además, **ninguna cinta del juego tiene resistencia a
explosión**: el campo sencillamente no existe en ningún tier.

### 3.2 Los biters no hacen daño de fuego ni de explosión

Verificado extrayendo el daño ofensivo real de `enemies.lua` y
`enemy-projectiles.lua`: los enemigos solo hacen **físico** (mordisco) y
**ácido** (escupitajo de spitter/worm). Cero fuego, cero explosión.

Consecuencia de diseño: fuego y explosión **no** protegen de los biters,
protegen de **tu propio fuego amigo** — torretas lanzallamas quemando tu línea,
artillería, cohetes, incendios de árboles. Por eso el mod lleva las cuatro
resistencias y no solo las dos que pedía la idea original.

---

## 4. Efecto real en combate

Golpes necesarios para destruir un tramo, aplicando la fórmula real del juego
`daño_final = (daño − decrease) × (1 − percent)`:

| Enemigo | Daño | Tipo | Exprés | Blindada | Factor |
|---|---|---|---|---|---|
| Wriggler pequeño / mediano | 3,75 / 5,5 | físico | 45 / 31 | **inmune** | ∞ |
| Biter pequeño | 7 | físico | 24 | **inmune** | ∞ |
| Wriggler grande | 9 | físico | 19 | 1500 | 79,4× |
| Biter mediano | 15 | físico | 11 | 214 | 18,9× |
| Biter grande | 30 | físico | 6 | 68 | 12,0× |
| Biter behemoth | 90 | físico | 2 | 18 | **9,7×** |

El `decrease = 8` de físico hace que los biters pequeños **no puedan hacerle
daño en absoluto**. Como la tecnología exige `logistics-3` + `military-3` +
ciencia de producción, para cuando la tienes los biters pequeños ya no son una
amenaza, así que en la práctica no rompe nada. Si aun así parece excesivo, bajar
`decrease` a 4 los devuelve al juego.

Contra behemoths —el número que de verdad importa— sigue siendo **~10×**.

---

## 5. Decisiones de diseño

### Rama lateral, no tier superior

Con Space Age instalado, la cinta turbo está por encima de la exprés. Hacer la
blindada más rápida que la turbo habría dejado obsoleto un tier entero de la
expansión. En su lugar:

- Misma velocidad que la exprés.
- **`next_upgrade = nil`**, así los planificadores de mejora la dejan en paz.
- **`fast_replaceable_group = "transport-belt"` conservado**, así una línea
  frontal existente se retrofitea pasándole la blindada por encima, sin
  desmontar nada.

Esas dos propiedades juntas son la clave de la ergonomía del mod: se coloca
encima de lo que ya tienes, y nada la mueve de sitio después.

### Clonado en vez de reescritura

Las tres entidades salen de `table.deepcopy` de sus equivalentes exprés. Puntos
de conexión, sonidos, timings de animación y definiciones de conector de
circuito vienen gratis y correctos. Solo se sustituyen nombre, iconos, vida,
resistencias, corpse y las rutas de sprites.

---

## 6. Gráficos: gris acero / titanio

### Por qué no bastaba un tinte

El campo `tint` de Factorio **multiplica** sobre el sprite base, y multiplicar
solo puede oscurecer canales, nunca subirlos. Partiendo de un cian saturado (R
bajo, B alto) **no existe ningún valor de tinte que produzca gris neutro**. Un
primer intento con tinte gunmetal seguía leyéndose azulado, precisamente por
esto.

### El hallazgo que simplificó todo

El análisis de los sprites reveló que **ya son mayormente gris metálico**: entre
el 44% y el 59% de los píxeles opacos tienen saturación < 0,1. Lo que los hace
azules es un acento **cian (hue ≈ 180°)** encima de metal oscuro.

Así que no hacía falta pasar nada a escala de grises —eso habría aplanado el
tread y matado la sensación de movimiento—. Bastaba **arrancar el croma y
conservar intacta la luminancia**.

### Resultado medido

| | Antes | Después |
|---|---|---|
| Saturación media | 0,159 | **0,013** |
| Píxeles con saturación > 0,3 | 11,8% | **0,1%** |
| Luminancia media | 0,277 | 0,294 *(+6%)* |
| RGB medio | (76, 68, 65) | **(74, 74, 76)** |

Neutro con un matiz frío mínimo. Acero, no azul ni gris sucio. Y el detalle
mecánico intacto, porque la luminancia nunca se tocó.

### El pipeline

`tools/recolor.py` genera **17 sprites** desde los PNG de vanilla: cinta,
subterránea (estructura + 2 patches), divisor (4 direcciones + 2 top patches),
3 iconos de item, icono de tecnología y **los 3 prototipos de restos** — sin
esto, una cinta blindada destruida dejaba chatarra azul en el suelo.

Constantes ajustables al principio del script:

```python
DESAT    = 0.92                   # 1.0 = gris totalmente neutro
CONTRAST = 0.12                   # smoothstep, mantiene el chapado nítido
LIFT     = 1.10                   # gamma de medios; el metal desnudo lee más claro
TINT     = (0.965, 0.978, 1.000)  # matiz frío mínimo -> acero, no cálido
```

Se usa **lightness HSL** `(max+min)/2` en vez de luma perceptual
`0.21/0.72/0.07`: con luma, un cian saturado colapsaría a gris oscuro y se
perdería el brillo aparente de los chevrones.

Para re-afinar el color basta con tocar las constantes y ejecutar:

```
python tools/recolor.py
```

### Sincronización a prueba de fallos

El script escribe `prototypes/graphics-map.lua` **a partir de los archivos que
realmente produjo**. El Lua remapea rutas contra ese mapa recorriendo el
prototipo clonado: una ruta que no esté en el mapa se deja intacta, y una que sí
esté existe con certeza en disco.

Consecuencia: **es imposible que un prototipo apunte a un sprite inexistente**.
Si se añade un sprite al script, el Lua lo recoge solo.

---

## 7. Bugs detectados durante el desarrollo

Los tres eran silenciosos: ninguno hacía fallar la carga.

1. **`next_upgrade` heredado.** El `deepcopy` de la exprés arrastraba
   `next_upgrade = "turbo-transport-belt"` de Space Age. Habría metido las
   cintas blindadas en la cadena de mejora automática, justo lo contrario de lo
   que se buscaba. → puesto a `nil`.

2. **Restos con icono azul.** Los prototipos `corpse` llevan su propio campo
   `icon`, independiente del de la entidad. Sin corregirlo, la entrada de
   chatarra en Factoriopedia seguía mostrando el icono cian de la exprés.
   → `corpse.icons` reasignado.

3. **`shared.tint` colgante.** Al reescribir `shared.lua` para el enfoque de
   remapeo desapareció `shared.tint`, pero `technology.lua` seguía
   referenciándolo. En Lua eso no falla: evalúa a `nil`. **El icono de
   investigación se estaba quedando azul sin tintar** y `--dump-data` pasaba sin
   una queja. → resuelto metiendo `logistics-3.png` en el propio pipeline de
   recoloreado.

4. **Resistencias sobrescritas en bloque.** Asignar `entity.resistances`
   entero descartaba lo que la entidad clonada ya traía. Las subterráneas
   exprés tienen **30% de resistencia a impacto** en vanilla, así que la
   subterránea blindada quedaba *más* frágil que la exprés frente a
   colisiones de vehículos — justo lo contrario de lo que promete una rama
   lateral blindada. Lo detectó `tools/run_tests.py`, no una lectura del
   código. → `shared.apply_resistances()` fusiona y se queda con el máximo por
   tipo de daño.

El tercero es el argumento a favor de verificar el resultado y no solo la
ausencia de errores. El cuarto lo es a favor de tener tests: nada fallaba, nada
se veía mal, y aun así el mod incumplía su propia premisa.

---

## 8. Verificación automatizada

```
python tools/run_tests.py            # todo, contra el volcado actual
python tools/run_tests.py --dump     # relanza el data stage y luego testea
python tools/run_tests.py -k balance # una sola suite
python tools/run_tests.py -v         # lista cada aserción
```

**333 aserciones en 30 tests**, cuatro suites, sin dependencias más allá de
Pillow y numpy (que ya pide `recolor.py`). No hay pytest: el harness son 133
líneas en `tools/tests/harness.py`, para que la suite corra con un `python`
pelado. Las aserciones se registran en vez de lanzar excepción, así un valor
malo reporta un fallo y no aborta el resto.

| Suite | Qué cubre |
|---|---|
| `manifest` | `info.json`, cada `require()` resuelve, claves de locale en los dos idiomas (sin huérfanas, sin duplicadas, sin español copiado del inglés), junction y activación en `mod-list.json` |
| `graphics` | los 17 sprites en ambos sentidos (nada en el mapa sin PNG, ningún PNG fuera del mapa), **el origen vanilla sigue existiendo**, dimensiones idénticas, canal alfa intacto bit a bit, y las cifras de color del §6 recalculadas |
| `data stage` | vida, velocidad, resistencias, `next_upgrade`, corpses, items, recetas, tecnología, que todo sprite referenciado existe en disco y que **vanilla queda sin tocar** |
| `balance` | daño enemigo extraído del volcado siguiendo streams y proyectiles, la tabla del §4 recalculada, y la premisa del §3 revalidada contra los datos del juego |

Dos tests merecen mención aparte porque no comprueban el mod sino sus
**supuestos**: uno verifica que el sprite exprés del que parte cada recoloreado
sigue existiendo en `base` —si Factorio lo renombra, el remapeo no falla, se
queda callado y la cinta vuelve a ser azul— y otro que ninguna cinta de vanilla
ha ganado resistencia a explosión, que es la razón de ser del mod.

La suite se validó con **mutación**: se sabotearon seis campos de una copia del
volcado (vida, `next_upgrade`, resistencias, un ingrediente, un prerrequisito y
un icono de corpse) y los seis fueron detectados, varios por más de un test.

### El data stage real

```
Factorio.exe --dump-data
```

Arranca el juego, procesa todos los prototipos de todos los mods activos,
escribe `script-output/data-raw-dump.json` y sale. Es el chequeo real del data
stage sin abrir una partida.

Sobre ese volcado de 29 MB se comprobó programáticamente:

- Valores finales de vida, velocidad, resistencias y `next_upgrade` de las tres
  entidades.
- Ingredientes, resultados y estado de las tres recetas.
- Prerrequisitos, efectos y coste de la tecnología.
- Que las 4 definiciones de icono tienen la forma esperada.
- Que **los 17 sprites referenciados existen en disco**.
- Que **no queda ni una sola referencia gráfica a la exprés** en las 6 entidades
  y corpses (solo permanecen los `.ogg`, intencionado: el sonido exprés
  corresponde a esa velocidad).

Resultado final: `exit 0`, `Factorio initialised` → `Goodbye`, cero errores,
cargando junto a Space Age y otros 30 mods.

> Nota: `--dump-icon-sprites` existe pero no escribe nada sin contexto gráfico.
> Los previews de comparación se generaron replicando en Python la matemática de
> capas de iconos de Factorio (espacio de referencia 32 px, `scale` por defecto
> `32/icon_size`, `shift` en píxeles desde el centro).

---

## 9. Estructura del proyecto

```
armored-belts/
├── info.json
├── data.lua
├── README.md
├── prototypes/
│   ├── shared.lua           resistencias, vidas, remapeo de sprites, iconos
│   ├── graphics-map.lua     GENERADO por recolor.py -- no editar a mano
│   ├── entities.lua         clonado de las 3 entidades + 3 corpses
│   ├── items.lua
│   ├── recipes.lua
│   └── technology.lua
├── locale/
│   ├── en/strings.cfg
│   └── es-ES/strings.cfg
├── graphics/
│   ├── entity/              cinta, subterránea, divisor (+ restos)
│   ├── icons/               3 iconos de item
│   └── technology/
└── tools/
    ├── recolor.py           genera graphics/ y graphics-map.lua
    ├── run_tests.py         runner; --dump relanza el data stage
    └── tests/
        ├── harness.py       registro de tests y aserciones
        ├── context.py       rutas, cargadores, fórmula de daño
        ├── test_manifest.py
        ├── test_graphics.py
        ├── test_data_stage.py
        └── test_balance.py
```

### Entorno de desarrollo

El mod vive en `C:\Users\chait\test\armored-belts` y está enlazado a la carpeta
de mods mediante un **directory junction**:

```
mklink /J "%APPDATA%\Factorio\mods\armored-belts" "C:\Users\chait\test\armored-belts"
```

Se edita en el directorio de trabajo y el juego lo ve al instante, sin copiar
nada. Activado en `mods/mod-list.json`.

---

## 10. Ideas pendientes

- **Balance:** `decrease = 8` en físico hace inmunes a los biters pequeños.
  Justificable por el momento del desbloqueo, pero bajarlo a 4 los devolvería al
  juego si se busca más tensión.
- **Space Age:** una variante blindada de la cinta turbo, para no sacrificar
  velocidad por blindaje en el endgame.
- **Placas de tungsteno** como ingrediente alternativo cuando Space Age está
  activo — más temático que el acero para blindaje.
- **Arte propio** en vez de recoloreado: remaches, chapa soldada, bordes
  desgastados. El recoloreado es sólido, pero arte original es lo que separa un
  mod que parece un reskin de uno que parece propio.
