# Reimplementación: Finanzas Personales con Grupos Opcionales

## Resumen

El modelo actual trata al `Grupo` como la unidad fundamental de toda operación financiera. Esta reimplementación invierte esa jerarquía: el usuario es la unidad base y sus finanzas son personales por defecto. Los grupos pasan a ser espacios compartidos opcionales que solo reciben datos a través de réplicas de movimientos personales.

La estrategia elegida es la **Opción B**: hacer nullable el campo `grupo` en todos los modelos financieros. `grupo IS NULL` significa contexto personal; `grupo IS NOT NULL` significa contexto grupal.

Los datos existentes son prescindibles y serán eliminados con las migraciones.

---

## 1. Cambios Funcionales

### 1.1 Flujo principal: finanzas personales

- Al ingresar a `/finances/`, el usuario ve directamente sus **propias finanzas personales**, sin necesidad de pertenecer a ningún grupo.
- Los KPIs (gasto total, ingreso total, saldo, desviación de presupuesto) se calculan sobre los movimientos del usuario con `grupo IS NULL`.
- El usuario puede agregar gastos, ingresos, conceptos y presupuesto sin haber creado ni unido ningún grupo.

### 1.2 Replicación a grupos

El flujo de registro de un **gasto personal** es un proceso de hasta 3 pasos. Los pasos 2 y 3 son opcionales y solo aparecen si el usuario los activa explícitamente.

#### Paso 1 — Datos del gasto personal

El formulario solicita: nombre, concepto, monto y detalle. Al final del formulario aparece un checkbox **"Registrar en un grupo"**. No existe el checkbox "Es compartido" en este paso.

- Si el checkbox **no está marcado**: al hacer clic en "Registrar gasto" se crea únicamente el movimiento personal y el flujo termina.
- Si el checkbox **está marcado**: al hacer clic en "Registrar gasto" se abre el Paso 2 (modal).

#### Paso 2 — Selección de grupo

Se muestra un modal con:
- **Lista desplegable** con todos los grupos activos a los que pertenece el usuario (obligatorio seleccionar uno).
- Checkbox **"Es compartido"** (opcional).
- Botón "Registrar gasto".

Comportamientos:
- Si "Es compartido" **no está marcado**: al hacer clic en "Registrar gasto" se crea el movimiento personal y se replica al grupo seleccionado. Flujo terminado.
- Si "Es compartido" **está marcado**: al hacer clic en "Registrar gasto" se abre el Paso 3.
- El checkbox "Es compartido" solo se muestra si el grupo seleccionado tiene al menos otro miembro además del usuario. Si el grupo tiene un único miembro (el propio usuario), el checkbox se oculta o se deshabilita.

#### Paso 3 — Gasto compartido

Se muestra un modal con:
- El **monto del gasto** presentado de forma visible y no editable (referencia visual para el usuario).
- **Lista desplegable** con los miembros del grupo seleccionado en el Paso 2, excluyendo al usuario actual.
- Botón "Registrar gasto".

Al hacer clic en "Registrar gasto":
1. Se crea el movimiento personal.
2. Se crea la réplica en el grupo seleccionado.
3. Se crea el `GastoCompartido` sobre la réplica, con el miembro elegido como deudor.
4. Se envían las notificaciones correspondientes.

**Alcance por acción:** cada ejecución del flujo replica el gasto a un único grupo. Si el usuario desea replicar el mismo gasto a otro grupo, puede hacerlo posteriormente desde el detalle del movimiento personal.

#### Replicación de ingresos

Para **ingresos**, el flujo también ofrece el checkbox "Registrar en un grupo" en el Paso 1. Si está marcado, se muestra el Paso 2 con la lista de grupos. No existe Paso 3 para ingresos (los ingresos no tienen gastos compartidos).

#### Comportamiento del modelo

- Por cada réplica se crea un `Movimiento` con `grupo=<grupo_seleccionado>` y se registra en `ReplicaGrupal`.
- La réplica conserva tipo, nombre, monto, detalle y fecha del movimiento personal. El concepto de la réplica es el concepto del grupo con el mismo nombre y tipo que el concepto personal, o `NULL` si no existe uno compatible.
- Las notificaciones a los miembros del grupo se envían al crear la réplica, no al crear el movimiento personal.

### 1.3 Gastos compartidos dentro de un grupo

- La opción "Es compartido" solo aparece en el Paso 2 cuando el grupo seleccionado tiene más de un miembro.
- El `GastoCompartido` se crea sobre el **movimiento réplica** (el que tiene `grupo IS NOT NULL`), nunca sobre el movimiento personal.
- Un movimiento personal nunca tiene `GastoCompartido` asociado directamente.
- Cada replicación es una acción independiente; si se quiere registrar el gasto como compartido en otro grupo, se repite el flujo desde el detalle del movimiento.

### 1.4 Creación directa en grupos bloqueada

- Ya no es posible agregar movimientos directamente a un grupo desde ninguna vista ni endpoint.
- Todos los movimientos grupales son réplicas. Cualquier intento de creación directa mediante la API devuelve `HTTP 403`.
- Los movimientos grupales existentes (réplicas) son de solo lectura desde la vista de grupo; no se pueden editar ni eliminar de forma independiente. Si se requiere corrección, debe hacerse en el movimiento personal origen, y la réplica se actualiza en consecuencia.

### 1.5 Gestión de grupos

- El usuario puede pertenecer a múltiples grupos activos simultáneamente.
- La creación de grupos sigue funcionando igual (desde la sección de grupos).
- La pertenencia a un grupo ya no es requisito para acceder a finanzas.
- El dashboard principal muestra un resumen de cada grupo al que pertenece el usuario, debajo de las finanzas personales.

### 1.6 Conceptos

- Cada usuario tiene su propio catálogo de **conceptos personales** (`grupo IS NULL, usuario=<usuario>`).
- Cada grupo tiene su propio catálogo de **conceptos grupales** (`grupo=<grupo>`).
- Los conceptos personales y grupales son independientes; un nombre puede existir en ambos contextos sin conflicto.
- Al replicar un movimiento a un grupo, si existe un concepto grupal con el mismo nombre y tipo que el concepto personal, se asigna automáticamente. Si no existe, la réplica queda sin concepto (`concepto=NULL`).
- El usuario administra sus conceptos personales desde `/finances/concepts/` y los conceptos de cada grupo desde la vista del grupo correspondiente.

### 1.7 Presupuesto

- Existe un **presupuesto personal** por usuario (`grupo IS NULL, usuario=<usuario>`).
- Cada grupo puede tener su propio presupuesto, gestionado por los miembros del grupo desde la vista de grupo.
- La desviación de presupuesto en el dashboard personal se calcula sobre el presupuesto personal vs. gastos personales.
- La desviación de presupuesto en la vista de grupo se calcula sobre el presupuesto del grupo vs. las réplicas de movimientos en ese grupo.

#### División de presupuesto

Al crear un registro de presupuesto personal, el usuario puede activar el checkbox **"Dividir presupuesto"** para especificar cómo se distribuye ese monto entre él y uno o más miembros de un grupo al que pertenece.

**Flujo:**

1. El usuario completa el formulario de presupuesto con los campos existentes (tipo, concepto, nombre, detalle, periodicidad, fecha, monto) y marca el checkbox "Dividir presupuesto".
2. Al hacer clic en "Guardar" se abre un modal de división con:
   - **Lista desplegable "Nombre del grupo"**: grupos activos a los que pertenece el usuario.
   - **Botón "Agregar usuario"**: abre un selector con los miembros del grupo elegido que aún no están en la grilla.
   - **Grilla de distribución** con columnas: `Usuario`, `Monto`, `Porcentaje`.
3. La grilla siempre tiene como **primera fila fija** al usuario actual. Sus columnas `Monto` y `Porcentaje` son de solo lectura y se autocalculan.
4. Cada fila agregada (otros usuarios) tiene `Monto` y `Porcentaje` editables. Ingresar un valor en uno autocalcula el otro para esa misma fila, y recalcula los valores del usuario actual.
5. Al hacer clic en **"Finalizar"** se guarda el registro de presupuesto junto con su división.

**Reglas de cálculo reactivo** (gestionado con Alpine.js en el frontend, verificado también en el backend):

- Sea `T` el monto total del registro de presupuesto.
- Sea `Mᵢ` el monto asignado al usuario `i` (distinto del usuario actual).
- **Al ingresar `Mᵢ`**: `Porcentajeᵢ = Mᵢ / T × 100`; `Monto_yo = T − Σ Mᵢ`; `Porcentaje_yo = Monto_yo / T × 100`.
- **Al ingresar `Porcentajeᵢ`**: `Mᵢ = T × Porcentajeᵢ / 100`; `Monto_yo = T − Σ Mᵢ`; `Porcentaje_yo = Monto_yo / T × 100`.
- Los cálculos para el usuario actual solo se realizan cuando **todos** los usuarios agregados tienen al menos un valor (`Monto` o `Porcentaje`) ingresado. Mientras falten valores en alguna fila, los campos del usuario actual se muestran vacíos.
- Si `Σ Mᵢ > T`, la fila que causó el exceso muestra un error en línea: *"El monto asignado supera el total disponible"*. El botón "Finalizar" permanece deshabilitado.

**Restricciones:**

- Solo se puede dividir un presupuesto **personal** (`grupo IS NULL`). Los presupuestos grupales no tienen división.
- Debe agregarse al menos un usuario además del usuario actual.
- El botón "Finalizar" solo se habilita cuando: todos los usuarios tienen valores, `Σ Mᵢ ≤ T`, y `Monto_yo ≥ 0`.
- Si se cambia el grupo en el dropdown, la grilla se resetea (se eliminan las filas agregadas).

**Comportamiento del modelo:**

- Se crea un registro `DivisionPresupuesto` por cada usuario en la grilla (incluyendo el usuario actual con su monto calculado).
- La suma de todos los `DivisionPresupuesto.monto` debe ser igual al `RegistroPresupuesto.monto`. Esto se valida en el servidor antes de guardar.
- El `porcentaje` no se almacena; se calcula dinámicamente como `monto / registro_presupuesto.monto × 100`.

### 1.8 Exportación CSV

- Desde el dashboard personal se exportan solo los movimientos personales.
- Desde la vista de grupo se exportan solo los movimientos de ese grupo (las réplicas).

### 1.9 Notificaciones

- Las notificaciones de tipo `TIPO_GASTO` y `TIPO_INGRESO` se envían a los miembros del grupo **solo cuando se crea una réplica**, no por el movimiento personal.
- Las notificaciones de `TIPO_GASTO_COMPARTIDO` funcionan igual que hoy, pero son disparadas por la creación de un `GastoCompartido` sobre la réplica grupal.
- El movimiento personal no genera notificaciones grupales.
- Al guardar una división de presupuesto, se envía una notificación de tipo `TIPO_PRESUPUESTO` a cada usuario incluido en la grilla (excluyendo al usuario actual), con el texto: *"[nombre_usuario] te asignó $[monto] del presupuesto '[nombre_presupuesto]' en [nombre_grupo]"*.

---

## 2. Cambios en la Base de Datos

### 2.1 Modelo `Concepto` (`finances/models.py`)

| Campo | Cambio |
|-------|--------|
| `grupo` | `null=True, blank=True` (era NOT NULL) |
| `usuario` | Nuevo campo `ForeignKey(AUTH_USER_MODEL, null=True, blank=True, on_delete=CASCADE)` |

**Regla de integridad:** exactamente uno de `usuario` o `grupo` debe estar presente. El otro debe ser `NULL`. Se implementa con una `CheckConstraint`:

```python
models.CheckConstraint(
    check=(
        Q(usuario__isnull=False, grupo__isnull=True) |
        Q(usuario__isnull=True, grupo__isnull=False)
    ),
    name='concepto_contexto_exclusivo',
)
```

**Constraint de unicidad** (reemplaza el existente):
- Para conceptos personales: `(nombre, usuario)` donde `activo=True` y `grupo IS NULL`
- Para conceptos grupales: `(nombre, grupo)` donde `activo=True` y `usuario IS NULL`

```python
models.UniqueConstraint(
    fields=['nombre', 'usuario'],
    condition=Q(activo=True, grupo__isnull=True),
    name='concepto_nombre_usuario_personal_unique',
),
models.UniqueConstraint(
    fields=['nombre', 'grupo'],
    condition=Q(activo=True, usuario__isnull=True),
    name='concepto_nombre_grupo_unique',
),
```

El constraint `conceptos_nombre_grupo_activo_unique` existente se elimina.

**Índices nuevos:**
```python
models.Index(fields=['usuario', 'tipo'], condition=Q(grupo__isnull=True), name='idx_concepto_usuario_tipo'),
```

---

### 2.2 Modelo `Movimiento` (`finances/models.py`)

| Campo | Cambio |
|-------|--------|
| `grupo` | `null=True, blank=True` (era NOT NULL) |

- `usuario` ya existe y es NOT NULL: identifica al propietario del movimiento personal.
- Cuando `grupo IS NULL` → movimiento personal.
- Cuando `grupo IS NOT NULL` → movimiento réplica (solo creado por el sistema al replicar).

**Índices modificados** (el índice `(grupo, -fecha_hora)` no cubre movimientos personales):
```python
# Reemplaza el índice (grupo, -fecha_hora)
models.Index(fields=['usuario', '-fecha_hora'], condition=Q(grupo__isnull=True), name='idx_mov_usuario_fecha'),
models.Index(fields=['grupo', '-fecha_hora'], condition=Q(grupo__isnull=False), name='idx_mov_grupo_fecha'),
# Reemplaza el índice (grupo, tipo)
models.Index(fields=['usuario', 'tipo'], condition=Q(grupo__isnull=True), name='idx_mov_usuario_tipo'),
models.Index(fields=['grupo', 'tipo'], condition=Q(grupo__isnull=False), name='idx_mov_grupo_tipo'),
```

**CheckConstraint:** un movimiento réplica no puede ser marcado como compartido directamente (la integridad se gestiona desde la vista, no con una constraint de DB).

---

### 2.3 Modelo `RegistroPresupuesto` (`finances/models.py`)

| Campo | Cambio |
|-------|--------|
| `grupo` | `null=True, blank=True` (era NOT NULL) |
| `usuario` | Nuevo campo `ForeignKey(AUTH_USER_MODEL, null=True, blank=True, on_delete=CASCADE)` |

Misma regla de integridad que `Concepto`: exactamente uno entre `usuario` y `grupo` debe estar presente.

```python
models.CheckConstraint(
    check=(
        Q(usuario__isnull=False, grupo__isnull=True) |
        Q(usuario__isnull=True, grupo__isnull=False)
    ),
    name='presupuesto_contexto_exclusivo',
)
```

El campo `concepto` en `RegistroPresupuesto` debe respetar el contexto: si el presupuesto es personal, el concepto debe ser personal del mismo usuario; si es grupal, el concepto debe ser del mismo grupo. Esto se valida en la capa de vista/serializer.

---

### 2.4 Modelo `GastoCompartido` (`finances/models.py`)

Sin cambios de esquema. El campo `grupo` permanece NOT NULL porque los gastos compartidos solo existen en el contexto grupal (sobre movimientos réplica). Esto es un invariante del dominio.

Se agrega una `CheckConstraint` para asegurar que el `movimiento` referenciado sea siempre un movimiento grupal:

```python
# Validado en capa de negocio; documentado aquí como invariante
# movimiento.grupo IS NOT NULL cuando existe un GastoCompartido
```

---

### 2.5 Nuevo modelo `ReplicaGrupal` (`finances/models.py`)

Registra la relación entre un movimiento personal y su espejo en un grupo.

```python
class ReplicaGrupal(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    movimiento_personal = models.ForeignKey(
        Movimiento,
        on_delete=models.CASCADE,
        related_name='replicas',
    )
    movimiento_grupo = models.ForeignKey(
        Movimiento,
        on_delete=models.CASCADE,
        related_name='origen_replica',
    )
    grupo = models.ForeignKey(
        'groups.Grupo',
        on_delete=models.CASCADE,
        related_name='replicas',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'replicas_grupales'
        unique_together = ('movimiento_personal', 'grupo')

    def __str__(self):
        return f"Réplica de {self.movimiento_personal_id} en {self.grupo.nombre}"
```

**Invariantes:**
- `movimiento_personal.grupo` debe ser `NULL`.
- `movimiento_grupo.grupo` debe ser igual a `self.grupo` (NOT NULL).
- `unique_together('movimiento_personal', 'grupo')`: un movimiento personal tiene como máximo una réplica por grupo.

---

### 2.6 Nuevo modelo `DivisionPresupuesto` (`finances/models.py`)

Registra cómo se distribuye el monto de un `RegistroPresupuesto` personal entre el usuario propietario y miembros de un grupo.

```python
class DivisionPresupuesto(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    registro_presupuesto = models.ForeignKey(
        RegistroPresupuesto,
        on_delete=models.CASCADE,
        related_name='divisiones',
    )
    grupo = models.ForeignKey(
        'groups.Grupo',
        on_delete=models.CASCADE,
        related_name='divisiones_presupuesto',
    )
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='divisiones_presupuesto',
    )
    monto = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'divisiones_presupuesto'
        unique_together = ('registro_presupuesto', 'usuario')

    def __str__(self):
        return f"{self.usuario.username}: ${self.monto:,} de {self.registro_presupuesto.nombre}"

    @property
    def porcentaje(self):
        total = self.registro_presupuesto.monto
        return round(self.monto / total * 100, 2) if total else 0
```

**Invariantes:**
- `registro_presupuesto.grupo` debe ser `NULL` (solo presupuestos personales pueden dividirse).
- `usuario` debe ser miembro activo de `grupo`. Se valida en la vista antes de crear el registro.
- La suma de todos los `DivisionPresupuesto.monto` para un mismo `registro_presupuesto` debe ser igual a `registro_presupuesto.monto`. Se valida en la capa de negocio antes del `bulk_create`.
- `unique_together('registro_presupuesto', 'usuario')`: un usuario aparece como máximo una vez por división.
- Siempre existe una fila donde `usuario == registro_presupuesto.usuario` (el propietario del presupuesto).

**Índice:**
```python
models.Index(fields=['registro_presupuesto'], name='idx_division_presupuesto'),
models.Index(fields=['usuario', 'grupo'], name='idx_division_usuario_grupo'),
```

---

### 2.7 Migración

Dado que los datos existentes son prescindibles, la migración consiste en:

1. Eliminar todas las tablas financieras existentes (`movimientos`, `conceptos`, `presupuesto`, `gastos_compartidos`) con `manage.py flush` o eliminando las migraciones previas.
2. Hacer squash de las migraciones `0001` a `0007` en una única migración inicial limpia que refleje el esquema nuevo.
3. Crear `0001_initial_v2.py` con el esquema completo descrito en esta sección.

---

## 3. Cambios en Arquitectura

### 3.1 Eliminación del helper `_get_grupo`

Los helpers `_get_grupo(user)` y `_require_group(request)` en `web_views.py` se eliminan completamente. No existe más la dependencia de grupo para acceder a finanzas.

**Reemplazados por:**

```python
def _get_grupos_usuario(user):
    """Retorna todos los grupos activos a los que pertenece el usuario."""
    return (
        GrupoMiembro.objects
        .filter(usuario=user, grupo__activo=True)
        .select_related('grupo')
    )
```

### 3.2 Vistas web (`web_views.py`)

#### `dashboard_view`
- Elimina llamada a `_require_group`.
- Filtra movimientos con `usuario=request.user, grupo__isnull=True`.
- Filtra presupuesto con `usuario=request.user, grupo__isnull=True`.
- Agrega `grupos_usuario` al contexto: lista de grupos con un resumen de gastos del mes (suma de réplicas de ese usuario en ese grupo).
- El template puede renderizar una sección colapsable por grupo debajo de los KPIs personales.

#### `budget_view`
- Filtra por `usuario=request.user, grupo__isnull=True` en GET y POST.
- Al crear `RegistroPresupuesto`, asigna `usuario=request.user, grupo=None`.
- El concepto seleccionable solo muestra conceptos personales del usuario.
- Agrega al contexto GET: `grupos_usuario` (para el dropdown del modal de división) y `miembros_por_grupo` (diccionario `{grupo_id: [{id, username}, ...]}` con todos los miembros de cada grupo, excluyendo al usuario actual). Esta información alimenta la lógica reactiva del modal en el frontend.

**Lógica adicional en `action='add'`** cuando `dividir_presupuesto=1`:

| Campo POST | Descripción | Obligatorio |
|---|---|---|
| `dividir_presupuesto` | Checkbox activado | No |
| `grupo_division_id` | UUID del grupo para la división | Si `dividir_presupuesto=1` |
| `divisiones[][usuario_id]` | Lista de IDs de usuarios (sin el usuario actual) | Si `dividir_presupuesto=1` |
| `divisiones[][monto]` | Lista de montos por usuario | Si `dividir_presupuesto=1` |

Procesamiento:
1. Crea el `RegistroPresupuesto` con `usuario=request.user, grupo=None`.
2. Si `dividir_presupuesto=1`:
   - Verifica que el usuario sea miembro activo de `grupo_division_id`.
   - Verifica que cada `usuario_id` de la lista sea miembro activo del grupo.
   - Calcula `monto_propietario = registro.monto − Σ monto_otros`. Valida que `monto_propietario ≥ 0`.
   - Valida que `Σ monto_otros + monto_propietario == registro.monto`.
   - Crea los registros `DivisionPresupuesto` mediante `bulk_create`, incluyendo una fila para el propietario con `monto_propietario`.
   - Envía notificación de tipo `TIPO_PRESUPUESTO` a cada usuario del listado (excluyendo al propietario).
3. Si alguna validación falla, no se crea ni el `RegistroPresupuesto` ni las divisiones (operación atómica con `transaction.atomic()`).

#### `concepts_view`
- Filtra por `usuario=request.user, grupo__isnull=True`.
- Al crear `Concepto`, asigna `usuario=request.user, grupo=None`.
- La constraint de unicidad se evalúa sobre `(nombre, usuario)`.

#### `movements_view`
- Filtra por `usuario=request.user, grupo__isnull=True`.
- El filtro por concepto solo aplica sobre conceptos personales del usuario.

#### `movement_detail_view`
- Busca el movimiento con `id=movement_id`. Verifica propiedad: si `grupo IS NULL` → `usuario=request.user`; si `grupo IS NOT NULL` → el usuario debe ser miembro del grupo mediante `GrupoMiembro`.

#### `export_csv_view`
- Filtra por `usuario=request.user, grupo__isnull=True`.

#### `add_movement_view` (rediseño completo)

Recibe un único POST con todos los datos de los pasos completados. Los campos del formulario son:

| Campo POST | Origen | Obligatorio |
|---|---|---|
| `tipo` | Paso 1 | Sí |
| `nombre` | Paso 1 | Sí |
| `concepto` | Paso 1 | No |
| `monto` | Paso 1 | Sí |
| `detalle` | Paso 1 | No |
| `registrar_en_grupo` | Paso 1 checkbox | No |
| `grupo_id` | Paso 2 dropdown | Solo si `registrar_en_grupo=1` |
| `es_compartido` | Paso 2 checkbox | No |
| `usuario_deudor` | Paso 3 dropdown | Solo si `es_compartido=1` |

Lógica de procesamiento:
1. Crea el movimiento personal: `usuario=request.user, grupo=None`.
2. Si `registrar_en_grupo=1`:
   - Verifica que el usuario sea miembro activo de `grupo_id`.
   - Busca el concepto grupal equivalente (mismo nombre y tipo) o usa `None`.
   - Crea `Movimiento(tipo, nombre, detalle, monto, concepto=concepto_grupal, usuario=request.user, grupo=grupo, fecha_hora=...)`.
   - Crea `ReplicaGrupal(movimiento_personal=mov_personal, movimiento_grupo=mov_grupo, grupo=grupo)`.
   - Envía notificaciones de grupo para la réplica.
   - Si `es_compartido=1`:
     - Verifica que `usuario_deudor` sea miembro del grupo.
     - Crea `GastoCompartido` sobre el movimiento réplica.
     - Envía notificación directa al deudor.

#### `gastos_compartidos_view`
- La consulta cambia de filtrar por `grupo=grupo` (grupo único activo) a filtrar por todos los grupos del usuario:
  ```python
  grupos_ids = _get_grupos_usuario(request.user).values_list('grupo_id', flat=True)
  pendientes_pago = GastoCompartido.objects.filter(
      usuario_deudor=request.user, grupo_id__in=grupos_ids, pagado=False
  )
  ```
- Se agrega el nombre del grupo en el listado para diferenciarlo cuando hay múltiples grupos.

#### Nueva vista: `group_finances_view(request, group_id)`
- URL: `/finances/groups/<uuid:group_id>/`
- Verifica que el usuario sea miembro del grupo.
- Muestra KPIs del grupo: suma de `Movimiento` donde `grupo_id=group_id`.
- Lista las últimas réplicas en ese grupo.
- No permite agregar movimientos directamente; muestra un mensaje explicativo y un enlace al dashboard personal.

### 3.3 API REST (`views.py` y `urls.py`)

#### Endpoints existentes bajo `/groups/<group_id>/`

| Endpoint | Cambio |
|----------|--------|
| `GET /groups/<id>/movements/` | Sin cambio. Lee movimientos del grupo. |
| `POST /groups/<id>/movements/` | **Eliminado / retorna `HTTP 405 Method Not Allowed`**. Los movimientos grupales solo se crean por replicación. |
| `GET /groups/<id>/movements/<id>/` | Sin cambio. |
| `GET /groups/<id>/concepts/` | Sin cambio. Lee conceptos del grupo. |
| `POST /groups/<id>/concepts/` | Sin cambio. Los conceptos grupales se crean directamente en el grupo. |
| `PUT/DELETE /groups/<id>/concepts/<id>/` | Sin cambio. |
| `GET /groups/<id>/finances/dashboard/` | Sin cambio. Opera sobre réplicas del grupo. |
| `GET/POST /groups/<id>/budget/` | Sin cambio. Opera sobre presupuesto del grupo. |
| `PATCH/DELETE /groups/<id>/budget/<id>/` | Sin cambio. |

#### Nuevos endpoints bajo `/personal/`

```
GET  /personal/dashboard/            → FinanciasDashboardPersonalView
GET  /personal/movements/            → MovimientoPersonalListView
POST /personal/movements/            → MovimientoPersonalListView (crea + réplicas)
GET  /personal/movements/<id>/       → MovimientoPersonalDetailView
POST /personal/movements/<id>/replicate/  → ReplicarMovimientoView
GET  /personal/concepts/             → ConceptoPersonalListCreateView
POST /personal/concepts/             → ConceptoPersonalListCreateView
PUT/DELETE /personal/concepts/<id>/  → ConceptoPersonalDetailView
GET  /personal/budget/               → PresupuestoPersonalListCreateView
POST /personal/budget/               → PresupuestoPersonalListCreateView
PATCH/DELETE /personal/budget/<id>/  → PresupuestoPersonalDetailView
GET  /personal/export/               → ExportMovimientosPersonalView
```

#### Permisos en nuevos endpoints

- Todos requieren `IsAuthenticated`.
- Todas las queries usan `usuario=request.user, grupo__isnull=True`.
- No se requiere `IsGroupMember` para endpoints personales.

#### Nuevo endpoint de replicación

`POST /personal/movements/<id>/replicate/`

Replica un movimiento personal existente a un único grupo. Si se desea replicar al mismo movimiento a un segundo grupo, se llama al endpoint nuevamente con ese grupo.

Body:
```json
{
  "grupo_id": "<group_uuid>",
  "es_compartido": false,
  "usuario_deudor_id": "<user_id>"
}
```

- `grupo_id`: obligatorio.
- `es_compartido`: opcional, default `false`.
- `usuario_deudor_id`: obligatorio solo si `es_compartido=true`.

Validaciones:
- `movement_id` debe pertenecer al usuario (`usuario=request.user, grupo IS NULL`).
- El usuario debe ser miembro activo del `grupo_id`.
- No debe existir ya una `ReplicaGrupal` para el par `(movimiento, grupo)` — retorna `HTTP 409 Conflict` si ya fue replicado.
- Si `es_compartido=true`, `usuario_deudor_id` debe ser miembro del grupo y distinto al usuario actual.

Retorna la réplica creada con su ID y, si aplica, el `GastoCompartido` creado.

### 3.4 Serializers (`serializers.py`)

- `ConceptoSerializer`: sin cambio estructural; el campo `grupo` se vuelve de solo lectura y puede ser `null`.
- `MovimientoSerializer`: agrega campo `es_replica` (bool, `SerializerMethodField` que verifica `origen_replica.exists()`).
- `MovimientoCreateSerializer`: elimina el campo `grupo` (se asigna siempre `None` en personal o automáticamente en réplica).
- Nuevo `ReplicaGrupalSerializer`: expone `grupo_nombre`, `movimiento_grupo_id`, `created_at`.
- `RegistroPresupuestoSerializer`: el campo `grupo` puede ser `null`; agrega campo `usuario_username`; agrega campo `divisiones` (`DivisionPresupuestoSerializer` anidado, `many=True`, `read_only=True`).
- Nuevo `DivisionPresupuestoSerializer`: expone `usuario_id`, `usuario_username`, `monto`, `porcentaje` (calculado), `grupo_nombre`.

### 3.5 Templates

#### `dashboard.html`
- Elimina la referencia al nombre de grupo en el header; reemplazar por "Mis Finanzas".
- Los KPIs operan sobre el contexto personal.
- Agrega sección "Mis grupos" debajo del gráfico: una tarjeta por grupo con gasto total del mes en ese grupo.
- El modal de **"Añadir Gasto"** implementa el flujo de 3 pasos gestionado con Alpine.js:

  **Paso 1 — Datos del gasto:**
  - Campos: nombre (text), concepto (select), monto (number), detalle (textarea).
  - Checkbox **"Registrar en un grupo"** al final. Solo se muestra si el usuario pertenece a al menos un grupo (la vista pasa `grupos_usuario` al contexto).
  - Botón "Registrar gasto": si el checkbox no está marcado envía el formulario; si está marcado avanza al Paso 2 sin enviar.

  **Paso 2 — Selección de grupo (modal sobre modal o panel de reemplazo):**
  - `<select>` con los grupos del usuario (generado desde `grupos_usuario` en el contexto).
  - Checkbox **"Es compartido"**. Se muestra siempre pero se deshabilita si el grupo seleccionado no tiene otros miembros (validación reactiva en Alpine.js: `otros_miembros[grupo_id].length === 0`).
  - Botón "Registrar gasto": si "Es compartido" no está marcado envía el formulario con `registrar_en_grupo=1` y `grupo_id`; si está marcado avanza al Paso 3.

  **Paso 3 — Gasto compartido:**
  - Muestra el monto (no editable, texto estático formateado en CLP).
  - `<select>` con los miembros del grupo seleccionado en el Paso 2, excluyendo al usuario actual. La lista se actualiza reactivamente cuando cambia el grupo en el Paso 2.
  - Botón "Registrar gasto": envía el formulario completo con `registrar_en_grupo=1`, `grupo_id`, `es_compartido=1`, `usuario_deudor`.

- El modal de **"Añadir Ingreso"** también ofrece el checkbox "Registrar en un grupo" y Paso 2, pero **no tiene Paso 3** (los ingresos no tienen gastos compartidos).
- El estado interno de Alpine.js debe incluir: `paso` (1/2/3), `registrar_en_grupo` (bool), `grupo_id_seleccionado` (string), `es_compartido` (bool), `usuario_deudor_id` (string).

#### `concepts.html`
- Título cambia a "Mis Conceptos".
- El filtro `grupo=grupo` en las queries se reemplaza por `usuario=request.user, grupo__isnull=True`.
- Se elimina la referencia al objeto `grupo` en el contexto.

#### `budget.html`
- Título cambia a "Mi Presupuesto".
- El filtro de queries usa `usuario=request.user, grupo__isnull=True`.
- Se elimina la referencia al objeto `grupo` en el contexto.
- El formulario de agregar registro incluye el checkbox **"Dividir presupuesto"** al final, visible solo si `grupos_usuario` no está vacío.
- Si el checkbox está marcado, al hacer clic en "Guardar" se abre un **modal de división** gestionado con Alpine.js:

  **Estado Alpine.js necesario:**
  ```
  dividir: bool, grupoSeleccionado: string, miembrosDisponibles: [],
  filas: [{usuario_id, username, monto, porcentaje, error}], montoTotal: int
  ```

  **Modal — estructura:**
  - `<select>` "Nombre del grupo": carga desde `grupos_usuario` pasado en el contexto. Al cambiar, actualiza `miembrosDisponibles` (desde `miembros_por_grupo[grupoSeleccionado]`) y limpia `filas`.
  - **Primera fila fija (usuario actual):** muestra el username con campos `Monto` y `Porcentaje` con atributo `disabled` y valores calculados reactivamente.
  - **Filas agregadas:** cada una tiene un `<span>` con el username del usuario, un `<input type="number">` para `Monto` y otro para `Porcentaje`. Son mutuamente reactivos: editar uno recalcula el otro usando Alpine.js watchers.
  - **Botón "Agregar usuario":** abre un `<select>` temporal (o inline) con `miembrosDisponibles` filtrado para excluir usuarios ya en `filas`. Al seleccionar, agrega una nueva fila a `filas` con valores vacíos.
  - **Validaciones en tiempo real:** si la suma de montos de filas agregadas supera `montoTotal`, la fila causante muestra un mensaje de error en línea y el botón "Finalizar" se deshabilita. El botón "Finalizar" también permanece deshabilitado si alguna fila agregada tiene `monto === null`.
  - **Botón "Finalizar":** envía el formulario original enriquecido con los campos ocultos `grupo_division_id`, `divisiones[][usuario_id]` y `divisiones[][monto]` para cada fila agregada.

  **Regla de visualización del monto del propietario:**
  Los campos del propietario (primera fila) solo muestran valores cuando todos los usuarios agregados tienen un monto definido. Mientras haya filas sin valor, los campos del propietario muestran `—`.

#### `movements.html`
- Filtra por movimientos personales del usuario.
- Columna "Usuario" se puede omitir (todos son del mismo usuario).

#### `movement_detail.html`
- Si el movimiento tiene réplicas (`movimiento.replicas.exists()`), muestra una sección "Replicado en grupos" con los nombres de los grupos y el estado de gastos compartidos.

#### `shared_expenses.html`
- Agrega columna "Grupo" en ambas listas (lo que debo / lo que me deben) para cuando hay múltiples grupos.

#### Nueva plantilla: `group_finances.html`
- Vista de finanzas de un grupo específico.
- Header con nombre del grupo y enlace "Volver a mis finanzas".
- KPIs: gasto total del grupo, ingreso total del grupo, saldo.
- Tabla de últimas réplicas en el grupo.
- Botón de exportar CSV del grupo.
- Enlace a presupuesto grupal y conceptos del grupo.
- Mensaje informativo: "Los movimientos de este grupo son réplicas de finanzas personales de los miembros."

---

## 4. Cambios No Funcionales

### 4.1 Performance

- Los nuevos índices condicionales sobre `(usuario, tipo)` y `(usuario, -fecha_hora)` para movimientos personales evitan full scans cuando `grupo IS NULL`.
- La eliminación del join implícito con `Grupo` en las queries personales reduce la complejidad de cada consulta al dashboard.
- El nuevo índice en `ReplicaGrupal(movimiento_personal)` permite encontrar rápidamente todas las réplicas de un movimiento.

### 4.2 Mantenibilidad

- El helper `_get_grupo()` y su lógica de "exactamente un grupo activo" era frágil y generaba errores silenciosos cuando un usuario no tenía grupo. Al eliminarlo, el código de vista se vuelve más explícito.
- Los dos contextos (personal y grupal) están ahora claramente separados por `grupo IS NULL` vs `grupo IS NOT NULL`, haciendo las queries auto-documentadas.
- La `CheckConstraint` en `Concepto` y `RegistroPresupuesto` hace que el invariante "personal XOR grupal" sea detectado en la base de datos, no solo en la aplicación.

### 4.3 Escalabilidad

- Un usuario puede pertenecer a N grupos sin restricción. La lógica de `_get_grupo()` que asumía exactamente uno desaparece.
- El modelo `ReplicaGrupal` permite agregar en el futuro metadatos de replicación (ej. porcentaje de participación por miembro, estado de sincronización) sin modificar `Movimiento`.

### 4.4 Experiencia de usuario

- El usuario no necesita crear ni unirse a un grupo para empezar a registrar sus finanzas. La fricción de onboarding se reduce.
- La separación explícita entre finanzas personales y grupales elimina la ambigüedad de "¿este gasto es mío o del grupo?".
- El flujo de replicación hace consciente al usuario de que está compartiendo información, en lugar de que todo sea automáticamente visible para el grupo.

---

## 5. Cambios en Seguridad

### 5.1 Aislamiento de datos personales

- Todo acceso a `Movimiento`, `Concepto` y `RegistroPresupuesto` en contexto personal **debe** incluir el filtro `usuario=request.user` en la query. Este es el mecanismo de autorización principal para datos personales.
- No existe verificación de membresía de grupo para datos personales; el propietario es siempre `usuario`.
- El `movement_detail_view` y el `MovimientoPersonalDetailView` deben verificar `usuario=request.user` antes de devolver el objeto, retornando `HTTP 404` si no coincide (no `HTTP 403`, para no confirmar la existencia del recurso).

### 5.2 Autorización de réplicas

- Al crear una réplica (`add_movement_view` o `ReplicarMovimientoView`), se verifica que el usuario sea miembro activo del grupo destino mediante `GrupoMiembro.objects.filter(usuario=request.user, grupo_id=grupo_id, grupo__activo=True).exists()`. Si la verificación falla, se retorna error sin crear ningún registro (la operación es atómica: o se crea todo o nada).
- Un usuario no puede replicar un movimiento que no le pertenece. El endpoint `POST /personal/movements/<id>/replicate/` valida `movimiento.usuario=request.user` y `movimiento.grupo IS NULL`.

### 5.3 Bloqueo de creación directa en grupos

- `POST /groups/<group_id>/movements/` retorna `HTTP 405 Method Not Allowed` con body:
  ```json
  {"detail": "Los movimientos grupales solo pueden crearse mediante replicación de un movimiento personal."}
  ```
- Este bloqueo se aplica también en `add_movement_view` del lado web: si alguien manipula el formulario para enviar `grupo_id` sin pasar por el flujo de replicación, el servidor ignora el campo y crea el movimiento como personal.

### 5.4 Gastos compartidos

- `GastoCompartido` solo puede crearse si el `movimiento` referenciado tiene `grupo IS NOT NULL` (es una réplica). Se valida en `add_movement_view` y en cualquier endpoint que cree `GastoCompartido`.
- El `usuario_deudor` debe ser miembro del grupo al que pertenece el movimiento. Se verifica con `GrupoMiembro` antes de crear el registro.
- Solo el `usuario_acreedor` puede marcar un `GastoCompartido` como pagado (comportamiento existente, sin cambio).

### 5.5 Presupuesto grupal

- El presupuesto grupal (`grupo IS NOT NULL`) solo puede ser modificado por miembros del grupo (`IsGroupMember`). Sin cambio respecto al comportamiento actual.
- El presupuesto personal (`grupo IS NULL`) solo puede ser modificado por su propietario (`usuario=request.user`). Verificado con el mismo patrón de aislamiento del §5.1.

### 5.6 División de presupuesto

- Solo el propietario del `RegistroPresupuesto` puede crear, ver o eliminar sus divisiones. Las queries de `DivisionPresupuesto` siempre incluyen `registro_presupuesto__usuario=request.user`.
- Los usuarios listados en la división (los deudores) solo pueden ver su propia fila de `DivisionPresupuesto`; no pueden ver las asignaciones de otros miembros del mismo presupuesto. Sus filas se exponen únicamente a través de la notificación recibida y, si se implementa, una vista de "presupuestos que me afectan".
- La validación de membresía de grupo (`GrupoMiembro`) se realiza en el servidor para cada `usuario_id` recibido en `divisiones[]`, independientemente de lo que el frontend envíe. Un usuario no puede asignar una división a alguien que no pertenezca al grupo seleccionado.
- La operación de creación de división está envuelta en `transaction.atomic()`: si cualquier validación falla (suma incorrecta, usuario no miembro, grupo inactivo), no se persiste ningún registro.

### 5.6 Exposición de datos en templates

- El contexto de `dashboard_view` no debe incluir datos de grupos a los que el usuario no pertenece. El listado de grupos en el contexto se obtiene siempre a través de `_get_grupos_usuario(request.user)`, nunca de `Grupo.objects.all()`.
- En el modal del Paso 3, la lista de miembros disponibles como deudores se filtra por `GrupoMiembro.objects.filter(grupo=grupo).exclude(usuario=request.user)`, nunca exponiendo usuarios de otros grupos. El contexto de `dashboard_view` debe incluir un diccionario `miembros_por_grupo` indexado por `grupo_id` para que Alpine.js pueda actualizar reactivamente el selector del Paso 3 al cambiar el grupo en el Paso 2.

---

## 6. Resumen de Archivos Afectados

| Archivo | Tipo de cambio |
|---------|---------------|
| `finances/models.py` | Modificación de `Concepto`, `Movimiento`, `RegistroPresupuesto`; nuevos modelos `ReplicaGrupal` y `DivisionPresupuesto` |
| `finances/migrations/` | Squash + nueva migración inicial |
| `finances/web_views.py` | Reescritura completa de todas las vistas; eliminación de `_get_grupo`; nuevo `group_finances_view` |
| `finances/views.py` | Bloqueo de `POST` en movimientos grupales; nuevas vistas personales; nuevo `ReplicarMovimientoView` |
| `finances/serializers.py` | Ajuste de campos nullable; nuevos `ReplicaGrupalSerializer` y `DivisionPresupuestoSerializer`; `RegistroPresupuestoSerializer` extiende con `divisiones` |
| `finances/web_urls.py` | Nuevas rutas para vista de grupo y endpoints personales |
| `finances/urls.py` | Nuevas rutas API personales; eliminación de `POST` en movimientos grupales |
| `finances/templates/finances/dashboard.html` | Rediseño de KPIs, sección de grupos, modal de replicación |
| `finances/templates/finances/concepts.html` | Contexto personal; eliminar referencia a `grupo` |
| `finances/templates/finances/budget.html` | Contexto personal; eliminar referencia a `grupo`; checkbox "Dividir presupuesto"; modal de división con grilla Alpine.js |
| `finances/templates/finances/movements.html` | Filtro por movimientos personales |
| `finances/templates/finances/movement_detail.html` | Sección de réplicas |
| `finances/templates/finances/shared_expenses.html` | Columna de grupo; multi-grupo |
| `finances/templates/finances/group_finances.html` | Nueva plantilla |
