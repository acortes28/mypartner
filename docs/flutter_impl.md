# Plan de Implementación Flutter + Django API REST

Documento de referencia para la migración del frontend de Django templates a Flutter, manteniendo Django como backend API REST. El objetivo es que la app Flutter tenga exactamente las mismas funcionalidades que el frontend web actual.

---

## 1. Estado actual de la API

### 1.1 Infraestructura lista

- **JWT con SimpleJWT**: access token (1h) + refresh (7 días), rotación y blacklist activos.
- **Rutas `api/v1/`** separadas de las web views: coexisten sin conflicto.
- **Swagger en `/api/docs/`**: documentación generada automáticamente con drf-spectacular.
- **CORS configurado**: necesario para Flutter web build.
- **Custom exception handler** en `apps/users/exceptions.py`: respuestas de error uniformes.
- **Paginación estándar**: `PageNumberPagination` con `PAGE_SIZE = 15` por defecto en `REST_FRAMEWORK`.

### 1.2 Endpoints API ya implementados

```
# Auth
POST   /api/v1/auth/register/
POST   /api/v1/auth/login/                         → { access, refresh, user }
POST   /api/v1/auth/logout/
POST   /api/v1/auth/token/refresh/
POST   /api/v1/auth/password-recovery/
POST   /api/v1/auth/password-recovery/confirm/

# Usuario
GET    /api/v1/users/me/
PATCH  /api/v1/users/me/                           → actualizar perfil

# Grupos
GET    /api/v1/groups/my-group/
POST   /api/v1/groups/
DELETE /api/v1/groups/<group_id>/
POST   /api/v1/groups/<group_id>/invite/
POST   /api/v1/groups/<group_id>/remove-member/
POST   /api/v1/groups/<group_id>/set-role/
POST   /api/v1/groups/<group_id>/leave/
GET    /api/v1/invitations/
POST   /api/v1/invitations/<id>/accept/
POST   /api/v1/invitations/<id>/reject/

# Finanzas — grupo
GET    /api/v1/groups/<id>/finances/dashboard/
GET    /api/v1/groups/<id>/concepts/
POST   /api/v1/groups/<id>/concepts/
PUT    /api/v1/groups/<id>/concepts/<id>/
DELETE /api/v1/groups/<id>/concepts/<id>/
POST   /api/v1/groups/<id>/concepts/<id>/delete-with-movements/
GET    /api/v1/groups/<id>/movements/              → paginado, filtro ?concepto=
GET    /api/v1/groups/<id>/movements/export/       → CSV
GET    /api/v1/groups/<id>/movements/<id>/
GET    /api/v1/groups/<id>/budget/
POST   /api/v1/groups/<id>/budget/
PATCH  /api/v1/groups/<id>/budget/<id>/
DELETE /api/v1/groups/<id>/budget/<id>/

# Finanzas — personal
GET    /api/v1/personal/dashboard/
GET    /api/v1/personal/movements/                 → paginado
POST   /api/v1/personal/movements/
GET    /api/v1/personal/movements/<id>/
POST   /api/v1/personal/movements/<id>/replicate/

# Documentos
GET    /api/v1/groups/<id>/documents/
POST   /api/v1/groups/<id>/documents/              → multipart/form-data
DELETE /api/v1/groups/<id>/documents/<id>/

# Anuncios
GET    /api/v1/groups/<id>/announcements/
POST   /api/v1/groups/<id>/announcements/
GET    /api/v1/groups/<id>/announcements/<id>/
DELETE /api/v1/groups/<id>/announcements/<id>/
POST   /api/v1/groups/<id>/announcements/<id>/comments/

# Notificaciones
GET    /api/v1/notifications/
POST   /api/v1/notifications/<id>/read/
POST   /api/v1/notifications/read-all/
```

---

## 2. Endpoints faltantes — a implementar en el backend

Todo lo siguiente existe solo en `web_views.py` y necesita un `APIView` equivalente en `views.py` de la app correspondiente.

### 2.1 Finanzas — personal (app `finances`)

| Método | URL propuesta | Función equivalente en web_views |
|---|---|---|
| GET | `/api/v1/personal/concepts/` | `concepts_view` GET |
| POST | `/api/v1/personal/concepts/` | `concepts_view` POST action=add |
| PUT | `/api/v1/personal/concepts/<id>/` | `concepts_view` POST action=edit |
| DELETE | `/api/v1/personal/concepts/<id>/` | `concepts_view` POST action=delete |
| POST | `/api/v1/personal/concepts/<id>/delete-with-movements/` | `concepts_view` opcion conflict |
| GET | `/api/v1/personal/budget/` | `budget_view` GET |
| POST | `/api/v1/personal/budget/` | `budget_view` POST action=add (con o sin división) |
| PATCH | `/api/v1/personal/budget/<id>/` | `budget_view` POST action=modify |
| DELETE | `/api/v1/personal/budget/<id>/` | `budget_view` POST action=delete |
| PATCH | `/api/v1/personal/movements/<id>/correct/` | `movement_correct_view` |
| GET | `/api/v1/personal/export/` | `export_csv_view` → CSV |
| GET | `/api/v1/personal/shared/` | `gastos_compartidos_view` GET |
| POST | `/api/v1/personal/shared/<id>/pay/` | `gastos_compartidos_view` POST |
| POST | `/api/v1/personal/shared/liquidar/` | `liquidar_view` |
| POST | `/api/v1/personal/split/confirm/` | `split_confirm_view` |
| GET | `/api/v1/personal/savings/` | `savings_personal_view` GET |
| POST | `/api/v1/personal/savings/` | `savings_personal_view` POST |
| GET | `/api/v1/personal/savings/<id>/` | `savings_personal_detail_view` GET |
| PATCH | `/api/v1/personal/savings/<id>/` | `savings_personal_detail_view` action=editar |
| POST | `/api/v1/personal/savings/<id>/aportar/` | `savings_personal_detail_view` action=aportar |
| POST | `/api/v1/personal/savings/<id>/retirar/` | `savings_personal_detail_view` action=retirar |
| POST | `/api/v1/personal/savings/<id>/archivar/` | `savings_personal_detail_view` action=archivar |
| GET | `/api/v1/personal/cards/` | `tarjetas_view` GET |
| POST | `/api/v1/personal/cards/` | `tarjetas_view` POST action=add |
| DELETE | `/api/v1/personal/cards/<id>/` | `tarjetas_view` POST action=delete |
| GET | `/api/v1/personal/cards/<id>/` | `tarjeta_detail_view` |

### 2.2 Finanzas — grupo (app `finances`)

| Método | URL propuesta | Función equivalente en web_views |
|---|---|---|
| GET | `/api/v1/groups/<id>/savings/` | `savings_group_view` GET |
| POST | `/api/v1/groups/<id>/savings/` | `savings_group_view` POST |
| GET | `/api/v1/groups/<id>/savings/<meta_id>/` | `savings_group_detail_view` GET |
| PATCH | `/api/v1/groups/<id>/savings/<meta_id>/` | `savings_group_detail_view` action=editar |
| POST | `/api/v1/groups/<id>/savings/<meta_id>/aportar/` | `savings_group_detail_view` action=aportar |
| POST | `/api/v1/groups/<id>/savings/<meta_id>/archivar/` | `savings_group_detail_view` action=archivar |

### 2.3 Resumen: endpoint de agregar movimiento enriquecido

El `add_movement_view` actual hace múltiples acciones en una sola vista POST:
- Crea movimiento personal
- Opcionalmente lo replica al grupo
- Opcionalmente crea `GastoCompartido`
- Opcionalmente sube un comprobante como `Documento`
- Opcionalmente actualiza cupo de tarjeta de crédito

El endpoint `POST /api/v1/personal/movements/` ya soporta la creación básica. Para Flutter se extiende con los campos opcionales adicionales:

```json
{
  "tipo": "Gasto",
  "nombre": "Supermercado",
  "detalle": "",
  "monto": 15000,
  "concepto": "<uuid>",
  "fecha_hora": "2026-06-06T12:00:00",
  "tarjeta": "<uuid>",
  "cuotas": 3,
  "registrar_en_grupo": true,
  "grupo_id": "<uuid>",
  "es_compartido": true,
  "usuario_deudor_id": "<uuid>",
  "monto_compartido": 7500
}
```

El comprobante se sube en un segundo request `multipart/form-data` a `POST /api/v1/groups/<id>/documents/` para mantener los endpoints desacoplados.

### 2.4 Notificaciones

El SSE actual (`/notifications/stream/`) no funciona en background en Flutter nativo. Estrategia de corto plazo: **polling desde Flutter** con `GET /api/v1/notifications/?unread=true` cada 30 segundos cuando la app está activa.

Mediano plazo: Firebase Cloud Messaging (FCM). Requiere agregar `fcm_token` al modelo `User` y un endpoint `PATCH /api/v1/users/me/fcm-token/`.

---

## 3. Mejoras de backend necesarias antes de Flutter

### 3.1 Serializer de Notificación con contexto de navegación

El `referencia_id` actual no siempre permite navegar al recurso (ej: un anuncio necesita `group_id` además del `announcement_id`). El serializer debe enriquecer la respuesta:

```python
# notifications/serializers.py
class NotificacionSerializer(serializers.ModelSerializer):
    contexto_navegacion = serializers.SerializerMethodField()

    def get_contexto_navegacion(self, obj):
        # Resolver group_id según tipo
        ...
```

### 3.2 Verificar consistencia de paginación

Los endpoints de listado deben devolver siempre el formato paginado:
```json
{ "count": 120, "next": "...", "previous": "...", "results": [...] }
```

Revisar que `personal/concepts/`, `personal/savings/`, `personal/cards/` usen `PageNumberPagination`.

---

## 4. Arquitectura Flutter

### 4.1 Estructura de directorios

```
lib/
├── main.dart
├── app.dart                       # MaterialApp + router
├── core/
│   ├── api/
│   │   ├── api_client.dart        # Dio + interceptor de JWT
│   │   ├── endpoints.dart         # Constantes de URL
│   │   └── api_error.dart         # Modelo de error normalizado
│   ├── auth/
│   │   ├── auth_repository.dart
│   │   └── token_storage.dart     # FlutterSecureStorage
│   ├── models/                    # Modelos Dart (clases + fromJson/toJson)
│   └── router.dart                # GoRouter
├── features/
│   ├── auth/
│   │   ├── login/
│   │   ├── register/
│   │   ├── password_recovery/
│   │   └── verify_email/
│   ├── menu/
│   ├── settings/
│   ├── groups/
│   │   ├── manage/
│   │   ├── invite/
│   │   └── invitations/
│   ├── finances/
│   │   ├── dashboard/
│   │   ├── budget/
│   │   ├── concepts/
│   │   ├── movements/
│   │   ├── shared_expenses/
│   │   ├── split/
│   │   ├── savings/
│   │   ├── cards/
│   │   └── group_finances/
│   ├── announcements/
│   ├── documents/
│   └── notifications/
└── shared/
    ├── widgets/                   # AppBar, BottomNav, LoadingOverlay, etc.
    └── utils/                     # Formateo de moneda, fechas
```

Cada feature sigue la estructura:
```
feature/
├── data/
│   ├── repository.dart
│   └── models/
├── presentation/
│   ├── screens/
│   └── widgets/
└── providers/                     # Riverpod providers
```

### 4.2 Paquetes recomendados

```yaml
dependencies:
  flutter:
    sdk: flutter

  # HTTP y autenticación
  dio: ^5.7.0                       # Cliente HTTP
  flutter_secure_storage: ^9.2.2   # Almacenamiento seguro de tokens

  # Estado
  flutter_riverpod: ^2.6.1          # Gestión de estado
  riverpod_annotation: ^2.6.1

  # Navegación
  go_router: ^14.6.2

  # UI
  fl_chart: ^0.69.0                 # Gráfico de torta en dashboard
  intl: ^0.19.0                     # Formato de números y fechas (es_CL)
  cached_network_image: ^3.4.1      # Imágenes cacheadas

  # Archivos
  file_picker: ^8.1.7               # Subir documentos/comprobantes
  open_filex: ^4.4.1                # Abrir archivos descargados

  # Utilidades
  equatable: ^2.0.7                 # Comparación de objetos en providers

dev_dependencies:
  build_runner: ^2.4.13
  riverpod_generator: ^2.6.1
  json_serializable: ^6.9.0
  freezed: ^2.5.8                   # Inmutabilidad de modelos
```

### 4.3 Cliente HTTP y renovación de token

```dart
// core/api/api_client.dart
class ApiClient {
  late final Dio _dio;

  ApiClient(this._tokenStorage) {
    _dio = Dio(BaseOptions(baseUrl: Endpoints.base));
    _dio.interceptors.add(_AuthInterceptor(_tokenStorage, this));
  }
}

class _AuthInterceptor extends Interceptor {
  @override
  Future<void> onRequest(options, handler) async {
    final token = await _storage.readAccessToken();
    if (token != null) options.headers['Authorization'] = 'Bearer $token';
    handler.next(options);
  }

  @override
  Future<void> onError(err, handler) async {
    if (err.response?.statusCode == 401) {
      final refreshed = await _refreshToken();
      if (refreshed) return handler.resolve(await _retry(err.requestOptions));
      await _logout();
    }
    handler.next(err);
  }
}
```

---

## 5. Modelos Dart

Un modelo por entidad del backend. Se generan con `freezed` + `json_serializable`.

| Modelo Django | Modelo Dart |
|---|---|
| `User` | `UserModel` |
| `Grupo` | `GroupModel` |
| `GrupoMiembro` | `GroupMemberModel` |
| `Invitacion` | `InvitationModel` |
| `Concepto` | `ConceptModel` |
| `Movimiento` | `MovementModel` |
| `RegistroPresupuesto` | `BudgetEntryModel` |
| `GastoCompartido` | `SharedExpenseModel` |
| `MetaAhorro` | `SavingsGoalModel` |
| `AporteAhorro` | `SavingsContributionModel` |
| `Tarjeta` | `CardModel` |
| `Anuncio` | `AnnouncementModel` |
| `Comentario` | `CommentModel` |
| `Documento` | `DocumentModel` |
| `Notificacion` | `NotificationModel` |

Todos los IDs son `String` en Dart (UUID del backend).

---

## 6. Pantallas Flutter

Mapeadas 1:1 con las plantillas Django existentes.

### 6.1 Autenticación

| Pantalla | Template Django | Ruta Flutter |
|---|---|---|
| Login | `users/login.html` | `/login` |
| Registro | `users/register.html` | `/register` |
| Recuperar contraseña | `users/password_recovery.html` | `/password-recovery` |
| Confirmar recuperación | `users/password_recovery_confirm.html` | `/password-recovery/confirm` |
| Verificar email | `users/verify_email_pending.html` | `/verify-email` |

### 6.2 Menú y ajustes

| Pantalla | Template Django | Ruta Flutter |
|---|---|---|
| Menú principal | `users/menu.html` | `/menu` |
| Ajustes de usuario | `users/settings.html` | `/settings` |

### 6.3 Grupos

| Pantalla | Template Django | Ruta Flutter |
|---|---|---|
| Gestión de grupo | `groups/manage.html` | `/groups/manage` |
| Detalle de grupo | `groups/manage_detail.html` | `/groups/manage/:groupId` |
| Vista de invitación | `groups/invitation.html` | `/invitations/:invitationId` |

### 6.4 Finanzas personales

| Pantalla | Template Django | Ruta Flutter |
|---|---|---|
| Dashboard personal | `finances/dashboard.html` | `/finances` |
| Presupuesto | `finances/budget.html` | `/finances/budget` |
| Conceptos | `finances/concepts.html` | `/finances/concepts` |
| Movimientos | `finances/movements.html` | `/finances/movements` |
| Detalle de movimiento | `finances/movement_detail.html` | `/finances/movements/:id` |
| Gastos compartidos | `finances/shared_expenses.html` | `/finances/shared` |
| Asistente de división | `finances/split.html` | `/finances/split` |
| Ahorros personales | `finances/savings_personal.html` | `/finances/savings` |
| Detalle de ahorro personal | `finances/savings_personal_detail.html` | `/finances/savings/:id` |
| Tarjetas | `finances/tarjetas.html` | `/finances/cards` |
| Detalle de tarjeta | `finances/tarjeta_detail.html` | `/finances/cards/:id` |

### 6.5 Finanzas grupales

| Pantalla | Template Django | Ruta Flutter |
|---|---|---|
| Lista de grupos (finanzas) | `finances/group_finances_list.html` | `/finances/groups` |
| Finanzas de un grupo | `finances/group_finances.html` | `/finances/groups/:groupId` |
| Ahorros grupales | `finances/savings_group.html` | `/finances/groups/:groupId/savings` |
| Detalle de ahorro grupal | `finances/savings_group_detail.html` | `/finances/groups/:groupId/savings/:id` |

### 6.6 Anuncios

| Pantalla | Template Django | Ruta Flutter |
|---|---|---|
| Selección de grupo | `announcements/group_select.html` | `/announcements` |
| Anuncios del grupo | `announcements/index.html` | `/announcements/:groupId` |
| Detalle de anuncio | `announcements/detail.html` | `/announcements/:groupId/:id` |

### 6.7 Documentos

| Pantalla | Template Django | Ruta Flutter |
|---|---|---|
| Selección de grupo | `documents/group_select.html` | `/documents` |
| Documentos del grupo | `documents/index.html` | `/documents/:groupId` |

### 6.8 Notificaciones

| Pantalla | Template Django | Ruta Flutter |
|---|---|---|
| Lista de notificaciones | `notifications/index.html` | `/notifications` |

---

## 7. Navegación

GoRouter con autenticación guard:

```dart
final router = GoRouter(
  redirect: (context, state) {
    final isAuth = ref.read(authProvider).isAuthenticated;
    final isLoginRoute = state.matchedLocation.startsWith('/login') ||
                         state.matchedLocation.startsWith('/register');
    if (!isAuth && !isLoginRoute) return '/login';
    if (isAuth && isLoginRoute) return '/menu';
    return null;
  },
  routes: [
    GoRoute(path: '/login', ...),
    GoRoute(path: '/menu', ...),
    // Shell con BottomNavigationBar para secciones principales
    ShellRoute(
      builder: (context, state, child) => AppShell(child: child),
      routes: [
        GoRoute(path: '/finances', ...),
        GoRoute(path: '/groups', ...),
        GoRoute(path: '/notifications', ...),
      ],
    ),
  ],
);
```

La `BottomNavigationBar` tiene 4 ítems: **Finanzas**, **Grupos**, **Anuncios/Documentos**, **Notificaciones** (con badge de no leídas).

---

## 8. Gestión de estado (Riverpod)

Un provider por feature. Patrón: `AsyncNotifier` para llamadas asíncronas a la API.

```dart
// finances/providers/movements_provider.dart
@riverpod
class MovementsNotifier extends _$MovementsNotifier {
  @override
  Future<PaginatedResult<MovementModel>> build() => _fetch(page: 1);

  Future<void> loadMore() async { ... }
  Future<void> addMovement(CreateMovementDto dto) async { ... }
}
```

Providers de contexto global:
- `authProvider` — tokens, user autenticado
- `currentGroupProvider` — grupo activo del usuario
- `notificationsCountProvider` — count de no leídas (polling cada 30s)

---

## 9. Formato de moneda (CLP)

Todos los montos están en pesos chilenos enteros. Helper global:

```dart
// shared/utils/currency.dart
String formatClp(int amount) =>
    NumberFormat.currency(locale: 'es_CL', symbol: '\$', decimalDigits: 0)
        .format(amount);
```

El `intl` package requiere `initializeDateFormatting('es_CL')` en `main()`.

---

## 10. Plan de implementación por fases

### Fase 1 — Backend: completar API (sin tocar modelos)

**Objetivo**: toda la lógica de `web_views.py` queda expuesta como API REST.

**Orden de prioridad** (por dependencia de las pantallas core):

1. `ConceptoPersonalListCreateView`, `ConceptoPersonalDetailView` → `/api/v1/personal/concepts/`
2. Extender `MovimientoCreateSerializer` para soportar `registrar_en_grupo`, `es_compartido`, `usuario_deudor_id`, `monto_compartido`, `tarjeta`, `cuotas`
3. `MovimientoCorrectView` → `/api/v1/personal/movements/<id>/correct/`
4. `PresupuestoPersonalListCreateView`, `PresupuestoPersonalDetailView` → `/api/v1/personal/budget/`
5. `GastoCompartidoListView`, `MarcarPagadoView`, `LiquidarView` → `/api/v1/personal/shared/`
6. `SplitConfirmAPIView` → `/api/v1/personal/split/confirm/`
7. `MetaAhorroPersonalViewSet` (list, create, detail, patch, aportar, retirar, archivar)
8. `TarjetaViewSet` (list, create, detail, delete)
9. `MetaAhorroGrupalViewSet` (list, create, detail, aportar, archivar) — por grupo
10. Enriquecer `NotificacionSerializer` con `contexto_navegacion`

Cada vista sigue el patrón ya establecido en `apps/finances/views.py` y `apps/groups/views.py`.

### Fase 2 — Flutter: scaffolding y autenticación

1. Crear proyecto Flutter (`flutter create finanzosos_app`)
2. Configurar Dio + `FlutterSecureStorage` + interceptor JWT
3. Implementar pantallas de auth (login, register, password recovery)
4. Configurar GoRouter con auth guard
5. `BottomNavigationBar` shell

### Fase 3 — Flutter: módulos core

1. **Dashboard personal**: gráfico de torta (`fl_chart`), KPIs, últimos movimientos, acceso rápido a agregar movimiento
2. **Agregar movimiento**: form con selección de concepto, grupo, tarjeta, gasto compartido
3. **Movimientos**: lista paginada con filtro por concepto
4. **Presupuesto personal**: lista por mes con navegación, form de creación con división grupal
5. **Conceptos personales**: CRUD

### Fase 4 — Flutter: módulos complementarios

1. **Gastos compartidos**: dos columnas (debo / me deben), liquidar
2. **Asistente de división**: form multi-paso, distribución por porcentaje o monto fijo
3. **Ahorros personales**: lista de metas con progress bar, aportar / retirar
4. **Tarjetas**: lista, detalle con movimientos, indicador de cupo

### Fase 5 — Flutter: grupos y colaboración

1. **Gestión de grupo**: crear, invitar, expulsar, cambiar rol, abandonar
2. **Finanzas grupales**: dashboard grupo, movimientos, presupuesto grupal
3. **Ahorros grupales**
4. **Anuncios**: lista, detalle, comentarios
5. **Documentos**: lista, subir, abrir/descargar

### Fase 6 — Flutter: notificaciones y pulido

1. **Notificaciones**: lista, marcar leída, navegación profunda por tipo
2. Polling de no leídas + badge en `BottomNavigationBar`
3. **Ajustes de usuario**: cambiar nombre, contraseña
4. Export CSV (share sheet nativo)
5. Manejo de errores global (snackbars, empty states, skeleton loaders)

### Fase 7 — Mejoras de infraestructura (mediano plazo)

1. **Firebase Cloud Messaging**: notificaciones push en background
   - Agregar `fcm_token` al modelo `User`
   - Endpoint `PATCH /api/v1/users/me/fcm-token/`
   - Enviar push desde `crear_notificaciones_grupo` y `Notificacion.objects.create()`
2. **S3/almacenamiento externo** para documentos (`django-storages`)
3. **Offline support** básico: caché de dashboard y movimientos recientes con `Hive` o `drift`

---

## 11. Consideraciones de diseño

- El diseño visual reproduce el frontend web actual: mismos colores, tipografía, layout de cards y tablas.
- Montos siempre en CLP enteros, sin decimales.
- Formato de fecha: `dd/MM/yyyy` para fechas, `dd/MM/yyyy HH:mm` para fecha+hora.
- El flujo de "agregar movimiento" se abre como un `BottomSheet` modal desde el dashboard (igual que el botón flotante web), no como pantalla aparte.
- La pantalla de "split" es un wizard de 3 pasos: (1) seleccionar grupo y monto, (2) asignar proporciones, (3) confirmar.
- Las listas paginadas usan `ListView` con `ScrollController` para cargar más al llegar al final ("infinite scroll"), equivalente a la paginación web.

---

## 12. Lo que NO cambia

- Los modelos Django no requieren cambios para soportar Flutter.
- Las `web_views.py` se mantienen en paralelo indefinidamente: la app web Django sigue funcionando mientras Flutter se desarrolla.
- La estructura JWT y los permisos (`IsGroupMember`, `IsGroupAdmin`) ya son correctos para Flutter.
- `CORS_ALLOWED_ORIGINS` ya está configurado (necesario solo para Flutter web).
