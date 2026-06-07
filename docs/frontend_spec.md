# MyPartner — Especificación de Frontend (Django POC)

> Documento de referencia UI/UX del prototipo Django. Describe cada pantalla, sus componentes, patrones de interacción y el sistema de diseño completo. Sirve como fuente de verdad para la reimplementación en Flutter.

---

## Índice

1. [Stack tecnológico](#1-stack-tecnológico)
2. [Sistema de diseño](#2-sistema-de-diseño)
3. [Layout global y navegación](#3-layout-global-y-navegación)
4. [Componentes globales reutilizables](#4-componentes-globales-reutilizables)
5. [Módulo: Autenticación](#5-módulo-autenticación)
6. [Módulo: Menú principal](#6-módulo-menú-principal)
7. [Módulo: Ajustes de usuario](#7-módulo-ajustes-de-usuario)
8. [Módulo: Finanzas personales — Dashboard](#8-módulo-finanzas-personales--dashboard)
9. [Módulo: Movimientos](#9-módulo-movimientos)
10. [Módulo: Tarjetas](#10-módulo-tarjetas)
11. [Módulo: Presupuesto](#11-módulo-presupuesto)
12. [Módulo: Conceptos](#12-módulo-conceptos)
13. [Módulo: Ahorros personales](#13-módulo-ahorros-personales)
14. [Módulo: Mis pendientes (gastos compartidos)](#14-módulo-mis-pendientes-gastos-compartidos)
15. [Módulo: Finanzas grupales — Lista de grupos](#15-módulo-finanzas-grupales--lista-de-grupos)
16. [Módulo: Finanzas grupales — Detalle de grupo](#16-módulo-finanzas-grupales--detalle-de-grupo)
17. [Módulo: Ahorros grupales](#17-módulo-ahorros-grupales)
18. [Módulo: División de gastos (Split)](#18-módulo-división-de-gastos-split)
19. [Módulo: Grupos — Gestión](#19-módulo-grupos--gestión)
20. [Módulo: Anuncios](#20-módulo-anuncios)
21. [Módulo: Documentos](#21-módulo-documentos)
22. [Módulo: Notificaciones](#22-módulo-notificaciones)
23. [Patrones de interacción](#23-patrones-de-interacción)
24. [Patrones de formulario](#24-patrones-de-formulario)
25. [Animaciones y transiciones](#25-animaciones-y-transiciones)

---

## 1. Stack tecnológico

| Capa | Tecnología |
|---|---|
| Backend | Django (Python) con templates Jinja2 |
| CSS | Tailwind CSS vía CDN (utility-first, sin archivo CSS propio) |
| JavaScript | Alpine.js 3.x (reactividad declarativa, sin bundler) |
| Charts | Chart.js (doughnut charts) |
| Fuente | Plus Jakarta Sans (Google Fonts — 400, 500, 600, 700, 800) |
| PWA | manifest.json + Service Worker básico |
| Push real-time | EventSource (SSE) para contador de notificaciones |

---

## 2. Sistema de diseño

### 2.1 Paleta de colores

#### Marca
| Token | Valor | Uso |
|---|---|---|
| `brand` | `#166534` | Color primario de marca (verde oscuro) |
| `brand-light` | `#bbf7d0` | Fondos claros de marca |
| `brand-dark` | `#14532d` | Hover/active en elementos primarios |

#### Colores semánticos en UI
| Contexto | Color base | Aplicación |
|---|---|---|
| Gastos / Peligro | `red-600` (#dc2626) | Montos negativos, botones destructivos, indicadores de gasto |
| Ingresos / Éxito | `green-600` (#16a34a) | Montos positivos, estados de completado |
| Acción primaria | `blue-600` (#2563eb) | Botones CTA de registro, creación, navegación |
| Presupuesto/Info | `blue-100/600` | Etiquetas de periodicidad Mensual |
| Anual | `purple-100/700` | Etiquetas de periodicidad Anual |
| Corrección | `orange-500` (#f97316) | Botones y estados de edición/corrección |
| Advertencia | `yellow-600` | Mensajes de warning |
| Neutros | `gray-50` → `gray-900` | Fondos, textos, bordes, separadores |

#### Colores de fondos de header por pantalla
| Módulo | Fondo header |
|---|---|
| Login | Gradiente `from-green-800 to-green-900` |
| Menú principal | Gradiente `from-green-800 via-green-700 to-green-900` |
| Finanzas personales | `bg-green-800` sólido |
| Finanzas grupales | `bg-green-800` sólido |
| Ahorros (personal y grupal) | `bg-green-800` sólido |
| Split | `bg-green-800` sólido |
| Resto de pantallas | `bg-gray-50` (sin hero header) |

### 2.2 Tipografía

Fuente única: **Plus Jakarta Sans**

| Escala | Clase Tailwind | Tamaño | Uso típico |
|---|---|---|---|
| xs | `text-xs` | 12px | Etiquetas, timestamps, subtítulos secundarios, labels de formulario |
| sm | `text-sm` | 14px | Texto de cuerpo, items de lista, botones |
| base | `text-base` | 16px | Texto base (raramente usado explícitamente) |
| lg | `text-lg` | 18px | Títulos de modales |
| xl | `text-xl` | 20px | Títulos de pantalla (h1 en la mayoría de vistas) |
| 2xl | `text-2xl` | 24px | Montos principales en KPI cards |
| 3xl | `text-3xl` | 30px | Logo en login |
| 4xl | `text-4xl` | 36px | Monto grande en detalle de movimiento |

**Pesos usados:**
- `font-normal` (400) — texto secundario
- `font-medium` (500) — textos de soporte
- `font-semibold` (600) — labels, items secundarios
- `font-bold` (700) — títulos, nombres de ítem
- `font-extrabold` (800) — montos en KPIs, nombre de app en navbar

### 2.3 Espaciado y tamaños

**Contenedor máximo:** `max-w-md` = 448px (centrado en pantalla, diseño pensado para móvil)

**Padding de pantalla:** `px-4` (16px) como regla general

**Bordes redondeados:**
- Cards principales: `rounded-2xl` (16px)
- Inputs / botones: `rounded-xl` (12px)
- Avatares: `rounded-full`
- Tags/badges: `rounded-full` o `rounded-lg`
- Bottom sheets (modales): `rounded-t-3xl` (24px arriba)
- Cards de tarjetas bancarias: `rounded-2xl`

**Sombras:**
- Cards de contenido: `shadow-sm`
- Elementos interactivos hover: `shadow-md`
- Navbar y modales: `shadow-lg` / `shadow-2xl`

### 2.4 Iconografía

Todos los íconos son SVG inline de la librería **Heroicons** (stroke-based, line-weight `stroke-width="2"` o `2.5`). Tamaño estándar: `w-5 h-5` en navbar, `w-4 h-4` en botones pequeños.

Emojis usados como íconos de módulo:
| Módulo | Emoji |
|---|---|
| Finanzas | 💰 |
| Finanzas grupales | 🏘️ |
| División de gastos | 🧾 |
| Anuncios | 📢 |
| Documentos | 📁 |
| Ahorros | 🐷 |
| Presupuesto | 📊 |
| Conceptos | 🏷️ |
| Tarjetas | 💳 |
| Crédito | 💎 |
| Grupos | 👥 |
| Admin | 👑 |

---

## 3. Layout global y navegación

### 3.1 Estructura HTML base

```
<body>
  <header>        ← Navbar sticky (solo si autenticado)
  <div>           ← Message modal (toast de feedback)
  <div>           ← Confirmation modal global
  <main>          ← Contenido de la página (max-w-md, centrado, pb-24)
  <div>           ← PWA install banner
</body>
```

### 3.2 Navbar

**Visible:** Solo cuando el usuario está autenticado  
**Posición:** Sticky top, z-40  
**Altura:** h-14 (56px)  
**Fondo:** `bg-green-800` (verde oscuro)  
**Contenido:**
- **Izquierda:** Logo "MyPartner" — `font-extrabold text-lg tracking-tight` — link a menú principal
- **Derecha:** 3 íconos en fila (gap-2):
  1. 🔔 **Bell de notificaciones** — con badge rojo (número de no leídas). Al hacer click abre dropdown inline con lista de notificaciones
  2. ⚙️ **Ajustes** — navega a `/settings/`
  3. 🚪 **Logout** — form POST

**Dropdown de notificaciones:**
- Posición: `absolute right-0 top-12`, ancho fijo `w-80`
- Fondo blanco, `rounded-2xl shadow-2xl border border-gray-100`
- Header verde oscuro con título y botón "Marcar todas"
- Lista de notificaciones (hasta ~5 más recientes no leídas)
- Cada ítem: título (xs), timestamp (xs gray-400)
- Footer: link "Ver todas mis notificaciones →"
- Estado vacío: "Sin notificaciones nuevas" centrado en gris
- Spinner durante carga (`animate-spin`)

### 3.3 Tipos de pantalla

**Tipo A — Pantalla con hero header verde:**
```
[NAVBAR]
[HERO SECTION — bg-green-800, texto blanco, KPIs]
[CONTENT AREA — bg-gray-50 con rounded-t-3xl, px-4]
[BOTTOM BAR — fixed, sobre el contenido]
```

**Tipo B — Pantalla estándar (sin hero):**
```
[NAVBAR]
[TÍTULO + BACK BUTTON — px-4 py-6]
[CARDS DE CONTENIDO — bg-white rounded-2xl, px-4, space-y-4]
```

**Tipo C — Pantalla de auth (sin navbar):**
```
[FONDO GRADIENTE o GRAY-50]
[LOGO + FORMULARIO CARD]
```

### 3.4 Navegación entre pantallas

No hay nav bar inferior permanente en la mayoría de pantallas. La navegación se hace mediante:
- **Back button** en header: botón `←` chevron (p-2, text-gray-500)
- **Bottom bar contextual** en dashboard de finanzas (3 tabs fijos en bottom)
- **Cards de menú** en pantalla principal
- **Side drawer** en dashboard de finanzas (menú lateral deslizante desde la derecha)
- **Links "Ver todos →"** en secciones de listas

---

## 4. Componentes globales reutilizables

### 4.1 Toast de mensajes del sistema

Aparece al hacer submit de cualquier form con feedback de Django messages.

**Comportamiento:**
- Se muestra centrado sobre un backdrop blur semitransparente
- Auto-cierre a los 2 segundos
- Cierre manual con botón X
- Progress bar verde que se contrae en 2s (animación CSS `msgShrink`)

**Estructura:**
```
[BACKDROP — bg-black/40 backdrop-blur-sm]
[CARD — bg-white rounded-2xl shadow-2xl max-w-sm]
  [BOTÓN X — esquina superior derecha]
  [LISTA DE MENSAJES]
    [ÍCONO — 40×40 rounded-2xl, color según tipo]
    [TEXTO — label uppercase xs bold + mensaje sm]
  [PROGRESS BAR — h-1 green-600 animada]
```

**Tipos de mensaje:**
| Tag | Ícono | Color ícono bg | Label |
|---|---|---|---|
| `error` | ✕ circular | `bg-red-100` / `text-red-600` | Error |
| `warning` | ⚠ triángulo | `bg-yellow-100` / `text-yellow-600` | Advertencia |
| `success` | ✓ circular | `bg-green-100` / `text-green-600` | Éxito |
| (default) | ℹ circular | `bg-blue-100` / `text-blue-600` | Información |

### 4.2 Modal de confirmación global

Presente en el DOM de todas las páginas autenticadas. Se activa mediante Alpine.js a través del estado global en `<body x-data>`.

**Diseño:** Bottom sheet desde abajo
- Backdrop: `bg-black/60 backdrop-blur-sm`
- Sheet: `bg-white rounded-t-3xl px-6 pt-4 pb-10`
- Handle gris en el tope: `w-10 h-1 bg-gray-200 rounded-full`
- Ícono de advertencia: `w-16 h-16 bg-red-50 rounded-2xl` con triángulo rojo
- Título: `text-xl font-extrabold text-gray-900`
- Mensaje: `text-sm text-gray-500 leading-relaxed`
- Botón confirmar: `bg-red-600 py-4 rounded-2xl font-bold`
- Botón cancelar: `bg-gray-100 py-4 rounded-2xl font-semibold text-gray-700`

**Activación desde cualquier template:**
```javascript
confirmTitle = 'Título';
confirmMessage = 'Mensaje descriptivo';
confirmBtnText = 'Texto del botón';
confirmAction = '/url/accion/';
confirmFields = { campo: 'valor' };
confirmModal = true;
```

### 4.3 Custom datepicker

Componente Alpine.js registrado globalmente como `datepicker()`.

**Diseño:**
- Trigger: botón full-width estilo input con texto de fecha formateada (dd/mm/yyyy)
- Dropdown: card absoluta con header verde oscuro (navegación mes) + grid 7×6 de días
- Día seleccionado: `bg-green-800 text-white font-bold rounded-xl`
- Hoy (no seleccionado): `ring-2 ring-green-500 ring-offset-1 rounded-xl font-semibold text-green-800`
- Días de otros meses: `text-gray-300 cursor-default`

### 4.4 Card de lista estándar

Patrón universal para ítems en listas:
```
[DIV — flex items-center gap-3 px-5 py-3.5 border-b border-gray-50]
  [AVATAR/ÍCONO — w-8/9 h-8/9 rounded-full bg-COLOR-100]
  [CONTENIDO — flex-1 min-w-0]
    [TÍTULO — text-sm font-semibold text-gray-900 truncate]
    [SUBTÍTULO — text-xs text-gray-400]
  [VALOR/ACCIÓN — text-right flex-shrink-0]
```

### 4.5 KPI Card

Fondo semi-transparente sobre header verde:
```
[DIV — bg-green-700/50 rounded-2xl p-4 backdrop-blur-sm]
  [LABEL — text-green-300 text-xs font-semibold mb-1]
  [VALOR — text-xl/2xl font-extrabold text-white]
```
Rojo condicional (`text-red-300`) cuando el valor es negativo.

### 4.6 Barra de progreso

```
[DIV — h-2.5 bg-gray-100 rounded-full overflow-hidden]
  [DIV — h-full rounded-full bg-blue-500 (o green-500 si completado)]
    → style="width: X%"
```
Altura varía: `h-1.5` (mínima), `h-2.5` (estándar), `h-3` (grande en header).

### 4.7 Badge/tag de estado

```
[SPAN — px-1.5 py-0.5 text-[10px] font-bold rounded-md]
```
Colores por tipo:
- Mensual: `bg-blue-100 text-blue-700`
- Anual: `bg-purple-100 text-purple-700`
- Dividido: `bg-orange-100 text-orange-700`
- Completada (ahorro): `bg-green-100 text-green-700`
- Admin: `bg-green-100 text-green-800`
- Miembro: `bg-gray-100 text-gray-600`

### 4.8 Select global

Los `<select>` tienen una apariencia custom universal:
- Flecha SVG verde (#166534) vía background-image
- `padding-right: 2.5rem` para no solapar la flecha
- Fondo blanco con `focus:outline-none`

### 4.9 Empty state

```
[DIV — text-center py-8/10/12]
  [EMOJI — text-4xl mb-3]
  [TÍTULO — text-gray-700 font-semibold mb-1] (opcional)
  [SUBTÍTULO — text-sm text-gray-400]
  [CTA BUTTON] (opcional)
```

---

## 5. Módulo: Autenticación

### 5.1 Login

**URL:** `/login/`  
**Tipo de pantalla:** C (sin navbar)  
**Fondo:** Gradiente `from-green-800 to-green-900` full-screen

**Estructura:**
```
[HERO — text-center mb-10]
  💚 (emoji grande text-5xl)
  "MyPartner" (text-3xl font-extrabold text-white)
  "Gestión colaborativa de presupuestos" (text-sm text-green-300)

[CARD — bg-white rounded-2xl shadow-2xl p-7]
  "Bienvenido de vuelta" (text-xl font-bold mb-6)
  
  [INPUT] Usuario — tipo text, autocomplete="username"
  [INPUT] Contraseña — tipo password
  
  [BUTTON] "Ingresar" — bg-blue-600, w-full, py-3.5
  
  [LINK] "Olvidé mi contraseña" — text-sm text-gray-500, centrado
  [DIVIDER] border-t border-gray-100
  [BUTTON] "Registrarme" — outline verde (border-2 border-green-700), w-full
```

**Estilos de inputs:** `px-4 py-3 rounded-xl border border-gray-200 focus:ring-2 focus:ring-green-600`

### 5.2 Registro

**URL:** `/register/`  
**Tipo:** C (sin navbar)  
**Fondo:** `bg-gray-50`

**Estructura:**
```
[HEADER — flex items-center gap-3 mb-6]
  [BACK BUTTON ←]
  "Crear cuenta" (text-xl font-bold)

[CARD — bg-white rounded-2xl shadow-sm p-6]
  [FORM — space-y-4]
    [INPUT] Email * — tipo email
    [INPUT] Usuario * — x-model vinculado para validación de contraseña
    
    [GRID 2 COL]
      [INPUT] Nombre *
      [INPUT] Apellido *
    
    [INPUT] Contraseña * — con validación live
    [CRITERIA PANEL — x-show="password.length > 0"]
      Bg-gray-50 rounded-xl p-3
      6 criterios con ✓/○ y color green-600/gray-400:
        • Mínimo 8 caracteres
        • Al menos una mayúscula
        • Al menos una minúscula
        • Al menos un número
        • Al menos un carácter especial
        • Sin nombre, apellido ni usuario
    
    [INPUT] Repetir contraseña *
    [BUTTON] "Registrarse" — bg-blue-600
  
  [BUTTON] "Cancelar" — outline gray

```

**Validación:**  
Estados de error en inputs: `border-red-400 bg-red-50` + mensaje `text-red-500 text-xs`

### 5.3 Recuperar contraseña

**URL:** `/password-recovery/`  
**Tipo:** C  
**Fondo:** `bg-gray-50`

```
[HEADER con back button ←]
[CARD bg-white]
  🔑 (text-4xl, centrado)
  Texto explicativo (text-sm text-gray-600)
  
  [ERROR STATE — si email no encontrado]
    Banner rojo con ícono de usuario + mensaje + CTA "Crear una cuenta"
  
  [INPUT] Email — validación live con regex
  [BUTTON] "Enviar correo" — disabled si email inválido (bg-gray-200 si disabled)
  [BUTTON] "Cancelar" — outline gray
```

### 5.4 Confirmar contraseña nueva

**URL:** `/password-recovery/confirm/<token>/`

```
[HEADER con back]
[CARD bg-white]
  [INPUT] Nueva contraseña — con panel de criterios (igual que registro)
  [INPUT] Repetir contraseña
  [BUTTON] "Cambiar contraseña" — bg-blue-600
```

### 5.5 Verificación de email pendiente

Pantalla informativa, sin formulario. Muestra mensaje con ícono de sobre y botón para reenviar verificación.

### 5.6 Verificación de email confirmada

Pantalla de resultado (éxito / token expirado / token inválido) con icono y CTA a login.

---

## 6. Módulo: Menú principal

**URL:** `/menu/`  
**Tipo:** A modificado (gradiente completo, contenido en bg-gray-50 redondeado)

```
[NAVBAR]

[HERO — bg-gradient green-800→900, px-6 pt-6 pb-8, text-white]
  Fecha actual: "lunes, 06 de junio" (text-green-200 text-sm font-medium)
  "Hola [Nombre] [Apellido]," (text-2xl font-extrabold)
  "¿Qué hay de nuevo hoy?" (text-green-300)

[CONTENIDO — bg-gray-50 rounded-t-3xl px-4 pt-6 pb-28]
  "MÓDULOS" (text-xs uppercase tracking-widest text-gray-400 mb-4)
  
  [LISTA DE MÓDULOS — space-y-3]
    Cada módulo es un <a> card:
    [DIV — flex items-center gap-4 bg-white rounded-2xl px-5 py-4 shadow-sm border border-gray-100]
      [ÍCONO — w-12 h-12 bg-COLOR-50 rounded-xl, emoji text-2xl, group-hover:scale-110]
      [TEXTO]
        Nombre (font-bold text-gray-900)
        Subtítulo (text-xs text-gray-500)
      [CHEVRON → gris, ml-auto]
```

**Módulos en orden:**
1. 💰 **Finanzas** — "Gastos, ingresos y presupuesto" → bg-blue-50
2. 🏘️ **Finanzas grupales** — "Gastos e ingresos compartidos" → bg-orange-50
3. 🧾 **División de gastos** — "Divide una cuenta entre el grupo" → bg-yellow-50
4. 📢 **Anuncios** — "Comunicados del grupo" → bg-green-50
5. 📁 **Documentos** — "Archivos compartidos" → bg-purple-50

**Banner de notificaciones no leídas** (condicional):
```
[A — flex items-center gap-3 mt-4 bg-blue-50 border border-blue-200 rounded-2xl px-4 py-3]
  🔔 "N notificación(es) sin leer" (text-sm font-semibold text-blue-800)
  [CHEVRON →]
```

**Botón flotante fijo:**
```
[DIV — fixed bottom-0 px-4 pb-6]
  [A → /finances/?panel=gasto]
    "Registrar nuevo gasto" — bg-red-600, py-4, w-full, rounded-2xl, font-bold
    [ÍCONO +]
```

---

## 7. Módulo: Ajustes de usuario

**URL:** `/settings/`  
**Tipo:** B estándar

```
"Mis ajustes" (text-2xl font-extrabold mb-2)

[CARD PERFIL — bg-white rounded-2xl p-6]
  [AVATAR — w-14 h-14 bg-green-100 rounded-2xl]
    Inicial del nombre en mayúscula (text-2xl font-bold text-green-700)
  [DATOS]
    Nombre completo (font-bold text-gray-900)
    @username (text-sm text-gray-500)
  [BORDER-T]
    Correo: label gris | valor semibold

[CARD MIS GRUPOS — bg-white rounded-2xl]
  [HEADER — bg-gray-50 border-b]
    "MIS GRUPOS" (uppercase xs bold)
    "Gestionar →" (text-xs text-blue-600, link)
  
  [LISTA de membresías activas]
    Cada fila: 
      [ÍCONO 👥 — w-8 h-8 bg-green-100 rounded-xl]
      [NOMBRE del grupo + badge de rol]
      [CHEVRON →]
    
    [EMPTY STATE si sin grupos]
      "Aún no perteneces a ningún grupo" + CTA crear

[BUTTON] "Gestionar mis grupos" — bg-blue-600, icon de grupo
```

---

## 8. Módulo: Finanzas personales — Dashboard

**URL:** `/finances/`  
**Tipo:** A (hero verde + contenido)

### 8.1 Header / Hero

```
[BG-GREEN-800 px-4 pt-2 pb-6]

[ROW — justify-between mb-3]
  "Personal" (text-green-300 xs uppercase)
  "Mis Finanzas" (text-xl font-extrabold)
  [BOTÓN Exportar — bg-green-600 px-3 py-1.5 text-xs]
  [BOTÓN ☰ — bg-green-700 p-2 rounded-lg → abre side drawer]

[ROW NAVEGACIÓN VISTA — mb-4]
  [TAB SWITCH — bg-green-900/50 rounded-xl p-1]
    "Histórico" | "Mensual" → tab activo: bg-white text-green-800
  [LINK Mis pendientes — bg-green-700 px-3 py-1.5 text-xs]
    [BADGE CONTADOR — absolute -top-1.5 bg-red-500 w-4 h-4 text-[10px]]

[KPI CARDS]
  [CARD FULL WIDTH — bg-green-700/50 rounded-2xl p-4]
    "Gasto acumulado mensual/histórico" (text-green-300 xs)
    Monto total (text-2xl font-extrabold)
  
  [GRID 2 COL]
    Saldo restante | Desviación Presupuestaria
    (rojo si < 0)
```

### 8.2 Contenido principal

```
[px-4 pt-4 space-y-4]

[CARD GRÁFICO — bg-white rounded-2xl p-5] (condicional)
  "Gastos por concepto — mes actual/histórico"
  [DOUGHNUT CHART — canvas 220×220 max, cutout 65%]
  [LEYENDA CUSTOM — por cada concepto]
    punto de color | nombre (truncado max-w-140px) | monto (CLP) (XX%)

[CARD ÚLTIMOS MOVIMIENTOS — bg-white rounded-2xl]
  [HEADER — bg-gray-50 border-b]
    "ÚLTIMOS MOVIMIENTOS" | "Ver todos →" (link azul)
  [LISTA de movimientos]
    [AVATAR circular — bg-red-100/green-100]
      ↑ (rojo para gasto) | ↓ (verde para ingreso)
    [NOMBRE truncado] + [Concepto xs gray-400]
    [-$monto rojo] | [+$monto verde]
    "Detalle" (link azul xs)
  [EMPTY STATE]
    "Sin movimientos registrados"
```

### 8.3 Barra inferior de acciones (bottom bar)

```
[FIXED bottom-0 bg-white border-t z-30]
[GRID 3 COLS — max-w-md mx-auto]
  💸 "Añadir Gasto" — activo: bg-red-50 text-red-700
  📋 "Ver movimientos" — link
  💵 "Añadir Ingreso" — activo: bg-green-50 text-green-700
```

### 8.4 Panel modal: Añadir gasto (Paso 1)

Bottom sheet desde abajo (`fixed inset-0`, `items-end`):
```
[BG-WHITE rounded-t-2xl p-6 slide-up]
  "Añadir Gasto" (font-bold lg) | [✕ cerrar]
  
  [FORM space-y-4]
    SELECT — Medio de pago (Efectivo | tarjetas)
    INPUT — Cuotas [x-show si tarjeta crédito]
    INPUT — Nombre *
    SELECT — Concepto (gastos del usuario)
    INPUT — Monto (CLP) * [inputmode=numeric, formato CLP en blur]
    INPUT — Detalle
    CHECKBOX — "Es compartido" [x-show si tiene grupos]
    SELECT — Grupo [x-show si es compartido]
    
    [BUTTON] "Registrar gasto" — bg-red-600
      → Si es compartido y hay grupo: avanza a Paso 2
      → Si no: submit directo
```

### 8.5 Panel modal: Dividir gasto (Paso 2)

```
[BG-WHITE rounded-t-2xl p-6 slide-up max-h-[92vh] overflow-y-auto]
  "Paso 2 de 2" (xs gray-400) | "Dividir gasto" (font-bold lg) | "← Volver"
  
  SELECT — "Compartir con *" (miembros del grupo)
  
  [TABLA DIVISIÓN — x-show si usuarioDeudor]
    Headers: Usuario | Monto | %
    Fila yo (fija): monto calculado automáticamente
    Fila otro: inputs de monto y porcentaje (sincronizados)
    ERROR: si monto compartido ≥ total → "⚠ El monto compartido..."
  
  [UPLOAD COMPROBANTE — x-show si usuarioDeudor]
    Área drag&drop con borde punteado
    → PDF, CSV, XLSX, PNG, máx 10 MB
  
  [BUTTON] "Registrar gasto" — bg-red-600, disabled si no válido
```

### 8.6 Panel modal: Añadir ingreso

```
[BG-WHITE rounded-t-2xl p-6 slide-up]
  "Añadir Ingreso" | [✕]
  
  SELECT — Cuenta/Tarjeta débito (opcional)
  INPUT — Nombre *
  SELECT — Concepto (ingresos)
  INPUT — Monto (CLP) *
  INPUT — Detalle
  CHECKBOX — "Registrar en un grupo"
  SELECT — Grupo [x-show si registrarEnGrupo]
  
  [BUTTON] "Registrar ingreso" — bg-green-600
```

### 8.7 Side drawer (menú lateral)

```
[DRAWER — fixed top-0 right-0 h-full w-72 bg-white z-50 shadow-2xl]
[HEADER — bg-green-800 text-white px-5 py-4]
  "Personal" | "Mis Finanzas" | [✕]
  
[NAV — px-3 py-4 space-y-1]
  Cada ítem: flex items-center gap-3 px-4 py-3.5 rounded-xl hover:bg-COLOR-50
    [ÍCONO — w-9 h-9 bg-COLOR-100 rounded-xl, emoji]
    [TÍTULO bold + subtítulo xs]
    [CHEVRON →]
  
  • 🐷 Ahorros — hover:bg-green-50
  • 📊 Presupuesto — hover:bg-blue-50
  • 🏷️ Conceptos — hover:bg-purple-50
  • 💳 Tarjetas — hover:bg-blue-50
```

---

## 9. Módulo: Movimientos

**URL:** `/finances/movimientos/`  
**Tipo:** B estándar

```
[HEADER con back button ←]
"Movimientos" (text-xl font-bold)

[FILTRO POR CONCEPTO]
  SELECT full-width — "Todos los conceptos" | conceptos del usuario
  → onChange submite el form automáticamente

[LISTA — bg-white rounded-2xl overflow-hidden]
  Por cada movimiento:
    [AVATAR circular bg-red-100/green-100 con ↑/↓]
    Nombre truncado | Concepto (xs gray-400) | Fecha (xs gray-400)
    Monto rojo/verde | "Ver detalle" (link azul xs)

[PAGINACIÓN — si hay más páginas]
  ← Anterior | N/Total | Siguiente →
  (px-4 py-2 text-sm font-semibold text-blue-600 border rounded-xl)

[EMPTY STATE]
  "Sin movimientos registrados" (py-12)
```

### 9.1 Detalle de movimiento

**URL:** `/finances/movimientos/<id>/`

```
[HEADER con back button ←]
"Detalle"

[CARD — bg-white rounded-2xl overflow-hidden]
  [BANNER SUPERIOR — bg-red-600/green-600 px-6 py-8 text-center]
    "Gasto/Ingreso personal" (sm font-semibold opacity-80)
    ±$MONTO (text-4xl font-extrabold)
  
  [LISTA DE DATOS — divide-y divide-gray-100]
    Nombre | Concepto | Detalle (si existe) | Fecha y hora
  
  [SECCIÓN CORREGIR MONTO — solo gastos]
    [COLLAPSIBLE — hover:bg-orange-50]
      "Corregir monto" (text-sm font-semibold text-orange-600) + chevron
      [EXPANDIDO]
        Texto explicativo (xs gray-500)
        INPUT — "Monto final (CLP)" [formato CLP]
        PREVIEW DIFERENCIA (bg-red-50 o bg-green-50 según signo)
        BUTTON "Registrar corrección" — bg-orange-500

[SECCIÓN RÉPLICAS EN GRUPOS — si existen]
  "REPLICADO EN GRUPOS" (label xs uppercase)
  Lista de grupos con link a cada uno
  
  [SI NO HAY RÉPLICAS]
    "Este movimiento no está replicado..."
    Link → ir al dashboard
```

---

## 10. Módulo: Tarjetas

**URL:** `/finances/tarjetas/`  
**Tipo:** B estándar

```
[HEADER — justify-between]
  ← | "Mis tarjetas"
  [BUTTON] "+ Añadir" — bg-blue-600

[LISTA DE TARJETAS — space-y-4]
  Por cada tarjeta:
  [CARD — rounded-2xl shadow-sm overflow-hidden]
    [VISUAL — px-5 py-5 text-white]
      Crédito: bg-gradient from-gray-700 to-gray-900
      Débito: bg-gradient from-blue-500 to-blue-700
      
      ROW: banco (xs opacity-60) + nombre (font-extrabold lg) | badge tipo
      
      [SI CRÉDITO y cupo_total]:
        "Cupo usado" label | valor/total
        Barra de progreso blanca (h-1.5)
      
      [SI DÉBITO]:
        "Saldo disponible" | monto (text-2xl font-extrabold)
    
    [FOOTER — bg-white flex justify-between px-5 py-3.5]
      "Ver movimientos →" (link azul sm)
      "Eliminar" (text-xs text-red-500, form POST)

[EMPTY STATE]
  💳 + "Sin tarjetas registradas"

[MODAL AÑADIR — bottom sheet]
  "Nueva tarjeta"
  INPUT — Nombre *
  [SELECTOR TIPO — grid 2 col]
    💳 Débito | 💎 Crédito
    → borde/fondo activo: débito=blue-600, crédito=gray-700
  SELECT — Banco
  [SI CRÉDITO x-show]
    INPUT — Cupo total (opcional)
    INPUT — Cupo actual usado (con validación cupoUsado ≤ cupoTotal)
  BUTTON "Guardar" — bg-blue-600
```

### 10.1 Detalle de tarjeta

```
[HEADER con back]
"Nombre de tarjeta"

[VISUAL CARD — igual al de la lista pero más grande, py-6]

[STATS — solo débito, grid 2 col]
  bg-red-50: Total gastado | bg-green-50: Total ingresos

[SECCIÓN "Movimientos"]
  Label xs uppercase
  [LISTA — bg-white rounded-2xl]
    Avatar rojo/verde con ↑/↓
    Nombre + concepto + fecha + cuotas (si crédito, badge "Xc" azul)
    Monto rojo/verde + "Detalle" link
```

---

## 11. Módulo: Presupuesto

**URL:** `/finances/budget/`  
**Tipo:** B estándar

```
[HEADER — justify-between]
  ← | "Mi Presupuesto"
  [BUTTON] "+ Agregar" — bg-blue-600 (toggle showAdd)

[NAVEGADOR DE MES — bg-white rounded-2xl px-4 py-3 mb-4]
  ← | "Mes YYYY" (text-green-700 font-extrabold lg) | →
  Navegación via fetch AJAX (sin reload de página)

[FORMULARIO AGREGAR — x-show, x-transition]
  bg-white rounded-2xl p-5 mb-4
  "Nuevo registro"
  [GRID 2 COL] Tipo (select) | Concepto (select, depende de tipo)
  INPUT — Nombre *
  [DATEPICKER custom]
  [GRID 2 COL] Monto (CLP) | Periodicidad (Puntual/Mensual/Anual)
  [DATEPICKER FECHA FIN — x-show si Mensual o Anual]
  CHECKBOX — "Dividir presupuesto" [si tiene grupos]
  [BOTONES] Guardar | Cancelar

[LISTA REGISTROS — bg-white rounded-2xl]
  Por cada registro:
    [ROW flex justify-between px-5 py-3.5]
      Nombre concepto + badges (Mensual/Anual/Dividido)
      Fecha | si fecha_fin: "Hasta MM/YYYY" (text-orange-500)
      Tipo (rojo si gasto, verde si ingreso)
      | Monto bold | [BOTONES Modificar/Eliminar]
    
    [DIVISIONES — si existen]
      "División:" label
      Por usuario: nombre | monto CLP (%)
    
    [INLINE EDIT — x-show si editId]
      Input de monto + OK + ✕
  
  [FOOTER — bg-green-50 border-t]
    "Total presupuesto" | Monto total (font-extrabold xl text-green-800)

[MODAL DIVISIÓN — bottom sheet, si se activa "Dividir presupuesto"]
  "Dividir presupuesto"
  SELECT — Grupo
  [TABLA — si grupo seleccionado]
    Headers: Usuario | Monto | %
    Fila propietario: auto-calculado
    Filas añadidas: inputs numéricos sincronizados
    [ERROR si suma > total]
  SELECT + BUTTON — Agregar usuario del grupo
  BUTTON "Finalizar" — disabled si distribución inválida
```

---

## 12. Módulo: Conceptos

**URL:** `/finances/concepts/`  
**Tipo:** B estándar

```
[HEADER — justify-between]
  ← | "Mis Conceptos"
  [BUTTON] "+ Agregar" — bg-blue-600

[ALERT CONFLICTO — bg-yellow-50, si concepto con movimientos]
  "Concepto con movimientos"
  Dos opciones: "Conservar movimientos" | "Eliminar todo" (destructivo)

[FORMULARIO AGREGAR — x-show]
  INPUT — Nombre *
  [TIPO — grid 2 col, radio buttons estilizados]
    Gasto → hover red / Ingreso → hover green
    Seleccionado: `has-[:checked]:border-red-400 has-[:checked]:bg-red-50`
  BOTONES: Guardar | Cancelar

[LISTA — bg-white rounded-2xl]
  Por cada concepto:
    [ROW flex justify-between]
      Punto de color (red-500 o green-500, w-2.5 h-2.5)
      Nombre bold | tipo (xs gray-400)
      [BOTONES] Editar (azul) | Eliminar (rojo)
    [INLINE EDIT — x-show]
      Input texto + OK + ✕

[EMPTY STATE]
  "Sin conceptos creados" (py-12)
```

---

## 13. Módulo: Ahorros personales

### 13.1 Lista de metas

**URL:** `/finances/savings/`

```
[HERO HEADER — bg-green-800]
  ← | "Personal" | "Mis Ahorros"
  [BUTTON] "+ Nueva meta" — bg-green-600 px-3 py-1.5

[FORMULARIO NUEVA META — x-show]
  bg-white rounded-2xl p-5
  INPUT — Nombre *
  INPUT — Monto objetivo (CLP) * [formato CLP]
  INPUT — Fecha límite (date, opcional)
  BOTONES: Crear meta | Cancelar

[LISTA DE METAS — space-y-4]
  Por cada meta:
  [LINK CARD — bg-white rounded-2xl p-5 hover:shadow-md]
    ROW: Nombre truncado + badge "Completada" (si aplica)
    Días restantes / "Vence hoy" (orange) / "Venció" (red) / "Sin fecha límite" (gray)
    [BARRA PROGRESO h-2.5]
      Azul si en curso | Verde si completada
    Monto ahorrado (xs gray-500) | X% de $META (bold)

[EMPTY STATE]
  🐷 + "Sin metas de ahorro aún"
```

### 13.2 Detalle de meta personal

**URL:** `/finances/savings/<id>/`

```
[HERO HEADER — bg-green-800]
  ← | "Meta personal" | Nombre de meta
  [BUTTON ✏️ editar — p-1.5, toggle showEdit]
  
  [CARD PROGRESO — bg-green-700/50 rounded-2xl p-4]
    Ahorrado (text-2xl font-extrabold) | Objetivo (text-lg text-green-200)
    [BARRA h-3 — azul/verde]
    X% | días restantes / estado de vencimiento

[FORMULARIO EDITAR — x-show]
  bg-white rounded-2xl p-5
  INPUT — Nombre | Monto objetivo | Fecha límite
  BOTONES: Guardar | Cancelar
  [FORM SEPARADA — border-t]
    "Archivar meta" (text-xs text-red-500, button destructivo)

[ACCIONES — grid 2 col]
  [BUTTON] Aportar — bg-green-700, ícono +
  [BUTTON] Retirar — bg-white border-2, disabled si sin saldo, ícono -

[HISTORIAL — bg-white rounded-2xl]
  "HISTORIAL" header
  Por cada movimiento:
    "Aporte" (verde) | "Retiro" (rojo)
    Fecha (xs gray-400)
    +/- monto (font-extrabold)

[MODAL APORTAR — bottom sheet]
  INPUT — Monto (CLP) *
  BUTTON "Confirmar aporte" — bg-green-700

[MODAL RETIRAR — bottom sheet]
  "Disponible: $XXX" (texto informativo)
  INPUT — Monto a retirar (CLP) *
  BUTTON "Confirmar retiro" — bg-red-600
```

---

## 14. Módulo: Mis pendientes (gastos compartidos)

**URL:** `/finances/shared/`  
**Tipo:** B estándar

```
[HEADER — justify-between]
  ← | "Mis pendientes"
  [BUTTON] "Liquidar" — bg-green-700

[RESUMEN — grid 2 col gap-3]
  bg-red-50 border-red-100: "Debo" | total debo (xl font-extrabold text-red-700)
  bg-green-50 border-green-100: "Me deben" | total (xl text-green-700)

[SECCIÓN "Lo que debo"]
  Label xs uppercase mb-2
  [LISTA — bg-white rounded-2xl]
    Por cada deuda:
      Avatar círculo bg-red-100 con ↑ (flecha arriba)
      Concepto | "Le debes a [username]" · [grupo] · fecha
      Monto rojo font-extrabold

[SECCIÓN "Lo que me deben"]
  [LISTA — bg-white rounded-2xl]
    Por cada crédito:
      Avatar bg-green-100 con ↓
      Concepto | "[username] te debe" · [grupo] · fecha
      Monto verde | [BUTTON] "Pagado" (verde outline, form POST)

[MODAL LIQUIDAR — bottom sheet]
  "Liquidar deudas"
  
  [SI SIN USUARIOS LIQUIDABLES]
    🤝 + "No tienes movimientos que puedan ser liquidados"
    Explicación: se necesitan ≥ 2 deudas con mismo usuario
  
  [SI HAY USUARIOS]
    Texto descriptivo (sm text-gray-500)
    [CHIPS DE USUARIOS — flex flex-wrap gap-2]
      Por usuario: chip con inicial del nombre + username
      Seleccionado: border-green-600 bg-green-50
    
    [PREVIEW LIQUIDACIÓN — si usuario seleccionado]
      bg-gray-50 rounded-2xl p-4
      "Me debe X" | verde | "Le debo X" | rojo
      [BORDER-T] "Saldo neto" | resultado (verde/rojo/neutro)
      Banner de resultado: texto descriptivo de quién debe qué
    
    BUTTON "Confirmar liquidación" — bg-green-700
```

---

## 15. Módulo: Finanzas grupales — Lista de grupos

**URL:** `/finances/groups/`  
**Tipo:** A parcial (hero verde + contenido)

```
[HERO HEADER — bg-green-800]
  ← | "MyPartner" | "Mis finanzas grupales"

[LISTA DE GRUPOS — px-4 pt-4 space-y-3]
  Por cada grupo:
  [LINK CARD — bg-white rounded-2xl border border-gray-100 overflow-hidden hover:shadow-md]
    [HEADER — px-5 py-4 border-b border-gray-50 flex justify-between]
      🏘️ (w-10 h-10 bg-green-100 rounded-xl)
      Nombre del grupo (font-bold)
      N miembros · "Admin" si es admin (text-green-700)
      CHEVRON →
    
    [KPI STRIP — grid 3 col divide-x]
      "Gasto mes" | valor (rojo extrabold)
      "Ingreso mes" | valor (verde extrabold)
      "Saldo mes" | valor (rojo si < 0, verde si ≥ 0)
  
  Nota pie: "Los montos corresponden al mes actual." (xs gray-400)

[EMPTY STATE]
  🏘️ + "Sin grupos" + CTA "Crear o unirse a un grupo"
```

---

## 16. Módulo: Finanzas grupales — Detalle de grupo

**URL:** `/finances/groups/<id>/`  
**Tipo:** A (hero verde + contenido)

```
[HERO HEADER — bg-green-800]
  ← | "Grupo · N miembro(s)" | "Nombre del grupo"
  [LINK] "🐷 Ahorros" — bg-green-600 px-3 py-1.5 text-xs
  
  [KPI GRID 2+2]
    Gasto mes | Ingreso mes
    Saldo mes | Gasto histórico

[INTEGRANTES — bg-white rounded-2xl]
  Header "INTEGRANTES" uppercase
  Chips por miembro: bg-gray-100 rounded-full
    Punto verde si admin, gris si miembro

[GASTOS COMPARTIDOS — si pendientes]
  bg-white rounded-2xl
  Header "GASTOS COMPARTIDOS"
  GRID 2 COL (dividido por borde vertical):
    "Debo" | total rojo | lista detalle
    "Me deben" | total verde | lista detalle
  Link "Ver todos mis pendientes →"

[PRESUPUESTO COMPARTIDO — si hay]
  bg-white rounded-2xl
  Header + totales (Gastos | Ingresos)
  Por registro: concepto + badge periodicidad + nombre/fecha + chips de división
  Monto + tipo (Gasto=rojo/Ingreso=verde)

[ÚLTIMOS MOVIMIENTOS]
  bg-white rounded-2xl
  Header
  Lista estándar de movimientos con @username adicional

[BANNER INFO — bg-blue-50 border-blue-100 rounded-2xl]
  Texto explicativo sobre cómo funciona la réplica de movimientos

[BUTTON] "Ir a mis finanzas personales" — bg-green-700
```

---

## 17. Módulo: Ahorros grupales

### 17.1 Lista (misma estructura que ahorros personales)

**URL:** `/finances/groups/<id>/savings/`  
Solo admins pueden crear metas. El botón "+ Nueva meta" es condicional.  
Formulario tiene checkbox adicional "Notificar al grupo".

### 17.2 Detalle de meta grupal

**URL:** `/finances/groups/<grupo_id>/savings/<meta_id>/`  
Idéntico a personal con:
- Solo admins ven el botón de edición
- Un único botón "Aportar a esta meta" (no hay Retirar separado)
- Sección adicional **"Aportes por miembro"**:
  ```
  Por cada miembro:
    Avatar inicial | Nombre
    Barra progreso (% del aporte total)
    Monto | % del total
  ```
- El historial incluye el username de quién aportó

---

## 18. Módulo: División de gastos (Split)

**URL:** `/finances/split/`  
**Tipo:** A (hero verde) con wizard de 3 pasos

### 18.1 Indicador de pasos

En el hero, debajo del título:
```
[FLEX ITEMS-CENTER gap-2]
  Por n en [1, 2, 3]:
    Círculo w-7 h-7:
      Completado: bg-green-400 con ✓
      Actual: bg-white text-green-800 con número
      Pendiente: bg-green-700 text-green-300 con número
    Línea h-0.5 (si no es el último):
      Completada: bg-green-400
      Pendiente: bg-green-700
```

### 18.2 Paso 1 — Configuración

```
"Configura la cuenta que vas a dividir." (xs gray-500)

[CARD bg-white]
  SELECT — Grupo *
  INPUT — "Total de la boleta (CLP) *"
  
  [PROPINA toggle]
    CHECKBOX "Propina / servicio" + label Sí/No
    [x-show si propina]
      INPUT numérico (%) + texto "+$monto calculado"
  
  [TOTAL CON PROPINA — bg-green-50, si monto > 0]
    "Total a dividir" | Monto (text-lg font-extrabold text-green-800)

[CARD bg-white — Modo de ingreso]
  "Modo de ingreso"
  [GRID 2 col]
    💸 "Por monto" — borde activo green-600
    🧾 "Por producto" — borde activo green-600
    Cada uno con descripción en xs gray-400

[BUTTON] "Comenzar →" — bg-green-700, disabled si sin grupo o sin monto
```

### 18.3 Paso 2A — Por monto

```
"¿Cuánto consumió cada uno?" | [← Volver]

[BARRA PROGRESO — bg-white rounded-2xl px-5 py-4]
  "Asignado" | "$asignado / $total"
  Barra h-2.5 verde (roja si excede)

[LISTA DE MIEMBROS — bg-white rounded-2xl]
  Yo: avatar green + nombre (yo) + monto auto-calculado (verde) + "auto-calculado"
  Otros: avatar gris + nombre + [← resto] (link) + input monto

[BUTTON] "⚡ Dividir equitativamente" — outline verde
[BUTTON] "Ver resumen →" — bg-green-700
```

### 18.4 Paso 2B — Por producto

```
[TOTAL ÍTEMS — bg-white rounded-2xl]
  "Total ítems ingresados" | monto
  Indicador: "✓ Coincide con total" (verde) | "Debe coincidir..." (amber)

[LISTA DE ÍTEMS]
  Por cada ítem:
    Nombre + "N × $precio = $subtotal"
    [X eliminar]
    Chips de usuarios (pill verde si asignado, gris si no)
    "÷ entre N personas · $X c/u" (si > 1 usuario)
    "⚠ Asigna al menos una persona" (si 0 usuarios)

[FORM AGREGAR ÍTEM — collapsible]
  INPUT nombre | grid: INPUT cantidad + INPUT precio
  Subtotal preview
  Chips de usuarios para asignar
  BOTONES: Agregar | Cancelar

[BUTTON] "Ver resumen →"
```

### 18.5 Paso 3 — Resumen y confirmación

```
[CARD TOTALES bg-white]
  Subtotal boleta | Propina (si aplica) | Total final

[CARD PAGADOR bg-white]
  "¿Quién pagó la cuenta?"
  Chips de miembros: seleccionado = border-green-600 bg-green-50 + ✓

[CARD DISTRIBUCIÓN — bg-white rounded-2xl]
  Header "DISTRIBUCIÓN DEL GASTO"
  Por miembro con monto > 0:
    Fila destacada (bg-green-50) para quien pagó
    Avatar | Nombre | "pagó la cuenta" o "debe a [pagador]"
    Monto (verde para pagador, rojo para deudores)

[CARD CONCEPTO — bg-white]
  INPUT editable "Concepto" (default: "División de cuenta")

[BUTTON] "Confirmar y asignar pendientes" — bg-green-700
  Estado loading: spinner + "Procesando..."
```

### 18.6 Paso 4 — Éxito

```
✅ (text-6xl)
"¡División registrada!" (text-xl font-extrabold)
"Se crearon los siguientes pendientes de pago:"

[LISTA — bg-white rounded-2xl]
  Por deudor: avatar rojo + nombre + "te debe" + monto rojo

[ACCIONES]
  "Ver mis pendientes" — bg-green-700
  "Nueva división" — outline verde
  "Volver al inicio" — text-sm text-gray-400
```

---

## 19. Módulo: Grupos — Gestión

### 19.1 Lista de grupos

**URL:** `/groups/manage/`

```
[HEADER con back ←]
"Mis grupos"

[LISTA — space-y-3 mb-4]
  Por cada grupo:
  [LINK CARD — flex items-center gap-4 bg-white rounded-2xl px-5 py-4]
    👥 (w-10 h-10 bg-green-100 rounded-xl)
    Nombre | descripción (xs gray-400 truncada) | badge rol (Admin 👑 / Miembro)
    CHEVRON →

[EMPTY STATE]
  👥 grande + "Aún no perteneces a ningún grupo"

[COLLAPSIBLE CREAR GRUPO — bg-white rounded-2xl]
  Header: ícono + icon "+" con "Crear nuevo grupo" + chevron rotante
  [EXPANDIDO — border-t]
    INPUT — Nombre del grupo *
    TEXTAREA — Descripción (2 rows, resize-none)
    BUTTON "Crear grupo" — bg-green-600
```

### 19.2 Detalle de grupo

**URL:** `/groups/manage/<id>/`

```
[HEADER con back ←]
Nombre del grupo | descripción (xs gray-400)

[CARD — bg-white] Mi rol
  "Tu rol en este grupo" | badge Admin 👑 / Miembro

[LISTA MIEMBROS — bg-white rounded-2xl]
  Header "MIEMBROS (N)"
  Por cada miembro:
    Avatar circular (inicial) bg-green-100 text-green-700
    Nombre + apellido + "(tú)" si es el user actual
    @username (xs gray-400)
    Rol: "Admin" (text-green-700) | "Miembro" (text-gray-400)
    [SI ES ADMIN y no es yo]
      BUTTON "Quitar Admin" / "Hacer Admin" (outline amarillo/verde)
      BUTTON "Quitar" (outline rojo) → abre modal de confirmación global

[SI ES ADMIN]
  [COLLAPSIBLE AGREGAR MIEMBRO]
    INPUT — username | TEXTAREA — comentario (opcional)
    BUTTON "Enviar invitación" — bg-green-600
  
  [BUTTON] "🗑 Eliminar grupo" — outline rojo (abre modal global)

[SI ES MIEMBRO]
  [BUTTON] "Abandonar grupo" — outline naranja (abre modal global)
```

---

## 20. Módulo: Anuncios

### 20.1 Lista de anuncios

**URL:** `/announcements/group/<id>/`

```
[HEADER — justify-between]
  ← | "Anuncios" | nombre del grupo (xs gray-400)
  [BUTTON] "+ Crear" — bg-blue-600

[FORM CREAR — x-show]
  bg-white rounded-2xl p-5 mb-4
  INPUT — Nombre * | TEXTAREA — Descripción * (3 rows)
  BOTONES: Publicar | Cancelar

[LISTA — space-y-3]
  Por cada anuncio:
  [CARD bg-white rounded-2xl p-5]
    Nombre (font-bold) | @username · fecha (xs gray-400)
    Descripción (sm gray-600, line-clamp-3)
    [BOTONES]
      "Ver detalle" — border border-blue-200 text-blue-600, flex-1
      "Eliminar" — border border-red-200 text-red-600 [solo si es el autor]

[EMPTY STATE]
  📢 + "Sin anuncios publicados"
```

### 20.2 Detalle de anuncio

```
[HEADER con back ←]
Nombre del anuncio truncado flex-1
[ÍCONO PAPELERA — si es el autor, abre modal global]

[CARD CUERPO — bg-white rounded-2xl p-5]
  Avatar circular (inicial) | Nombre completo
  Fecha · nombre del grupo (xs gray-400)
  Descripción completa (sm leading-relaxed whitespace-pre-wrap)

[CARD COMENTARIOS — bg-white rounded-2xl]
  Header "COMENTARIOS (N)"
  Por cada comentario:
    Avatar pequeño (w-6 h-6) | @username | fecha
    Contenido (sm text-gray-700, pl-8)
  EMPTY: "Sin comentarios" (py-6)

[CARD NUEVO COMENTARIO — bg-white rounded-2xl p-5]
  TEXTAREA — placeholder "Escribe un comentario..." (3 rows)
  BUTTON "Comentar" — bg-blue-600
```

---

## 21. Módulo: Documentos

**URL:** `/documents/group/<id>/`

```
[HEADER — justify-between]
  ← | "Documentos" | nombre del grupo (xs gray-400)
  [BUTTON] "+ Subir" — bg-blue-600

[FORM SUBIR — x-show]
  bg-white rounded-2xl p-5 mb-4
  INPUT — Nombre * | INPUT FILE — .pdf .csv .xlsx .png (máx 10MB)
  TEXTAREA — Descripción (2 rows, opcional)
  BOTONES: Subir | Cancelar

[LISTA — space-y-3]
  Por cada documento:
  [CARD bg-white rounded-2xl p-4 flex items-start gap-4]
    [ÍCONO TIPO — w-10 h-10 rounded-xl]
      PDF: bg-red-100 text-red-600
      PNG: bg-purple-100 text-purple-600
      XLSX: bg-green-100 text-green-600
      CSV: bg-blue-100 text-blue-600
      Texto: extensión en uppercase font-extrabold xs
    
    Nombre (sm font-semibold) + descripción (xs gray-500) + @usuario · fecha
    
    [BOTONES]
      "Ver" — link externo, border blue
      "Eliminar" — border red [solo si es el autor] → modal global

[EMPTY STATE]
  📁 + "Sin documentos subidos"
```

---

## 22. Módulo: Notificaciones

**URL:** `/notifications/`

```
[HEADER — justify-between]
  ← | "Notificaciones"
  [LINK] "Marcar todas" — border blue text-xs [si hay sin leer]

[LISTA — bg-white rounded-2xl]
  Por cada notificación:
  [LINK — flex items-start gap-3 px-5 py-4 border-b hover:bg-gray-50]
    Fondo bg-blue-50/40 si no leída
    
    [AVATAR TIPO — w-9 h-9 rounded-full]
      💸 gasto: bg-red-100 text-red-600
      💵 ingreso: bg-green-100 text-green-600
      📊 presupuesto: bg-blue-100 text-blue-600
      📢 anuncio: bg-yellow-100 text-yellow-600
      💌 otro: bg-purple-100 text-purple-600
    
    Título (sm, font-semibold si no leída, gray-600 si leída)
    Fecha (xs gray-400)
    
    [PUNTO AZUL — w-2 h-2 bg-blue-500 rounded-full si no leída]

[PAGINACIÓN estándar]

[EMPTY STATE]
  🔔 + "Sin notificaciones" (py-12)
```

---

## 23. Patrones de interacción

### 23.1 Modales tipo Bottom Sheet

Todos los modales de formulario siguen este patrón:

```
Position: fixed inset-0 z-40/50
Display: flex items-end justify-center
Backdrop: bg-black/50 (o /60 para modales importantes) @click.self="cerrar"

Sheet: bg-white rounded-t-2xl w-full max-w-md p-6 slide-up
  (max-h-[92vh] overflow-y-auto si contenido variable)

Header del sheet:
  Título (font-bold lg) + botón ✕ (text-xl leading-none text-gray-400)
```

La animación `slide-up` es un keyframe CSS:
```css
@keyframes slideUp {
  from { transform: translateY(100%); opacity: 0; }
  to   { transform: translateY(0); opacity: 1; }
}
```

### 23.2 Collapsibles (expandibles inline)

Patrón de sección expandible dentro de una card:
```
[BUTTON trigger — flex justify-between w-full px-5 py-4 hover:bg-gray-50]
  Texto | chevron SVG con :class="open ? 'rotate-180' : ''"

[DIV expandible — x-show x-transition border-t px-5 pb-5]
  Contenido del formulario/info
```

### 23.3 Chips de selección múltiple

Para asignación de usuarios (Split, etc.):
```
[BUTTON — px-2.5/3 py-1/1.5 rounded-full text-xs font-semibold]
  Activo: bg-green-600 text-white
  Inactivo: bg-gray-100 text-gray-500 hover:bg-gray-200
```

### 23.4 Tab switch (toggle de vista)

```
[DIV — bg-green-900/50 rounded-xl p-1]
  [A — px-4 py-1.5 rounded-lg text-xs font-bold]
    Activo: bg-white text-green-800
    Inactivo: text-green-300 hover:text-white
```

### 23.5 Inputs de montos en CLP

Patrón consistente en todos los inputs de monto:
```
type="text"
inputmode="numeric"
@input: filtrar solo dígitos, actualizar modelo
@focus: mostrar valor crudo (sin formato)
@blur: formatear con toLocaleString('es-CL')
```

### 23.6 Sidebar drawer (panel lateral)

Para finanzas personales:
```
Backdrop: fixed inset-0 bg-black/50 z-40 @click="sideMenu=false"
  x-transition:enter: opacity 0→1 (200ms)
  x-transition:leave: opacity 1→0 (150ms)

Drawer: fixed top-0 right-0 h-full w-72 bg-white z-50 shadow-2xl
  x-transition:enter: translate-x-full → translate-x-0 (250ms)
  x-transition:leave: translate-x-0 → translate-x-full (200ms)
```

---

## 24. Patrones de formulario

### 24.1 Estructura de inputs

```
[LABEL — block text-sm font-semibold text-gray-700 mb-1.5]
[INPUT — w-full px-4 py-3 rounded-xl border focus:outline-none focus:ring-2]
  Normal: border-gray-200
  Error: border-red-400 bg-red-50
  Focus: ring-green-600 (o color del contexto)
[ERROR MSG — text-red-500 text-xs mt-1]
```

Labels en formularios internos (más pequeños): `text-xs font-semibold text-gray-600 mb-1`

### 24.2 Botones principales

**Tamaño grande (CTA de pantalla):**
```
py-3.5 rounded-2xl font-bold text-sm w-full
```

**Tamaño mediano (dentro de secciones):**
```
py-2.5 rounded-xl font-bold text-sm
```

**Tamaño pequeño (inline actions):**
```
px-2.5 py-1 text-xs font-semibold rounded-lg border
```

**Estados disabled:** `:disabled:opacity-50` o `:disabled:opacity-40` + `cursor-not-allowed`

**Estilos por color:**
| Contexto | Fondo | Hover |
|---|---|---|
| Primario/Crear | bg-blue-600 | bg-blue-700 |
| Verde/Confirmar | bg-green-600/700 | bg-green-700/800 |
| Peligro/Gasto | bg-red-600 | bg-red-700 |
| Corrección | bg-orange-500 | bg-orange-600 |
| Outline peligro | border-red-300 text-red-600 | bg-red-50 |
| Outline verde | border-green-200 text-green-700 | bg-green-50 |
| Neutro | bg-gray-100 | bg-gray-200 |

### 24.3 Validación en tiempo real

Usa Alpine.js `get` properties (computed). Botones de submit desactivados si condición no cumple. Validaciones:
- Contraseña: 6 criterios verificados en tiempo real
- Montos: `parseInt(value) > 0`
- Formularios compuestos: computed `allGood` / `gastoValido` / `divisionValida`

---

## 25. Animaciones y transiciones

### 25.1 Animaciones CSS globales

| Nombre | Definición | Uso |
|---|---|---|
| `slideUp` | translateY(100%)→0, opacity 0→1, 250ms ease-out | Bottom sheets |
| `fadeIn` | opacity 0→1, 200ms ease-out | Dropdowns, popups |
| `msgShrink` | width 100%→0% | Progress bar del toast |
| `animate-spin` | rotación 360° continua | Spinners de carga |

### 25.2 Transiciones Alpine.js

Todos los `x-show` con `x-transition` usan las transiciones por defecto de Alpine (opacity + scale, 150ms). Las transiciones explícitas:

```
x-transition:enter="transition ease-out duration-200"
x-transition:enter-start="opacity-0 scale-95"
x-transition:enter-end="opacity-100 scale-100"
x-transition:leave="transition ease-in duration-150"
x-transition:leave-start="opacity-100"
x-transition:leave-end="opacity-0"
```

### 25.3 Hover/active states

- Cards de módulo: `hover:shadow-md transition-shadow`
- Ícono de módulo en hover: `group-hover:scale-110 transition-transform`
- Botones: `transition-colors`
- Links de lista: `hover:bg-gray-50 transition-colors`
- Presupuesto — navegación de mes: opacity fade (0.4→1) vía JavaScript en fetch

---

## Apéndice A: Rutas de URLs

| Ruta | Vista | Módulo |
|---|---|---|
| `/login/` | Login | Auth |
| `/register/` | Registro | Auth |
| `/password-recovery/` | Recuperar clave | Auth |
| `/menu/` | Menú principal | App |
| `/settings/` | Ajustes | App |
| `/finances/` | Dashboard finanzas | Finanzas |
| `/finances/movimientos/` | Lista movimientos | Finanzas |
| `/finances/movimientos/<id>/` | Detalle movimiento | Finanzas |
| `/finances/tarjetas/` | Tarjetas | Finanzas |
| `/finances/tarjetas/<id>/` | Detalle tarjeta | Finanzas |
| `/finances/budget/` | Presupuesto | Finanzas |
| `/finances/concepts/` | Conceptos | Finanzas |
| `/finances/savings/` | Ahorros personales | Finanzas |
| `/finances/savings/<id>/` | Detalle ahorro | Finanzas |
| `/finances/shared/` | Mis pendientes | Finanzas |
| `/finances/split/` | División de gastos | Finanzas |
| `/finances/groups/` | Grupos financieros | Finanzas Grupales |
| `/finances/groups/<id>/` | Detalle grupo | Finanzas Grupales |
| `/finances/groups/<id>/savings/` | Ahorros grupal | Finanzas Grupales |
| `/finances/groups/<id>/savings/<id>/` | Detalle ahorro grupal | Finanzas Grupales |
| `/groups/manage/` | Gestión grupos | Grupos |
| `/groups/manage/<id>/` | Detalle grupo | Grupos |
| `/groups/invitation/<token>/` | Invitación | Grupos |
| `/announcements/` | Selector de grupo | Anuncios |
| `/announcements/group/<id>/` | Lista anuncios | Anuncios |
| `/announcements/group/<id>/<id>/` | Detalle anuncio | Anuncios |
| `/documents/` | Selector de grupo | Documentos |
| `/documents/group/<id>/` | Lista documentos | Documentos |
| `/notifications/` | Notificaciones | Notificaciones |

## Apéndice B: Convenciones de nomenclatura de clases Tailwind

El proyecto usa utility-first puro, sin componentes CSS extraídos. Patrones de clase que se repiten como "componentes implícitos":

**Input estándar:**
`w-full px-4 py-3 rounded-xl border border-gray-200 focus:outline-none focus:ring-2 focus:ring-green-600 text-sm`

**Card contenedor:**
`bg-white rounded-2xl shadow-sm overflow-hidden`

**Section header:**
`px-5 py-3 bg-gray-50 border-b border-gray-100`

**Label xs:**
`text-xs font-bold text-gray-500 uppercase tracking-wide`

**Avatar circular:**
`w-9 h-9 rounded-full flex items-center justify-center flex-shrink-0`

**Button CTA:**
`w-full py-3.5 font-bold rounded-xl text-sm transition-colors`

**Back button:**
`p-2 text-gray-500 hover:text-gray-700`
