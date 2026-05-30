# Requerimientos del Proyecto — Finanzosos

> Versión: 1.1 — MVP  
> Fecha: 2026-05-29

---

## Índice

1. [Evaluación de las Historias de Usuario](#1-evaluación-de-las-historias-de-usuario)
2. [Requerimientos Funcionales](#2-requerimientos-funcionales)
3. [Requerimientos No Funcionales](#3-requerimientos-no-funcionales)
4. [Modelo de Datos](#4-modelo-de-datos)
5. [Especificaciones Técnicas](#5-especificaciones-técnicas)
6. [Especificaciones de Seguridad](#6-especificaciones-de-seguridad)

---

## 1. Evaluación de las Historias de Usuario

### 1.1 Resumen general

Las historias de usuario cubren los flujos principales de la aplicación y están bien estructuradas con escenarios Gherkin y criterios de aceptación. Se identificaron errores de consistencia, ambigüedades, texto copiado incorrectamente y brechas funcionales. **Todas las correcciones listadas a continuación están incorporadas en la Sección 2.**

### 1.2 Errores e inconsistencias corregidos

| ID | Historia | Tipo | Descripción | Corrección aplicada |
|----|----------|------|-------------|---------------------|
| E-01 | HU-01 | Criterio faltante | El Escenario 3 menciona el botón "Registrarme" pero no estaba en los criterios de aceptación. | Agregado como RF-01.4. |
| E-02 | HU-02 | Ambigüedad de diseño | El campo "Nombre del grupo" en el formulario de registro contradice la posibilidad de registrarse sin grupo (HU-07, HU-08). | Campo eliminado del formulario de registro. El grupo se gestiona exclusivamente en RF-08. |
| E-03 | HU-02 | Criterio incompleto | No se especificaba longitud mínima de contraseña. | Agregado "mínimo 8 caracteres" en RF-02.5. |
| E-04 | HU-03 | Inconsistencia de nombres | Gherkin usa "Enviar correo de recuperación" y los criterios usan "Recuperar contraseña" para el mismo botón. | Nombre unificado a "Enviar correo de recuperación" en RF-03. |
| E-05 | HU-03 | Errores tipográficos | "constraseña" y "contrasela" en los criterios. | Corregido en RF-03. |
| E-06 | HU-04 | Texto copiado incorrectamente | El Escenario 4 ("Acceder a mis ajustes") tenía el Gherkin del Escenario 3 ("Documentos"). | Corregido en RF-04. |
| E-07 | HU-04 | Referencias sin resolver | Los escenarios referenciaban "HU-XX" en lugar de las HUs concretas. | Resuelto en RF-04 apuntando a RF-09, RF-13 y RF-14. |
| E-08 | HU-05 | Comportamiento incorrecto | El Gherkin del Escenario 4 redirigía la notificación de nuevo anuncio a la pantalla de presupuesto. | Corregido en RF-05.5: redirige al detalle del anuncio. |
| E-09 | HU-05 | Criterio faltante | Los tipos de notificación no incluían notificaciones por nuevo ingreso, aunque HU-09 las requería. | Agregado en RF-05.1 y RF-05.9. |
| E-10 | HU-08 | Numeración duplicada | Tres escenarios distintos numerados como "Escenario 3". | Numeración corregida en RF-08. |
| E-11 | HU-08 | Resultado incorrecto en Gherkin | El escenario de "Quitar privilegios de administrador" decía "da privilegios" en vez de "quita". | Corregido en RF-08.5. |
| E-12 | HU-08 | Criterio contradictorio | Los criterios indicaban que el botón "Eliminar grupo" aparece para usuarios **no** administradores. | Corregido en RF-08.7: solo disponible para administradores. |
| E-13 | HU-09 | Numeración duplicada | Dos escenarios distintos numerados como "Escenario 5". | Reflejado correctamente en RF-09. |
| E-14 | HU-10 | Resultado incorrecto en Gherkin | El Escenario 3 de modificar presupuesto decía "se elimina" en lugar de "se modifica". | Corregido en RF-10.4. |
| E-15 | HU-11 | Inconsistencia de nombres | Los escenarios usan "Quitar" y los criterios usan "Eliminar" para el mismo botón. | Unificado a "Eliminar" en RF-11. |
| E-16 | HU-14 | Texto incorrecto en Gherkin | La notificación del Escenario 1 decía "el usuario subió un archivo" en un módulo de anuncios. | Corregido en RF-14.8. |

### 1.3 Brechas funcionales resueltas

| ID | Descripción | Decisión tomada |
|----|-------------|-----------------|
| B-01 | No existía HU para la pantalla "Ver todas mis notificaciones". | Definida como RF-05.7 y RF-05.8. |
| B-02 | No se especificaba si los conceptos son globales o por grupo. | Son por grupo (RF-11.1). |
| B-03 | No se definía qué ocurre con los datos al eliminar un grupo. | Se aplica soft delete: los datos quedan inactivos pero no se eliminan físicamente (RF-08.7). |
| B-04 | HU-07 solo mostraba datos de perfil sin opción de edición. | Edición de perfil fuera del alcance del MVP; declarado explícitamente en RF-07. |
| B-05 | No se especificaba si un usuario puede pertenecer a más de un grupo. | Un usuario pertenece a un solo grupo activo a la vez en el MVP (RF-08.9). |
| B-06 | Campo "Nombre del grupo" en el registro creaba ambigüedad arquitectónica. | Eliminado del registro. El grupo se crea o se une en RF-08 (ver también E-02). |
| B-07 | Comportamiento no definido cuando un usuario sin grupo accede a módulos de grupo. | Definido en RF-00.3. |
| B-08 | No había especificación de la pantalla de detalle de movimiento desde la Vista de Movimientos. | Definida en RF-12.5. |

---

## 2. Requerimientos Funcionales

### RF-00: Comportamiento transversal del sistema

| ID | Descripción |
|----|-------------|
| RF-00.1 | Si la sesión del usuario ha expirado y el access token no puede renovarse, el sistema debe redirigir al usuario a la pantalla de login con un mensaje informativo. |
| RF-00.2 | Los recursos soft-deleted (grupos eliminados, conceptos eliminados, documentos eliminados) no deben ser visibles ni accesibles por ningún usuario. |
| RF-00.3 | Si un usuario sin grupo intenta acceder a los módulos de Finanzas, Documentos o Anuncios, el sistema debe mostrar un mensaje que diga "Para acceder a este módulo necesitas pertenecer a un grupo" con un acceso directo a la Vista de Gestión de Grupo. |
| RF-00.4 | Todos los montos de la aplicación se expresan en pesos chilenos (CLP), son valores enteros positivos y se muestran con separador de miles (punto). |
| RF-00.5 | Todos los formatos de fecha y hora en la interfaz siguen el estándar `DD/MM/YYYY HH:MM`. |

### RF-01: Autenticación

| ID | Descripción |
|----|-------------|
| RF-01.1 | El sistema debe permitir al usuario iniciar sesión con nombre de usuario y contraseña. |
| RF-01.2 | Si las credenciales son incorrectas, se debe mostrar el mensaje "Usuario o contraseña inválidos" sin especificar cuál de los dos campos es incorrecto. |
| RF-01.3 | Tras un login exitoso, el sistema redirige al usuario al menú principal. |
| RF-01.4 | La pantalla de login debe incluir el botón "Registrarme" que redirige a la pantalla de registro (RF-02). |
| RF-01.5 | La pantalla de login debe incluir el botón "Olvidé mi contraseña" que redirige a la pantalla de recuperación (RF-03). |
| RF-01.6 | El sistema debe permitir cerrar sesión desde el menú principal. Al cerrar sesión se invalida la sesión activa y se redirige al login. |

### RF-02: Registro de usuario

| ID | Descripción |
|----|-------------|
| RF-02.1 | El formulario de registro solicita: correo electrónico, nombre de usuario, nombre, apellido, contraseña y confirmación de contraseña. |
| RF-02.2 | El sistema valida que el correo electrónico tenga formato válido (ej: `nombre@dominio.com`). |
| RF-02.3 | El sistema valida que el nombre de usuario no esté en uso. Si lo está, muestra: "Este nombre de usuario ya está en uso". |
| RF-02.4 | El sistema valida que el correo electrónico no esté en uso. Si lo está, muestra: "Este correo ya está en uso". |
| RF-02.5 | La contraseña debe cumplir: mínimo 8 caracteres, al menos una letra mayúscula, al menos una letra minúscula, al menos un dígito, al menos un carácter especial, no contener el nombre de usuario, no contener el nombre ni el apellido del usuario (comparación insensible a mayúsculas). Si no cumple, muestra: "La contraseña es insegura". |
| RF-02.6 | El sistema informa al usuario los criterios de contraseña con indicación visual en tiempo real (al escribir). |
| RF-02.7 | El campo contraseña que no cumple los criterios se marca con borde rojo. |
| RF-02.8 | Tras un registro exitoso, se muestra una pantalla de confirmación. El usuario registrado no pertenece a ningún grupo inicialmente. |
| RF-02.9 | El botón "Cancelar" redirige al usuario a la pantalla de login. |

### RF-03: Recuperación de contraseña

| ID | Descripción |
|----|-------------|
| RF-03.1 | La pantalla de recuperación solicita únicamente el correo electrónico del usuario. |
| RF-03.2 | El botón "Enviar correo de recuperación" se habilita solo cuando el campo tiene formato de correo electrónico válido. |
| RF-03.3 | Al hacer clic en "Enviar correo de recuperación", el sistema envía un correo al usuario con un enlace de recuperación y muestra el mensaje "Te enviamos un correo con el link de recuperación". |
| RF-03.4 | El enlace de recuperación expira en 10 minutos y solo puede usarse una vez. |
| RF-03.5 | Al acceder al enlace, el sistema muestra una pantalla solicitando nueva contraseña y confirmación de nueva contraseña. |
| RF-03.6 | La nueva contraseña debe cumplir los mismos criterios que RF-02.5. Si no los cumple, no se permite el cambio e indica al usuario qué criterio no se cumple. |
| RF-03.7 | Tras el cambio exitoso de contraseña, se informa al usuario y se muestra el botón "Ir al inicio" que redirige al login. |
| RF-03.8 | El botón "Cancelar" en la pantalla de recuperación redirige al usuario al login. |

### RF-04: Menú principal

| ID | Descripción |
|----|-------------|
| RF-04.1 | El menú principal muestra el saludo "Hola [Nombre] [Apellido], ¿Qué hay de nuevo hoy?" y debajo el nombre del grupo del usuario en cursiva y centrado. Si no pertenece a ningún grupo, muestra "Sin grupo". |
| RF-04.2 | El menú incluye botones de acceso a los módulos: Finanzas (RF-09), Anuncios (RF-14) y Documentos (RF-13). Los botones están dispuestos en una sola columna. |
| RF-04.3 | En la parte superior derecha de la pantalla se ubican, de izquierda a derecha: el botón de notificaciones (RF-05), el botón "Mis ajustes" (RF-07) y el botón "Cerrar sesión". |
| RF-04.4 | Al hacer clic en "Cerrar sesión" se termina la sesión y se redirige al login. |

### RF-05: Notificaciones

| ID | Descripción |
|----|-------------|
| RF-05.1 | Las notificaciones se generan para todos los miembros del grupo cuando ocurre: un nuevo gasto, un nuevo ingreso, una modificación al presupuesto, un nuevo anuncio o una invitación a grupo. |
| RF-05.2 | El botón de notificaciones es de color azul con ícono de campana y está ubicado en la parte superior derecha, a la izquierda de "Mis ajustes". |
| RF-05.3 | Al hacer clic en el botón de notificaciones, se despliega un panel con las notificaciones no leídas (título y fecha/hora) y al final una fila "Ver todas mis notificaciones". |
| RF-05.4 | Al hacer clic en una notificación de nuevo gasto o ingreso, redirige al detalle del movimiento. |
| RF-05.5 | Al hacer clic en una notificación de cambio en presupuesto, redirige a la Vista de Presupuesto. |
| RF-05.6 | Al hacer clic en una notificación de nuevo anuncio, redirige al detalle del anuncio. |
| RF-05.7 | Al hacer clic en una notificación de invitación a grupo, redirige a la pantalla de gestión de invitación. |
| RF-05.8 | Al hacer clic en "Ver todas mis notificaciones", se va a la pantalla de historial de notificaciones, paginada (10 por página), ordenada de más reciente a más antigua, con botón de paginación en la parte inferior. |
| RF-05.9 | Los títulos de las notificaciones según su tipo son los siguientes: nuevo gasto: "Se generó un gasto por [Monto] de [usuario] por [concepto]"; nuevo ingreso: "Se registró un ingreso por [Monto] de [usuario] por [concepto]"; cambio en presupuesto: "Se realizó un cambio en el presupuesto de [concepto]"; nuevo anuncio: "Se realizó el siguiente anuncio: [Título del anuncio]"; invitación a grupo: "El usuario [nombre de usuario emisor] te ha invitado al grupo [Nombre del grupo]". |

### RF-06: Gestión de invitaciones

| ID | Descripción |
|----|-------------|
| RF-06.1 | La pantalla de gestión de invitación muestra: nombre del grupo, comentario de la invitación, botón "Aceptar" (verde) y botón "Rechazar" (rojo). |
| RF-06.2 | Al hacer clic en "Aceptar": si el usuario no pertenece a ningún grupo, es agregado directamente. Si ya pertenece a un grupo, se muestra una confirmación indicando que abandonará su grupo actual; al confirmar, abandona el grupo previo y se une al nuevo. |
| RF-06.3 | Al hacer clic en "Rechazar", la invitación queda con estado rechazado y se informa al usuario. |
| RF-06.4 | Si un mismo emisor recibe dos rechazos del mismo receptor en un intervalo menor a una hora, ese emisor queda bloqueado para enviar nuevas invitaciones a ese receptor durante 24 horas. |

### RF-07: Mis ajustes

| ID | Descripción |
|----|-------------|
| RF-07.1 | La vista muestra la siguiente información del usuario: nombre de usuario, nombre, apellido y nombre del grupo ("Sin grupo" si no pertenece a ninguno). |
| RF-07.2 | La edición del perfil está fuera del alcance del MVP. La vista es de solo lectura. |
| RF-07.3 | Debe existir el botón "Gestionar Grupo" (azul) que redirige a la Vista de Gestión de Grupo (RF-08). |

### RF-08: Gestión de grupo

| ID | Descripción |
|----|-------------|
| RF-08.1 | Si el usuario no pertenece a ningún grupo, se muestra el mensaje "Aún no perteneces a ningún grupo" y el botón "Crear un nuevo grupo". |
| RF-08.2 | Crear un grupo requiere nombre y descripción. El creador recibe automáticamente el rol de administrador del grupo. |
| RF-08.3 | Si el usuario pertenece a un grupo, la vista muestra: nombre del grupo, descripción y listado de miembros con su rol. |
| RF-08.4 | Un administrador puede invitar a otros usuarios buscando por nombre de usuario e incluyendo un comentario. El sistema informa que la invitación fue enviada exitosamente. |
| RF-08.5 | Un administrador puede otorgar o revocar el rol de administrador a cualquier otro miembro, con confirmación previa. Al revocar, el botón de la fila cambia de "Quitar Admin" a "Hacer Admin" y viceversa. |
| RF-08.6 | Un administrador puede expulsar a cualquier miembro no administrador con confirmación previa. El sistema informa que el usuario fue expulsado. |
| RF-08.7 | Un administrador puede eliminar el grupo con confirmación previa. Al eliminarse, todos los miembros quedan sin grupo; el grupo y sus datos asociados quedan inactivos (soft delete), no se eliminan físicamente. |
| RF-08.8 | Un usuario no administrador puede abandonar el grupo con confirmación previa. El sistema informa que el usuario abandonó el grupo. |
| RF-08.9 | Un usuario no administrador solo puede visualizar la información del grupo, sin botones de modificación. Al final de su vista aparece únicamente el botón "Abandonar grupo". |
| RF-08.10 | Para el MVP, un usuario pertenece a un único grupo activo a la vez. |

### RF-09: Módulo de Finanzas

| ID | Descripción |
|----|-------------|
| RF-09.1 | El módulo es una vista compartida por todos los miembros del grupo. |
| RF-09.2 | Al ingresar se muestran los siguientes indicadores financieros del mes en curso: **Gasto acumulado mensual** (suma de todos los gastos del mes), **Saldo restante** (suma de ingresos menos suma de gastos del mes) y **Desviación del presupuesto** (suma de los montos del presupuesto hasta la fecha actual del mes menos los gastos hasta esa misma fecha). |
| RF-09.3 | Se muestra un gráfico de torta con los gastos del mes agrupados por concepto. Si hay más de 5 conceptos, los de menor monto se agrupan en un segmento llamado "Otros". |
| RF-09.4 | Se muestran los últimos 5 movimientos (ingresos y gastos) en una tabla con columnas: Concepto, Monto, Usuario, Fecha y hora, y botón "Ver detalle". |
| RF-09.5 | El formulario de nuevo gasto solicita: Nombre (obligatorio), Detalle (opcional), Concepto de tipo Gasto (obligatorio, lista desplegable), Monto (obligatorio). El registro incluye automáticamente el nombre del usuario y la fecha y hora del ingreso. |
| RF-09.6 | El formulario de nuevo ingreso solicita: Nombre (obligatorio), Detalle (opcional), Concepto de tipo Ingreso (obligatorio, lista desplegable), Monto (obligatorio). El registro incluye automáticamente el nombre del usuario y la fecha y hora del ingreso. |
| RF-09.7 | Al registrar un gasto o un ingreso, se notifica a todos los miembros del grupo (ver RF-05.9). |
| RF-09.8 | El botón "Exportar" genera y descarga un archivo `.csv` con todos los movimientos históricos del grupo. El archivo usa separador `;` y encoding UTF-8 con BOM. Columnas: Tipo, Concepto, Nombre, Detalle, Monto, Usuario, Fecha y hora. |
| RF-09.9 | La disposición de los elementos es: botones "Gestionar Presupuesto" (azul), "Conceptos" (azul) y "Exportar" (verde) en la parte superior izquierda; indicadores financieros en la parte superior; gráfico de torta debajo de los indicadores; tabla de últimos movimientos debajo del gráfico; barra inferior con las secciones "Añadir Gasto", "Ver movimientos" y "Añadir Ingreso". |
| RF-09.10 | El botón "Ver detalle" de un movimiento muestra: Nombre, Concepto, Detalle, Monto, Usuario y Fecha y hora. |

### RF-10: Vista de Presupuesto

| ID | Descripción |
|----|-------------|
| RF-10.1 | La vista es compartida por todos los miembros del grupo. |
| RF-10.2 | Se muestra una tabla con los registros de presupuesto del grupo. Columnas: Concepto y Monto. La última fila muestra el total de la columna Monto. |
| RF-10.3 | Por cada fila existen los botones "Modificar" y "Eliminar" al final de la fila. El botón "Agregar" está en la parte superior derecha y el botón "Atrás" en la parte superior izquierda. |
| RF-10.4 | El formulario de nuevo registro solicita: Tipo (Gasto/Ingreso, obligatorio), Concepto dependiente del tipo (obligatorio), Nombre (obligatorio), Detalle (opcional), Fecha (obligatorio), Monto (obligatorio). |
| RF-10.5 | Al hacer clic en "Modificar", se despliega un formulario donde **solo se puede cambiar el Monto**. Los demás campos son de solo lectura. |
| RF-10.6 | Al hacer clic en "Eliminar", se solicita confirmación previa. |
| RF-10.7 | Al modificar o eliminar un registro de presupuesto, se notifica a los miembros del grupo. |
| RF-10.8 | El botón "Atrás" redirige al Módulo de Finanzas. |

### RF-11: Vista de Conceptos

| ID | Descripción |
|----|-------------|
| RF-11.1 | Los conceptos son de tipo Gasto o Ingreso y son específicos por grupo. |
| RF-11.2 | La vista muestra una tabla con columnas: Nombre, Tipo, botón "Editar" y botón "Eliminar". El botón "Agregar" está en la parte superior derecha y el botón "Atrás" en la parte superior izquierda. |
| RF-11.3 | El formulario de nuevo concepto solicita: Nombre (obligatorio) y Tipo (obligatorio). |
| RF-11.4 | Al hacer clic en "Editar", se despliega un formulario donde **solo se puede modificar el Nombre** del concepto. |
| RF-11.5 | Al hacer clic en "Eliminar" en un concepto **sin** movimientos asociados, se solicita confirmación y se elimina. |
| RF-11.6 | Al hacer clic en "Eliminar" en un concepto **con** movimientos asociados, el sistema informa la situación y ofrece dos opciones: (a) **"Eliminar movimientos asociados"**: elimina el concepto y todos sus movimientos; (b) **"Mantener movimientos"**: elimina el concepto y deja los movimientos asociados con el campo concepto como `NULL` (se mostrará como "Desconocido" en la interfaz). |
| RF-11.7 | El botón "Atrás" redirige al Módulo de Finanzas. |

### RF-12: Vista de Movimientos

| ID | Descripción |
|----|-------------|
| RF-12.1 | La vista es compartida por todos los miembros del grupo. |
| RF-12.2 | Se muestra el listado de todos los movimientos paginado (máximo 15 por página), ordenado de forma descendente por fecha y hora. El botón de paginación está en la parte inferior de la pantalla. |
| RF-12.3 | Columnas de la tabla: Tipo, Concepto, Nombre, Monto, Usuario, Fecha y hora, y botón "Ver detalle". |
| RF-12.4 | Debe existir un filtro por concepto (lista desplegable con los conceptos del grupo). |
| RF-12.5 | Al hacer clic en "Ver detalle", se muestra la información completa del movimiento: Tipo, Nombre, Concepto, Detalle, Monto, Usuario y Fecha y hora. |

### RF-13: Módulo de Documentos

| ID | Descripción |
|----|-------------|
| RF-13.1 | El módulo es una vista compartida por todos los miembros del grupo. |
| RF-13.2 | Se muestra un listado de documentos con: Nombre, Descripción, Fecha de subida y Usuario. |
| RF-13.3 | El formulario de subida (botón "Agregar") solicita: Nombre, Archivo adjunto y Descripción. |
| RF-13.4 | Los formatos permitidos son exclusivamente: `.pdf`, `.csv`, `.xlsx` y `.png`. El sistema valida por extensión y por tipo MIME. |
| RF-13.5 | Un documento solo puede ser eliminado por el usuario que lo subió, con confirmación previa. |
| RF-13.6 | Al subir un documento, se notifica a los miembros del grupo. |

### RF-14: Módulo de Anuncios

| ID | Descripción |
|----|-------------|
| RF-14.1 | El módulo es una vista compartida por todos los miembros del grupo. |
| RF-14.2 | Se muestra un listado de anuncios con: Nombre, Descripción, Fecha de creación y Usuario. |
| RF-14.3 | El formulario de creación (botón "Crear anuncio") solicita: Nombre y Descripción. El botón para publicar se llama "Publicar". |
| RF-14.4 | Por cada anuncio existe el botón "Ver". Si el anuncio fue creado por el usuario visualizador, también aparece el botón "Eliminar". |
| RF-14.5 | Al hacer clic en "Ver" se accede al detalle del anuncio. El detalle incluye Nombre, Descripción, Fecha, Usuario y una sección de comentarios. |
| RF-14.6 | En la sección de comentarios del detalle hay una caja de texto y el botón "Comentar" que publica el comentario. Los comentarios solo son visibles en la vista de detalle. |
| RF-14.7 | Un anuncio solo puede ser eliminado por el usuario que lo creó. La eliminación no requiere confirmación. |
| RF-14.8 | Al crear un anuncio, se notifica a los miembros del grupo indicando que se creó un nuevo anuncio (ver RF-05.9). |

---

## 3. Requerimientos No Funcionales

### RNF-01: Usabilidad

| ID | Descripción |
|----|-------------|
| RNF-01.1 | La interfaz debe ser **mobile-first**: diseñada y optimizada primero para pantallas de teléfonos inteligentes (ancho mínimo de referencia: 375px), y adaptada a pantallas más grandes de forma responsiva. |
| RNF-01.2 | La paleta de colores debe usar verde naturaleza como color primario, azul para botones de acción y acceso a módulos, rojo para acciones destructivas y verde para confirmaciones. |
| RNF-01.3 | Todos los formularios deben validar los campos en tiempo real (al perder foco o al escribir) e informar errores de forma clara, específica y accesible. |
| RNF-01.4 | Las acciones destructivas o irreversibles (eliminar grupo, expulsar miembro, eliminar concepto con movimientos) deben requerir una confirmación explícita del usuario mediante un modal con botones "Aceptar" y "Cancelar". |
| RNF-01.5 | Los tiempos de carga de pantalla no deben superar los 3 segundos en una conexión 4G estándar. |
| RNF-01.6 | Los textos de la interfaz deben estar en español (Chile). Los formatos de fecha siguen el estándar `DD/MM/YYYY HH:MM`. |
| RNF-01.7 | Los mensajes de error del sistema (validación de formularios, errores de red) deben ser en español, claros y orientados al usuario, sin exponer información técnica interna. |

### RNF-02: Rendimiento

| ID | Descripción |
|----|-------------|
| RNF-02.1 | El tiempo de respuesta de la API para operaciones de lectura no debe superar los 1.5 segundos bajo carga normal (hasta 50 usuarios concurrentes en el MVP). |
| RNF-02.2 | El tiempo de respuesta para operaciones de escritura (registro de movimientos, anuncios, documentos) no debe superar los 2 segundos. |
| RNF-02.3 | Los listados de movimientos, notificaciones y documentos deben implementar paginación en el servidor. El cliente nunca debe cargar la totalidad de registros en memoria. |
| RNF-02.4 | Las consultas a la base de datos deben usar índices sobre los campos frecuentemente filtrados: `grupo_id`, `usuario_id`, `tipo`, `fecha_hora`. |

### RNF-03: Disponibilidad y confiabilidad

| ID | Descripción |
|----|-------------|
| RNF-03.1 | La disponibilidad objetivo para el MVP es del **99%** mensual, excluyendo ventanas de mantenimiento programadas y comunicadas con anticipación. |
| RNF-03.2 | Se deben realizar respaldos diarios automatizados de la base de datos con retención mínima de 7 días. |
| RNF-03.3 | El sistema debe capturar y registrar errores internos en logs de servidor, mostrando al usuario únicamente mensajes genéricos sin trazas de error. |

### RNF-04: Escalabilidad

| ID | Descripción |
|----|-------------|
| RNF-04.1 | La arquitectura del MVP debe soportar hasta **200 usuarios registrados** y **50 usuarios concurrentes** sin degradación significativa del rendimiento. |
| RNF-04.2 | La separación entre frontend (SPA) y backend (API REST) debe permitir escalar ambas capas de forma independiente en versiones posteriores. |

### RNF-05: Mantenibilidad

| ID | Descripción |
|----|-------------|
| RNF-05.1 | El código fuente debe estar versionado en un repositorio git con ramas organizadas: `main`, `develop` y `feature/*`. |
| RNF-05.2 | La API debe estar documentada en formato OpenAPI (Swagger), generada automáticamente con `drf-spectacular`. |
| RNF-05.3 | Las variables de entorno sensibles (credenciales de base de datos, claves de API, secret key de Django) deben gestionarse mediante archivos `.env` y nunca commitearse al repositorio. |
| RNF-05.4 | El proyecto debe incluir un archivo `requirements/` con dependencias separadas para desarrollo y producción. |

### RNF-06: Compatibilidad

| ID | Descripción |
|----|-------------|
| RNF-06.1 | La aplicación debe funcionar correctamente en las últimas dos versiones de los navegadores: Chrome (Android e iOS), Safari (iOS) y Firefox. |
| RNF-06.2 | La interfaz debe ser responsiva y usable en pantallas desde 375px hasta 1440px de ancho. |

---

## 4. Modelo de Datos

El modelo usa UUID v4 como clave primaria en todas las entidades para evitar exposición de secuencias internas. En Django, esto se implementa con `UUIDField(primary_key=True, default=uuid.uuid4, editable=False)`.

Los campos `created_at` y `updated_at` usan `DateTimeField(auto_now_add=True)` y `DateTimeField(auto_now=True)` respectivamente.

### 4.1 Entidades

#### `users` — Modelo de usuario (`AbstractUser`)

Se extiende `django.contrib.auth.models.AbstractUser`. Los campos `first_name`, `last_name`, `email` y `password` ya forman parte de `AbstractUser`; se agregan los campos propios del proyecto.

| Campo | Tipo Django | Restricciones | Descripción |
|-------|-------------|---------------|-------------|
| id | UUIDField (PK) | default=uuid4 | Identificador único |
| username | CharField(50) | unique | Nombre de usuario para login |
| email | EmailField | unique | Correo electrónico |
| first_name | CharField(100) | — | Nombre (heredado de AbstractUser) |
| last_name | CharField(100) | — | Apellido (heredado de AbstractUser) |
| password | CharField | — | Hash de contraseña (manejado por Django) |
| created_at | DateTimeField | auto_now_add | Fecha de creación |
| updated_at | DateTimeField | auto_now | Fecha de última modificación |

> En `settings.py`: `AUTH_USER_MODEL = 'users.User'`. Debe definirse antes de la primera migración.

#### `groups` — Grupos

| Campo | Tipo Django | Restricciones | Descripción |
|-------|-------------|---------------|-------------|
| id | UUIDField (PK) | default=uuid4 | Identificador único |
| nombre | CharField(100) | not null | Nombre del grupo |
| descripcion | TextField | blank=True | Descripción del grupo |
| activo | BooleanField | default=True | False cuando el grupo es eliminado (soft delete) |
| created_at | DateTimeField | auto_now_add | Fecha de creación |
| updated_at | DateTimeField | auto_now | Fecha de última modificación |

> Se recomienda un `Manager` personalizado que filtre `activo=True` por defecto.

#### `group_members` — Membresías (tabla pivote)

| Campo | Tipo Django | Restricciones | Descripción |
|-------|-------------|---------------|-------------|
| id | UUIDField (PK) | default=uuid4 | Identificador único |
| user | ForeignKey(User) | on_delete=CASCADE | Usuario miembro |
| group | ForeignKey(Group) | on_delete=CASCADE | Grupo |
| rol | CharField(10) | choices: admin/miembro | Rol dentro del grupo |
| created_at | DateTimeField | auto_now_add | Fecha de incorporación |

> Restricción de unicidad: `unique_together = ('user', 'group')`.

#### `concepts` — Conceptos

| Campo | Tipo Django | Restricciones | Descripción |
|-------|-------------|---------------|-------------|
| id | UUIDField (PK) | default=uuid4 | Identificador único |
| nombre | CharField(100) | not null | Nombre del concepto |
| tipo | CharField(10) | choices: Gasto/Ingreso | Tipo del concepto |
| group | ForeignKey(Group) | on_delete=CASCADE | Grupo propietario |
| activo | BooleanField | default=True | Soft delete |
| created_at | DateTimeField | auto_now_add | Fecha de creación |

#### `movements` — Movimientos

| Campo | Tipo Django | Restricciones | Descripción |
|-------|-------------|---------------|-------------|
| id | UUIDField (PK) | default=uuid4 | Identificador único |
| tipo | CharField(10) | choices: Gasto/Ingreso | Tipo de movimiento |
| nombre | CharField(255) | not null | Nombre descriptivo |
| detalle | TextField | blank=True | Detalle opcional |
| monto | PositiveIntegerField | not null | Monto en CLP (sin decimales) |
| concept | ForeignKey(Concept) | on_delete=SET_NULL, null=True | NULL si el concepto fue eliminado con "Mantener movimientos" |
| user | ForeignKey(User) | on_delete=PROTECT | Usuario que lo registró |
| group | ForeignKey(Group) | on_delete=CASCADE | Grupo al que pertenece |
| fecha_hora | DateTimeField | not null | Fecha y hora del movimiento |
| created_at | DateTimeField | auto_now_add | Fecha de registro en el sistema |

> Índices recomendados: `group` + `fecha_hora` (para listados paginados), `group` + `tipo`.

#### `budget_records` — Registros de presupuesto

| Campo | Tipo Django | Restricciones | Descripción |
|-------|-------------|---------------|-------------|
| id | UUIDField (PK) | default=uuid4 | Identificador único |
| tipo | CharField(10) | choices: Gasto/Ingreso | Tipo |
| concept | ForeignKey(Concept) | on_delete=PROTECT | Concepto presupuestado |
| nombre | CharField(255) | not null | Nombre del registro |
| detalle | TextField | blank=True | Detalle opcional |
| monto | PositiveIntegerField | not null | Monto en CLP |
| fecha | DateField | not null | Fecha del registro de presupuesto |
| group | ForeignKey(Group) | on_delete=CASCADE | Grupo al que pertenece |
| created_at | DateTimeField | auto_now_add | Fecha de creación |
| updated_at | DateTimeField | auto_now | Fecha de última modificación |

#### `documents` — Documentos

| Campo | Tipo Django | Restricciones | Descripción |
|-------|-------------|---------------|-------------|
| id | UUIDField (PK) | default=uuid4 | Identificador único |
| nombre | CharField(255) | not null | Nombre del documento |
| descripcion | TextField | blank=True | Descripción |
| archivo | FileField | upload_to='documents/' | Archivo almacenado |
| tipo_archivo | CharField(10) | not null | Extensión validada (pdf, csv, xlsx, png) |
| tamano_bytes | PositiveIntegerField | — | Tamaño del archivo |
| user | ForeignKey(User) | on_delete=PROTECT | Usuario que lo subió |
| group | ForeignKey(Group) | on_delete=CASCADE | Grupo al que pertenece |
| activo | BooleanField | default=True | Soft delete |
| created_at | DateTimeField | auto_now_add | Fecha de subida |

#### `announcements` — Anuncios

| Campo | Tipo Django | Restricciones | Descripción |
|-------|-------------|---------------|-------------|
| id | UUIDField (PK) | default=uuid4 | Identificador único |
| nombre | CharField(255) | not null | Título del anuncio |
| descripcion | TextField | not null | Contenido del anuncio |
| user | ForeignKey(User) | on_delete=PROTECT | Usuario creador |
| group | ForeignKey(Group) | on_delete=CASCADE | Grupo al que pertenece |
| activo | BooleanField | default=True | Soft delete |
| created_at | DateTimeField | auto_now_add | Fecha de creación |

#### `comments` — Comentarios de anuncios

| Campo | Tipo Django | Restricciones | Descripción |
|-------|-------------|---------------|-------------|
| id | UUIDField (PK) | default=uuid4 | Identificador único |
| contenido | TextField | not null | Texto del comentario |
| announcement | ForeignKey(Announcement) | on_delete=CASCADE | Anuncio al que pertenece |
| user | ForeignKey(User) | on_delete=PROTECT | Usuario comentador |
| created_at | DateTimeField | auto_now_add | Fecha de creación |

#### `notifications` — Notificaciones

| Campo | Tipo Django | Restricciones | Descripción |
|-------|-------------|---------------|-------------|
| id | UUIDField (PK) | default=uuid4 | Identificador único |
| titulo | CharField(500) | not null | Texto descriptivo |
| tipo | CharField(20) | choices: gasto/ingreso/presupuesto/anuncio/invitacion | Tipo de notificación |
| referencia_id | UUIDField | null=True | ID del objeto referenciado |
| user | ForeignKey(User) | on_delete=CASCADE | Usuario destinatario |
| leida | BooleanField | default=False | Estado de lectura |
| created_at | DateTimeField | auto_now_add | Fecha de generación |

> Índice recomendado: `user` + `leida` (para el panel de notificaciones no leídas).

#### `invitations` — Invitaciones a grupos

| Campo | Tipo Django | Restricciones | Descripción |
|-------|-------------|---------------|-------------|
| id | UUIDField (PK) | default=uuid4 | Identificador único |
| emisor | ForeignKey(User, related_name='sent_invitations') | on_delete=CASCADE | Usuario emisor |
| receptor | ForeignKey(User, related_name='received_invitations') | on_delete=CASCADE | Usuario receptor |
| group | ForeignKey(Group) | on_delete=CASCADE | Grupo al que se invita |
| comentario | TextField | blank=True | Mensaje de la invitación |
| estado | CharField(15) | choices: pendiente/aceptada/rechazada, default=pendiente | Estado actual |
| created_at | DateTimeField | auto_now_add | Fecha de envío |
| updated_at | DateTimeField | auto_now | Fecha de última actualización |

#### `password_reset_tokens` — Tokens de recuperación de contraseña

| Campo | Tipo Django | Restricciones | Descripción |
|-------|-------------|---------------|-------------|
| id | UUIDField (PK) | default=uuid4 | Identificador único |
| user | ForeignKey(User) | on_delete=CASCADE | Usuario propietario |
| token_hash | CharField(255) | unique | Hash SHA-256 del token enviado por correo |
| expira_en | DateTimeField | not null | `created_at + 10 minutos` |
| usado | BooleanField | default=False | True después de ser utilizado |
| created_at | DateTimeField | auto_now_add | Fecha de creación |

### 4.2 Relaciones principales

```
User ──< GroupMember >── Group
Group ──< Concept
Group ──< Movement >── Concept (nullable)
Group ──< BudgetRecord >── Concept
Group ──< Document >── User
Group ──< Announcement >── User
Announcement ──< Comment >── User
User ──< Notification
User ──< Invitation (emisor/receptor) >── Group
User ──< PasswordResetToken
```

---

## 5. Especificaciones Técnicas

### 5.1 Stack tecnológico

#### Frontend

| Componente | Tecnología | Versión mínima |
|------------|------------|----------------|
| Framework | React + Vite | React 18, Vite 5 |
| Estilos | Tailwind CSS | v3 |
| Enrutamiento | React Router | v6 |
| Estado del servidor | TanStack Query (React Query) | v5 |
| Gráficos | Recharts | v2 |
| Cliente HTTP | Axios | v1 |

#### Backend

| Componente | Tecnología | Versión mínima |
|------------|------------|----------------|
| Framework | Django | 5.x |
| API REST | Django REST Framework (DRF) | 3.15+ |
| Autenticación JWT | djangorestframework-simplejwt | 5.x |
| CORS | django-cors-headers | 4.x |
| Documentación API | drf-spectacular | 0.27+ |
| Correo electrónico | django-anymail (SendGrid/Mailgun) | 10.x |
| Almacenamiento de archivos | django-storages | 1.14+ |
| Protección de fuerza bruta | django-axes | 6.x |
| Validación MIME de archivos | python-magic | 0.4+ |
| Procesamiento de imágenes | Pillow | 10.x |

#### Base de datos

| Componente | Tecnología | Versión mínima |
|------------|------------|----------------|
| Motor | PostgreSQL | 15 |
| Adaptador | psycopg2-binary | 2.9+ |
| Migraciones | Django Migrations (built-in) | — |

#### Almacenamiento de archivos

Para el MVP se configura almacenamiento local mediante `MEDIA_ROOT` y `MEDIA_URL` en Django. El backend de almacenamiento se define vía `DEFAULT_FILE_STORAGE` en `settings.py`, lo que permite migrar a S3 (`storages.backends.s3boto3.S3Boto3Storage`) sin modificar el código de la aplicación.

### 5.2 Estructura del proyecto Django

```
finanzosos/
├── config/
│   ├── settings/
│   │   ├── base.py          # Configuración compartida
│   │   ├── development.py   # DEBUG=True, SQLite o PostgreSQL local
│   │   └── production.py    # HTTPS, S3, logging, etc.
│   ├── urls.py              # Router raíz: /api/v1/ y /admin/
│   └── wsgi.py
├── apps/
│   ├── users/               # Modelo User, registro, autenticación
│   ├── groups/              # Group, GroupMember, Invitation
│   ├── finances/            # Movement, BudgetRecord, Concept
│   ├── documents/           # Document
│   ├── announcements/       # Announcement, Comment
│   └── notifications/       # Notification
├── requirements/
│   ├── base.txt
│   ├── development.txt
│   └── production.txt
└── manage.py
```

### 5.3 Configuración clave de Django (`config/settings/base.py`)

```python
AUTH_USER_MODEL = 'users.User'

INSTALLED_APPS = [
    # Django built-ins
    'django.contrib.admin',
    'django.contrib.auth',
    ...
    # Third-party
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    'drf_spectacular',
    'axes',
    # Project apps
    'apps.users',
    'apps.groups',
    'apps.finances',
    'apps.documents',
    'apps.announcements',
    'apps.notifications',
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 15,
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
}

PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.BCryptSHA256PasswordHasher',  # Primero: bcrypt
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',        # Fallback
]
```

### 5.4 Validadores de contraseña (`AUTH_PASSWORD_VALIDATORS`)

```python
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
     'OPTIONS': {'min_length': 8}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    # Validadores custom del proyecto:
    {'NAME': 'apps.users.validators.HasUppercaseValidator'},
    {'NAME': 'apps.users.validators.HasLowercaseValidator'},
    {'NAME': 'apps.users.validators.HasDigitValidator'},
    {'NAME': 'apps.users.validators.HasSpecialCharValidator'},
    {'NAME': 'apps.users.validators.NotContainsUserInfoValidator'},
]
```

### 5.5 Arquitectura general

```
┌──────────────────────────────────────┐
│          Cliente (SPA React)          │
│        [Navegador móvil/web]          │
└───────────────┬──────────────────────┘
                │ HTTPS / REST API (JSON)
                ▼
┌──────────────────────────────────────┐
│       Django + DRF (API REST)         │
│  JWT Auth · DRF Serializers · Views  │
│  Django ORM · Django Signals         │
│  Django Admin · django-axes           │
└──────┬───────────────────────┬───────┘
       │                       │
       ▼                       ▼
┌─────────────┐      ┌──────────────────┐
│ PostgreSQL  │      │  Almacenamiento  │
│   15+       │      │  de archivos     │
│  (datos)    │      │  (local / S3)    │
└─────────────┘      └──────────────────┘
```

### 5.6 Endpoints de la API REST

Todas las rutas requieren el header `Authorization: Bearer <access_token>`, excepto las de autenticación y recuperación.

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/api/v1/auth/login/` | Iniciar sesión → devuelve access + refresh token |
| POST | `/api/v1/auth/register/` | Registrar nuevo usuario |
| POST | `/api/v1/auth/logout/` | Cerrar sesión (blacklist del refresh token) |
| POST | `/api/v1/auth/token/refresh/` | Renovar access token con refresh token |
| POST | `/api/v1/auth/password-recovery/` | Solicitar correo de recuperación |
| POST | `/api/v1/auth/password-recovery/confirm/` | Confirmar nueva contraseña con token |
| GET | `/api/v1/users/me/` | Obtener datos del usuario autenticado |
| GET | `/api/v1/groups/my-group/` | Obtener grupo del usuario con sus miembros |
| POST | `/api/v1/groups/` | Crear un grupo |
| DELETE | `/api/v1/groups/{id}/` | Eliminar el grupo (admin) |
| POST | `/api/v1/groups/{id}/invite/` | Enviar invitación a usuario (admin) |
| POST | `/api/v1/groups/{id}/remove-member/` | Expulsar miembro (admin) |
| POST | `/api/v1/groups/{id}/set-role/` | Cambiar rol de un miembro (admin) |
| POST | `/api/v1/groups/{id}/leave/` | Abandonar el grupo (miembro no admin) |
| GET | `/api/v1/invitations/` | Listar invitaciones pendientes del usuario |
| POST | `/api/v1/invitations/{id}/accept/` | Aceptar invitación |
| POST | `/api/v1/invitations/{id}/reject/` | Rechazar invitación |
| GET/POST | `/api/v1/groups/{id}/concepts/` | Listar / crear conceptos |
| PUT/DELETE | `/api/v1/groups/{id}/concepts/{cid}/` | Editar / eliminar concepto |
| POST | `/api/v1/groups/{id}/concepts/{cid}/delete-with-movements/` | Eliminar concepto y elegir qué hacer con sus movimientos |
| GET/POST | `/api/v1/groups/{id}/movements/` | Listar / crear movimientos (con filtro por concepto y paginación) |
| GET | `/api/v1/groups/{id}/movements/{mid}/` | Detalle de un movimiento |
| GET | `/api/v1/groups/{id}/movements/export/` | Exportar CSV de movimientos |
| GET/POST | `/api/v1/groups/{id}/budget/` | Listar / crear registros de presupuesto |
| PATCH/DELETE | `/api/v1/groups/{id}/budget/{bid}/` | Modificar monto / eliminar registro |
| GET/POST | `/api/v1/groups/{id}/documents/` | Listar / subir documentos |
| DELETE | `/api/v1/groups/{id}/documents/{did}/` | Eliminar documento (solo el creador) |
| GET/POST | `/api/v1/groups/{id}/announcements/` | Listar / crear anuncios |
| GET/DELETE | `/api/v1/groups/{id}/announcements/{aid}/` | Ver detalle / eliminar anuncio |
| POST | `/api/v1/groups/{id}/announcements/{aid}/comments/` | Agregar comentario a un anuncio |
| GET | `/api/v1/notifications/` | Listar notificaciones (con filtro `unread=true`) |
| POST | `/api/v1/notifications/{nid}/read/` | Marcar una notificación como leída |
| POST | `/api/v1/notifications/read-all/` | Marcar todas como leídas |

### 5.7 Generación de notificaciones

Para el MVP las notificaciones se generan de forma **sincrónica** mediante Django Signals (`post_save`) o llamadas explícitas en la capa de servicio, evitando la complejidad de Celery. Al crear un `Movement`, `BudgetRecord`, `Announcement` o `Invitation`, se itera sobre los miembros del grupo y se crea un registro `Notification` por cada uno.

### 5.8 Exportación CSV

El endpoint de exportación genera el archivo en memoria con `csv.writer` de la librería estándar de Python, configurado con separador `;` y codificación UTF-8 con BOM (`utf-8-sig`). La respuesta HTTP usa `Content-Type: text/csv; charset=utf-8` y el header `Content-Disposition: attachment; filename="movimientos.csv"`.

---

## 6. Especificaciones de Seguridad

### 6.1 Autenticación y sesiones

| ID | Especificación |
|----|----------------|
| SEG-01 | Las contraseñas se almacenan como hash bcrypt. Se configura `BCryptSHA256PasswordHasher` como primer hasher en `PASSWORD_HASHERS`. Nunca en texto plano. |
| SEG-02 | Los JWT se firman con el algoritmo `HS256` usando `SECRET_KEY` de Django, que nunca debe estar en el código fuente. En producción se recomienda `RS256`. |
| SEG-03 | El refresh token debe enviarse al cliente en una cookie con flags `HttpOnly`, `Secure` y `SameSite=Strict` para protegerlo de acceso por JavaScript. |
| SEG-04 | Los tokens de recuperación de contraseña se almacenan como hash SHA-256 en la tabla `password_reset_tokens`. El token en texto plano solo viaja en el correo electrónico. |
| SEG-05 | Al cerrar sesión, el refresh token se agrega a la blacklist de `rest_framework_simplejwt.token_blacklist`. |
| SEG-06 | Se configura `django-axes` para bloquear accesos después de 5 intentos fallidos por IP en los endpoints `/api/v1/auth/login/` y `/api/v1/auth/password-recovery/`. El bloqueo dura 15 minutos. |

### 6.2 Autorización

| ID | Especificación |
|----|----------------|
| SEG-07 | Se implementan permisos DRF personalizados: `IsGroupMember` (valida que el usuario pertenece al grupo del recurso solicitado) y `IsGroupAdmin` (valida que el usuario tiene rol `admin` en el grupo). |
| SEG-08 | Todo acceso a recursos de grupo (movimientos, presupuesto, documentos, anuncios, conceptos) verifica `IsGroupMember` antes de procesar la solicitud. |
| SEG-09 | Las operaciones de administrador (invitar, expulsar, cambiar rol, eliminar grupo) verifican `IsGroupAdmin`. |
| SEG-10 | La eliminación de documentos y anuncios usa un permiso `IsOwner` que verifica que `request.user == objeto.user`. |
| SEG-11 | Los IDs de grupo en la URL nunca se asumen válidos sin consultar la membresía del usuario en la base de datos. |

### 6.3 Política de contraseñas

| Criterio | Regla |
|----------|-------|
| Longitud mínima | 8 caracteres |
| Mayúsculas | Al menos una letra mayúscula |
| Minúsculas | Al menos una letra minúscula |
| Números | Al menos un dígito |
| Caracteres especiales | Al menos uno de: `!@#$%^&*()_+-=[]{}|;':",./<>?` |
| Prohibiciones | No debe contener el username, el nombre ni el apellido del usuario (comparación case-insensitive) |

Los validadores personalizados se implementan en `apps/users/validators.py` y se registran en `AUTH_PASSWORD_VALIDATORS`.

### 6.4 Comunicaciones y transporte

| ID | Especificación |
|----|----------------|
| SEG-12 | Toda comunicación entre cliente y servidor debe realizarse exclusivamente por HTTPS (TLS 1.2 mínimo). En producción se configura `SECURE_SSL_REDIRECT = True` y `SECURE_HSTS_SECONDS = 31536000`. |
| SEG-13 | Configurar en Django las cabeceras de seguridad: `SECURE_CONTENT_TYPE_NOSNIFF = True`, `X_FRAME_OPTIONS = 'DENY'`, `SECURE_BROWSER_XSS_FILTER = True`. |
| SEG-14 | `django-cors-headers` se configura con `CORS_ALLOWED_ORIGINS` listando únicamente el dominio del frontend en producción y `http://localhost:5173` en desarrollo. |
| SEG-15 | La protección CSRF de Django permanece activa para las vistas del Admin. Para la API REST con JWT, las rutas de la API usan `SessionAuthentication` deshabilitado, por lo que CSRF no aplica en esas rutas. |

### 6.5 Validación y sanitización

| ID | Especificación |
|----|----------------|
| SEG-16 | Todo input recibido desde el cliente se valida mediante DRF Serializers en el backend, independientemente de la validación en el frontend. |
| SEG-17 | Los campos de texto libre (comentarios, descripciones) se renderizan en el cliente escapando caracteres HTML para prevenir XSS. React escapa por defecto; se prohíbe el uso de `dangerouslySetInnerHTML`. |
| SEG-18 | Los archivos subidos al Módulo de Documentos se validan por extensión en el Serializer y por tipo MIME real con `python-magic`. El tamaño máximo por archivo es **10 MB** para el MVP (`FILE_UPLOAD_MAX_MEMORY_SIZE`). |
| SEG-19 | Los parámetros de paginación (`page`, `page_size`) se validan como enteros positivos con un máximo de `page_size = 50` para prevenir consultas abusivas. |

### 6.6 Datos sensibles y logs

| ID | Especificación |
|----|----------------|
| SEG-20 | Los mensajes de error del endpoint de login no deben indicar si el fallo fue por usuario inexistente o contraseña incorrecta. Respuesta uniforme: `{"detail": "Usuario o contraseña inválidos"}`. |
| SEG-21 | El sistema de logging de Django (`LOGGING`) no debe registrar contraseñas, tokens, ni payloads de formularios con datos personales. Se configura `django.security` en nivel `WARNING` y se excluyen los campos sensibles. |
| SEG-22 | Las variables de entorno con credenciales (`DATABASE_URL`, `SECRET_KEY`, claves SMTP, claves S3) se gestionan con `python-decouple` o `django-environ` y nunca se commitean al repositorio. El archivo `.env` debe estar en `.gitignore`. |
| SEG-23 | En producción, `DEBUG = False` es obligatorio. Con `DEBUG = True`, Django expone trazas completas de error que no deben llegar a usuarios finales. |
