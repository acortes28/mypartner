# Módulo de Ahorros — Especificaciones

## Concepto central: Metas de Ahorro

La unidad fundamental es una **meta** — un objetivo con nombre, monto objetivo, fecha límite opcional y aportes registrados. Puede ser personal o grupal.

---

## Acceso al módulo

El módulo de ahorros **no tiene entrada directa desde el menú principal**. Se accede desde los dashboards existentes:

- **Ahorro personal** → accesible desde el dashboard de Finanzas (`/finances/`) mediante un acceso directo en la cabecera o en una sección del listado principal.
- **Ahorro grupal** → accesible desde el dashboard de cada grupo (`/finances/groups/<group_id>/`) mediante un acceso directo equivalente.

Esto mantiene el contexto: el usuario llega al ahorro desde el ámbito (personal o grupal) donde tiene sentido usarlo, sin necesidad de un módulo aislado en el menú.

---

## Flujo Individual

### Vista principal de metas personales

Acceso: botón/enlace "Mis ahorros" dentro del dashboard de Finanzas personales.

- Lista de metas con tarjetas que muestran:
  - Nombre de la meta
  - Barra de progreso visual
  - Monto ahorrado / monto objetivo
  - Días restantes (si hay fecha límite)
- Orden: metas más próximas a su fecha límite primero.
- Estado visual diferenciado:
  - **En curso** → barra verde
  - **Completada** → badge de completado
  - **Vencida sin completar** → tarjeta en gris
- Botón "Nueva meta" para crear.

### Crear meta personal — 2 pasos

**Paso 1:** Nombre + monto objetivo + fecha límite (opcional)

**Paso 2:** Aporte inicial opcional + frecuencia de recordatorio (semanal / mensual / ninguno)

### Vista de detalle de meta personal

- Barra de progreso prominente con porcentaje
- Historial de aportes con fecha y monto
- Botón principal: **"Aportar"** → abre un mini-modal con input de monto formateado (separador de miles)
- Acciones secundarias: editar meta / archivar meta
- Botón **"Retirar"** → descuenta del saldo de la meta y genera un movimiento de tipo Ingreso con etiqueta "Retiro de ahorro". No elimina el historial, solo ajusta el saldo neto.

---

## Flujo Grupal

### Vista principal de metas grupales

Acceso: botón/enlace "Ahorros del grupo" dentro del dashboard de cada grupo (`/finances/groups/<group_id>/`).

- Lista de metas grupales del grupo, con la misma estructura de tarjeta que el flujo personal.
- Diferencia clave: debajo de la barra de progreso total, se muestra un desglose por miembro con avatar, monto aportado y porcentaje individual de la meta.

### Crear meta grupal — 3 pasos

**Paso 1:** Nombre + monto objetivo + fecha límite (opcional)

**Paso 2:** ¿Dividir el objetivo equitativamente entre miembros?
- Toggle Sí/No
- Si es Sí: muestra cuánto le corresponde a cada miembro

**Paso 3:** Notificar al grupo (sí/no)

Solo el **admin del grupo** puede crear y editar metas grupales. Cualquier miembro puede aportar.

### Vista de detalle de meta grupal

- Barra de progreso total del grupo
- Desglose por miembro: avatar + monto aportado + porcentaje de la meta que cubre
- Botón **"Aportar"** disponible para cualquier miembro → el sistema registra quién aportó qué
- El admin puede editar o archivar la meta

---

## Integración con módulos existentes

| Punto de integración | Comportamiento |
|---|---|
| **Registrar ingreso (personal)** | Opción "Asignar a meta de ahorro" al crear un ingreso personal |
| **Presupuesto** | Nueva categoría especial "Ahorro" que aparece en el resumen mensual |
| **Dashboard personal** | Widget con el progreso de la meta activa más próxima a su fecha límite |
| **Dashboard grupal** | Widget con el progreso de la meta grupal más próxima a su fecha límite |
| **Notificaciones** | Alerta al grupo o usuario al llegar al 50%, 75% y 100% del objetivo |

---

## Decisiones de diseño

### Los aportes crean movimientos
Cada aporte genera un movimiento de tipo "Ahorro" en el historial de finanzas (personales o grupales). Esto mantiene coherencia con el registro financiero y refleja el ahorro en el presupuesto mensual.

### Retiro de ahorros
El retiro no elimina el historial: descuenta del saldo neto de la meta y crea un movimiento de tipo Ingreso etiquetado como "Retiro de ahorro". La trazabilidad se conserva siempre.

### Metas grupales: tracking paralelo (no fondo centralizado)
No existe un "pozo" real de dinero en la app. Cada miembro registra sus aportes y el sistema los agrega, pero la administración del dinero real queda fuera del alcance de la app — consistente con el modelo actual de gastos compartidos.

---

## Modelo de datos (conceptual)

```
MetaAhorro
├── nombre                  : str
├── monto_objetivo          : int (CLP)
├── fecha_limite            : date | null
├── tipo                    : enum [personal, grupal]
├── usuario                 : FK User | null   (si tipo = personal)
├── grupo                   : FK Grupo | null  (si tipo = grupal)
└── activa                  : bool

AporteAhorro
├── meta                    : FK MetaAhorro
├── usuario                 : FK User
├── monto                   : int (CLP)
├── fecha                   : datetime
└── movimiento              : FK Movimiento | null  (trazabilidad opcional)
```

---

## Pantallas necesarias

| Pantalla | URL sugerida |
|---|---|
| Lista de metas personales | `/finances/savings/` |
| Detalle de meta personal | `/finances/savings/<id>/` |
| Crear meta personal | `/finances/savings/new/` |
| Lista de metas grupales | `/finances/groups/<group_id>/savings/` |
| Detalle de meta grupal | `/finances/groups/<group_id>/savings/<id>/` |
| Crear meta grupal | `/finances/groups/<group_id>/savings/new/` |

El modal de aporte es reutilizable entre flujo personal y grupal.

---

## Fuera del alcance (v1)

- Intereses o rendimientos
- Conexión con cuentas bancarias reales
- Inversiones o categorías de activos

---

## Implementación sugerida

Implementar en dos iteraciones:

1. **v1 — Metas personales:** modelo de datos, vistas personales, integración con dashboard personal y presupuesto.
2. **v2 — Metas grupales:** extensión del modelo, vistas grupales, integración con dashboard de grupo y notificaciones.
