# Migración a Flutter + Django API REST

Análisis del estado actual del backend y consideraciones para usar Flutter como frontend móvil.

---

## Lo que ya está listo

La base de autenticación y la estructura API no necesitan rehacerse.

- **JWT con SimpleJWT**: access token (1h) + refresh (7 días) con rotación y blacklist. Flutter lo consume con un interceptor Dio que renueva el token automáticamente ante un 401.
- **Estructura `api/v1/`** separada de las web views: las rutas API y las rutas de templates coexisten sin conflicto.
- **Swagger en `/api/docs/`**: documentación generada automáticamente con drf-spectacular.
- **CORS configurado**: necesario para web builds de Flutter. En Flutter nativo (iOS/Android) CORS no aplica, pero conviene mantenerlo correcto.
- **Autenticación por Bearer token**: toda la API usa `JWTAuthentication`, no sesiones ni cookies.

### Endpoints de autenticación listos

```
POST /api/v1/auth/register/
POST /api/v1/auth/login/              → { access, refresh, user }
POST /api/v1/auth/token/refresh/      → { access, refresh }
POST /api/v1/auth/logout/             → blacklist del refresh token
POST /api/v1/auth/password-recovery/
POST /api/v1/auth/password-recovery/confirm/
GET  /api/v1/users/me/
```

---

## Funcionalidades sin endpoint API

El problema principal: una parte importante del negocio vive solo en `web_views.py` (vistas de templates Django) y no es consumible por Flutter. Todo lo siguiente necesita un `APIView` equivalente en `views.py`.

| Funcionalidad | Estado |
|---|---|
| Presupuesto personal (listar, crear, eliminar, filtrar por mes) | Solo en web_views |
| Crear movimiento personal directo | Solo en web_views |
| Corrección de monto de movimiento | Solo en web_views |
| Asistente de división (`split_confirm`) | Solo en web_views |
| Ahorros personales (crear meta, aportar, retirar, archivar) | Solo en web_views |
| Ahorros grupales | Solo en web_views |
| Gastos compartidos (listar pendientes, marcar pagado) | Solo en web_views |
| Conceptos personales (listar, crear, editar, eliminar) | Solo en web_views |
| Dashboard personal completo | Parcialmente en API |

El patrón a seguir es el ya establecido en `apps/finances/views.py` y `apps/groups/views.py`.

---

## Notificaciones en tiempo real

El SSE actual (`/notifications/sse/`) funciona en browser pero en Flutter es incómodo de mantener y no funciona en background. Opciones:

### Firebase Cloud Messaging (FCM) — recomendado
El más adecuado para móvil. Funciona en background sin consumir batería. Se integra en el backend enviando el push desde `crear_notificaciones_grupo` y desde cualquier `Notificacion.objects.create()`. Requiere agregar el FCM token del dispositivo al modelo de usuario.

### WebSockets con Django Channels
Más complejo: requiere Redis + configuración ASGI. Útil si se quiere bidireccionalidad real, pero para notificaciones FCM es suficiente.

### Polling desde Flutter — opción de corto plazo
Lo más simple para empezar. El endpoint ya existe:
```
GET /api/v1/notifications/?unread=true
```
Se llama periódicamente desde Flutter. Escala mal pero es válido para un MVP.

---

## Inconsistencias en la API actual a corregir

### Paginación no uniforme
Algunos endpoints usan `PageNumberPagination`, otros retornan listas planas. Flutter necesita un contrato consistente. Definir un tamaño de página estándar y aplicarlo a todos los endpoints de listado.

### Formato de errores inconsistente
Algunas vistas retornan `{'detail': '...'}`, otras `{'error': '...'}`. Estandarizar con un custom exception handler:

```python
# settings.py
REST_FRAMEWORK = {
    ...
    'EXCEPTION_HANDLER': 'apps.core.exceptions.custom_exception_handler',
}
```

### `referencia_id` en notificaciones sin contexto de grupo
El modelo `Notificacion` solo guarda un `referencia_id` (UUID del recurso) sin el `group_id` asociado. Esto ya causó un bug (el redirect de notificación de anuncio fallaba porque la URL requiere ambos IDs). El serializer de notificaciones debería enriquecer la respuesta con el contexto necesario para que Flutter pueda navegar directamente al recurso.

---

## Archivos y media

El módulo de documentos sube archivos a `MEDIA_ROOT` y Django los sirve directamente. Para Flutter en producción:

- **Corto plazo**: Django sirve los archivos. Funciona pero no escala.
- **Recomendado**: migrar a S3 (o compatible) con `django-storages`. Flutter descarga directamente desde S3 con URLs firmadas, sin pasar por el servidor Django.

---

## Flujo de autenticación en Flutter

```dart
// Almacenamiento seguro
final storage = FlutterSecureStorage();
await storage.write(key: 'access_token', value: response['access']);
await storage.write(key: 'refresh_token', value: response['refresh']);

// Interceptor Dio para renovación automática
interceptors.add(InterceptorsWrapper(
  onError: (error, handler) async {
    if (error.response?.statusCode == 401) {
      // Intentar refresh
      final refreshed = await refreshToken();
      if (refreshed) return handler.resolve(await retry(error.requestOptions));
      // Si falla, logout
    }
    handler.next(error);
  },
));
```

---

## Prioridades de implementación

### Corto plazo (sin cambios de arquitectura)
1. Crear los endpoints API faltantes en `views.py` para las features que solo están en `web_views.py`.
2. Estandarizar paginación y formato de errores en toda la API.
3. Enriquecer el serializer de `Notificacion` con contexto de navegación (tipo de recurso + IDs necesarios).

### Mediano plazo
4. Migrar archivos a S3 con `django-storages`.
5. Implementar FCM para notificaciones push en background.

### Lo que no necesita cambiar
- La estructura JWT está correctamente configurada.
- Los modelos no requieren cambios para soportar Flutter.
- Las `web_views.py` pueden coexistir en paralelo indefinidamente mientras se migra gradualmente.
