# Requerimientos

## Historias de usuario

### HU-01 : Vista de login

**Como** usuario de la aplicación
**quiero** poder ingresar a la aplicación con mi usuario y contraseña
**para** acceder a las funcionalidades de la aplicación web

#### Escenario 1 : Login exitoso
``` gherkin
Dado que el usuario ingresó su usuario y contraseña
Cuando haga clic en "Ingresar"
Y las credenciales sean correctas
Entonces acceda al menú principal
```

#### Escenario 2 : Login incorrecto
``` gherkin
Dado que el usuario ingresó su usuario y contraseña
Cuando haga clic en "Ingresar"
Y las credenciales sean incorrectas
Entonces aparezca un error indicando que las credenciales son inválidas
```

#### Escenario 3 : Registro de nuevo usuario
``` gherkin
Dado que el usuario se encuentra en la pantalla de login
Y no tiene un usuario registrado
Cuando haga clic en "Registrarme"
Entonces lo lleve a la pantalal de registro
```

### Criterios de aceptación

- Deben existir los campos "Usuario" y "Contraseña".
- El campo de "Usuario" debe solicitar el nombre de usuario con el cual se registró el usuario previamente.
- Debe existir los siguientes botones:
    - Ingresar: Valida las credenciales para dar acceso en caso de ser correctas.
    - Olvidé mi contraseña: Envía al usuario a la pantalla de "Olvidé mi contraseña" (HU-03).
- El system design debe tener como base un color verde naturaleza.
- Cuando el usuario haga clic en "Ingresar" el sistema debe validar sus credenciales y redirigirlo al Menú principal en caso de ser correctas.
- Cuando el usuario haga clic en "Registrarme" el sistema debe redirigirlo a la pantalla de Registro de Usuario (HU-02)

### HU-02 : Pantalla de registro de usuario

**Como** persona sin usuario registrado
**quiero** poder crear un usuario en la aplicación web
**para** tener acceso a sus funcionalidades

#### Escenario 1 : Contraseña insegura
``` gherkin
Dado que el usuario llenó el formulario de datos solicitados
Cuando ingrese la contraseña a usar
Y la contraseña no cumpla con los requerimientos de seguridad
Entonces el sistema colorea el borde de la caja de texto en rojo
Y le muestra un mensaje diciendo "La contraseña es insegura"
```

#### Escenario 2 : Correo electrónico en uso
``` gherkin
Dado que el usuario llenó el formulario de datos solicitados
Cuando ingrese el correo electrónico a usar
Y el correo electrónico ya esté en uso
Entonces el sistema colorea el borde de la caja de texto en rojo
Y le muestra un mensaje diciendo "Este correo ya está en uso"
```

#### Escenario 3 : Nombre de usuario en uso
``` gherkin
Dado que el usuario llenó el formulario de datos solicitados
Cuando ingrese el nombre de usuario
Y el nombre de usuario ya está en uso
Entonces el sistema colorea el borde de la caja de texto en rojo
Y le muestra un mensaje diciendo "Este nombre de usuario ya está en uso"
```

#### Escenario 4 : Registro exitoso
``` gherkin
Dado que el usuario llenó el formulario de datos solicitados
Cuando haga clic en "Registrarse"
Y la validación de datos sea correcta
Entonces aparezca una pantalla indicando que su registro fue exitoso
```

### Criterios de aceptación

- La pantalla debe ser un formulario que solicite:
    - Correo electrónico
    - Nombre de Usuario
    - Nombre
    - Apellido
    - Nombre del grupo
    - Contraseña
    - Repetir contraseña
- Deben existir los siguientes botones:
    - Registrarse
    - Cancelar
- Al hacer clic en el botón "Registrarse" entonces el sistema valida que los datos esten ingresados correctamente. Esto último quiere decir:
    - Que el correo electrónico ingresado cumpla con la estructura de correo electrónico. Por ejemplo: "nombre@dominio.com"
    - Que la contraseña cumpla con los siguientes criterios:
        - Debe tener letras y números
        - Debe tener al menos un caracter especial
        - No debe contener el nombre del usuario
        - No debe contener ni el nombre ni el apellido
- Se le debe informar al usuario los criterios que debe cumplir la constraseña.
- El nombre de usuario será el identificador con el que accederá a la aplicación web.
El botón "Cancelar" debe redirigir al usuario a la pantalla de Login (HU-01).

### HU-03 : Pantalla de Recuperar Contraseña

**Como** usuario que olvidó la contraseña
**quiero** poder cambiar mi contraseña
**para** poder acceder a la aplicación web

#### Escenario 1 : Solicitar recuperación de contraseña
``` gherkin
Dado que hice clic en el botón "Recuperar contraseña" en la vista de Login
Y el sistema me redireccione a la vista de Recuperar contraseña
Cuando ingrese mi correo electrónico
Y haga clic en "Enviar correo de recuperación"
Entonces se envié un correo de recuperación de contraseña
Y me informe que se envió un correo con el link de recuperación
```

#### Escenario 2 : Abrir link de recuperación de contraseña
``` gherkin
Dado que se envió un correo con el link de recuperación
Y recibí el correo con el link de recuperación
Cuando haga clic en el botón "Cambiar mi contraseña" en el cuerpo del correo
Entonces se abra una página solicitando la nueva contraseña
```

#### Escenario 3 : Cambiar contraseña desde el link de recuperación
``` gherkin
Dado que se abrió una página solicitando la nueva contraseña
Y se ingresó la contraseña
Cuando haga clic en el botón "Cambiar contraseña"
Entonces se cambie la contraseña del usuario
Y se informe al usuario que el cambio de contraseña de efectuó exitosamente
Y muestre un botón que diga "Ir al Inicio"
```

### Criterios de aceptación
- La vista de recuperar contraseña solo debe solicitar el correo electrónico del usuario.
- Deben existir dos botones:
    - Enviar correo de recuperación
    - Cancelar
- Si el correo electrónico ingresado cumple con la estructura de correo electrónico. Por ejemplo: "nombre@dominio.com", entonces se habilita el botón "Recuperar contraseña"
- Al hacer clic en el botón "Recuperar contraseña" entonces el sistema debe enviar un correo electrónico al usuario donde en el cuerpo del correo se encuentre el botón "Cambiar mi constraseña" el cual abre una página con el link de recuperación.
- El link de recuperación debe ser temporal y debe expirar en 10 minutos.
- Al abrir el link de recuperación se debe mostrar una pantalla solicitando la nueva contraseña y repetir la nueva contraseña.
- La contraseña debe cumplir con los siguientes criterios:
    - Debe tener letras y números
    - Debe tener al menos un caracter especial
    - No debe contener el nombre del usuario
    - No debe contener ni el nombre ni el apellido
- Se le debe informar al usuario los criterios que debe cumplir la constraseña
- Si al hacer clic en "Cambiar mi contraseña" después de haber ingresado la nueva contraseña y esta no cumple con los criterios en el link de recuperación entonces no debe permitir cambiar la contraseña y debe indicar al usuario que la contraseña no cumple los criterios.
- Si al hacer clic en "Cambiar la contrasela" después de haber ingresaado la nueva contraseña y esta cumple con los criterios en el link de recuperación entonces el sistema debe cambiar la contraseña e informar al usuario que esta se cambió exitosamente.
- Al desplegar la información del cambio exitoso de la contraseña se debe desplegar el botón "Ir al Inicio" el cual debe llevar al usuario a la pantalla de Login. 


### HU-04 : Menú principal

**Como** usuario de la aplicación
**quiero** ver el menú principal
**para** utilizar las distintas funcionalidades de la aplicación web

### Escenarios de negocio

#### Escenario 1 : Visualizar el menú principal
``` gherkin
Dado que ingresé con mi usuario a la aplicación web
Cuando se despliegue el menú principal
Entonces vea los módulos disponibles
```

#### Escenario 2 : Acceder al módulo Finanzas
``` gherkin
Dado que me encuentro en el menú principal
Cuando haga clic en el módulo "Finanzas"
Entonces me dirija al módulo de finanzas (HU-XX)
```

#### Escenario 3 : Acceder al módulo Documentos
``` gherkin
Dado que me encuentro en el menú principal
Cuando haga clic en el módulo "Documentos"
Entonces me dirija al módulo de documentos (HU-XX)
```

#### Escenario 4 : Acceder a mis ajustes
``` gherkin
Dado que me encuentro en el menú principal
Cuando haga clic en el módulo "Documentos"
Entonces me dirija al módulo de documentos (HU-XX)
```

#### Escenario 5 : Cerrar sesión
``` gherkin
Dado que me encuentro en el menú principal
Cuando haga clic en el botón "Cerrar Sesión"
Entonces cierre mi sesión
Y me dirija a la vista de login
```

### Criterios de aceptación

- El menú principal debe tener los siguientes textos en la pantalla
    - "Hola [Nombre] [Apellido], ¿Que hay de nuevo hoy?" como titulo
    - [Nombre del grupo] en cursiva y centrado debajo del titulo
- El menú principal debe los botones para acceder a los módulos:
    - Finanzas
    - Anuncios
    - Documentos
- Los botones deben estar dispuestos en uan sola columna donde cada fila es un botón
- El system design debe tener como base un color verde naturaleza
- Los botones de acceso a cada uno de los módulos debe ser un botón que contenga el nombre del módulo.
- Los botones de acceso deben ser de color azul.
- El botón de "Mis ajustes" debe estar ubicado en la parte superior derecha de la pantalla a la derecha del botón "Mis notificaciones" (HU-05).
- Al presionar el botón "Mis ajustes" me debe llevar a la pantalla de Ajustes.
- El botón de "Cerrar sesión" debe estar ubicado en la parte superior derecha de la pantalla a la derecha del botón "Mis ajustes".

### HU-05 : Sección de notificaciones

**Como** usuario de la aplicación
**Quiero** ver las notificaciones de la aplicación
**Para** estar informado de los anuncios y movimientos

#### Escenario 1 : Visualizar las notificaciones
``` gherkin
Dado que ingresé con mi usuario a la aplicación web
Cuando se despliegue el menú principal
Y haga clic en el icono de campana de notificaciones
Entonces vea las notificaciones no leídas y un botón de "Ver todas las notificaciones"
```

#### Escenario 2 : Seleccionar una notificación por gasto
``` gherkin
Dado que el usuario hizo clic en el botón de notificaciones
Cuando se despliegue el listado de notificaciones no leídas
Y haga clic en una notificación por nuevo gasto
Entonces Se redirige al usuario a la pantalla del detalle del gasto
```

#### Escenario 3 : Seleccionar una notificación por cambio de presupuesto
``` gherkin
Dado que el usuario hizo clic en el botón de notificaciones
Cuando se despliegue el listado de notificaciones no leídas
Y haga clic en una notificación cambio de presupuesto
Entonces redirija al usuario a la pantalla de presupuesto
```

#### Escenario 4 : Seleccionar una notificación por nuevo anuncio
``` gherkin
Dado que el usuario hizo clic en el botón de notificaciones
Cuando se despliegue el listado de notificaciones no leídas
Y haga clic en una notificación por nuevo anuncio
Entonces redirija al usuario a la pantalla de presupuesto
```

#### Escenario 5 : Seleccionar una notificación por invitación a un grupo
``` gherkin
Dado que el usuario hizo clic en el botón de notificaciones
Cuando se despliegue el listado de notificaciones no leídas
Y haga clic en una notificación por invitación a un grupo
Entonces redirija al usuario a la pantalla de gestión de la invitación
```

### Criterios de aceptación

- EL botón debe estar ubicado en la parte superior derecha de la pantalla a la izquierda del botón "Mis ajustes"
- Al hacer clic en el botón "Mis notificaciones" se debe mostrar una lista con las notificaciones no leídas y una fila clickeable al final que diga "Ver todas mis notificaciones".
- Cada fila notificación no leída debe tener el titulo descriptivo de la notificación y la fecha y hora de cuando se genero
- Las notificaciones se generan cuando
    - Un usuario del grupo genera un gasto
    - Se modifica el presupuesto
    - Se realiza un anuncio en el módilo de Anuncios
    - Se recibe una invitación a un grupo
- El titulo y comportamiento de las notificaciones dependiendo de la naturaleza son las siguientes:
    - Notificación por nuevo de gasto: 
        - Titulo: "Se genero un gasto por [Monto en CLP] de [usuario] por [concepto]"
        - Comportamiento: Se redirige al usuario a la pantalla del detalle del gasto.
    - Notificación por cambio en el presupuesto:
        - Titulo: "Se realizó un cambio en el presupuesto de [concepto]"
        - Comportamiento: Se redirige al usuario a la pantalla de presupuesto.
    - Notificación por nuevo anuncio:
        - Titulo: "Se realizó el siguiente anuncio: [Titulo del anuncio]"
        - Comportamiento: Se redirige al usuario al detalle del anuncio.
    - Notificación por invitación a un grupo:
        - Titulo: "El usuario [Nombre de Usuario que envió la invitación] te ha invitado al grupo [Nombre del grupo]"
        - Comportamiento: Se redirige al usuario a la pantalla de gestión de invitación.
- El botón de "Mis notificaciones" debe ser de color azul y solo tener un ícono de campana.
- Al hacer clic en el botón "Ver todas mis notificaciones" se debe ir a la vista de "Notificaciones" para visualizar todas las notificaciones históricas paginadas por 10 notificaciones.
- En botón de paginación debe estra en la parte inferior de la pantalla.

### HU-06 : Pantalla de gestión de invitación

**Como** usuario de la aplicación
**Quiero** visualizar una invitación a un grupo recibida
**Para** aceptar o rechazar la invitación

#### Escenario 1 : Aceptar una invitación
``` gherkin
Dado que el usuario recibió una notificación de invitación a un grupo
Y haga clic en la notificación
Cuando se despliegue la pantalla de gestión de invitación
Y haga clic en "Aceptar"
Entonces el sistema me agregue al grupo de la invitación
Y se muestre en la pantalla que fue agregado al grupo [Nombre del grupo]
```

#### Escenario 2 : Rechazar una invitación
``` gherkin
Dado que el usuario recibió una notificación de invitación a un grupo
Y haga clic en la notificación
Cuando se despliegue la pantalla de gestión de invitación
Y haga clic en "Rechazar"
Entonces se muestre en la pantalla que la invitación fue rechazada
```

### Criterios de aceptación
- La pantalla de gestión de invitación debe mostrar el detalle de solo una invitación
- La invitación en la pantalla de gestión de invitación debe mostrar el nombre del grupo, el comentario de la invitación, el botón "Aceptar" y el botón "Rechazar"
- El botón "Aceptar" debe ser de color verde.
- Al hacer clic en el botón "Aceptar" se debe agregar al usuario al grupo de la invitación.
- El botón "Rechazar" debe ser de color rojo.
- Al hacer clic en el botón "Rechazar" no se debe agregar al usuario al grupo de la invitación y esta invitación queda rechazada.
- Si se rechaza dos veces una invitación en un intervalo de menos de una hora entonces el emisor de la invitación no puede volver a enviar una invitación nueva hasta después de 24 horas.


### HU-07 : Mis ajustes

**Como** usuario de la aplicación
**Quiero** configurar los datos de mi cuenta
**Para** visualizar la información de mi cuenta y mi grupo

#### Escenario 1 : Acceder a Vista de Grupo
``` gherkin
Dado que el usuario se encuentra en Mis Ajustes
Cuando haga clic en el botón "Gestionar Grupo"
Entonces el sistema redirija al usuario a la Vista de Gestión de Grupo
```

### Criterios de aceptación
- La vista de "Mis ajustes" debe mostrar la siguiente información:
    - Nombre de usuario
    - Nombre
    - Apellido
    - Nombre de grupo
- Si el usuario no pertenece a ningún grupo, en la información del Nombre de Grupo debe decir "Sin grupo".
- Debe contener un botón "Gestionar Grupo".
- El botón "Gestionar Grupo" debe ser de color azul.
- Al hacer clic en el botón "Gestionar Grupo" se debe redirigir a la Vista de Gestión de Grupo.

### HU-08 : Vista de Gestión de Grupo

**Como** usuario de la aplicación
**Quiero** Ver la información de mi grupo
**Para** gestionar la información de mi grupo

#### Escenario 1 : Crear un grupo como administrador
``` gherkin
Dado que el usuario se encuentra en la Vista de Gestión de Grupo
Y no tiene un grupo creado
Cuando haga clic en "Crear grupo"
Y llene el formulario de la información del grupo
Y haga clic en "Aceptar"
Entonces el sistema crea el grupo
Y el sistema da privilegios de administrador del grupo al usuario creador del grupo 
```

#### Escenario 2 : Agregar miembro como administrador
``` gherkin
Dado que el usuario es administrador de un grupo
Y accede a la Vista de GEstión de Grupo
Cuando haga clic en "Agregar miembro"
Y el usuario ingresa el nombre del usuario a invitar
Y el usuario ingresa la descripción de la invitación
Y haga clic en "Aceptar"
Entonces el sistema envía una invitación al usuario invitado
Y el sistema informa que la invitación fue enviada exitosamente
```

#### Escenario 3 : Quitar miembro como administrador
``` gherkin
Dado que el usuario es administrador de un grupo
Y accede a la Vista de Gestión de Grupo
Cuando vea la lista de miembros del grupo
Y haga clic en "Quitar" en la fila de uno de los miembros
Y se abra un modal pidiendo confirmación
Y haga clic en "Aceptar"
Entonces el sistema quita al usuario del grupo
Y el sistema informa que el usuario fue expulsado del grupo
```

#### Escenario 3 : Dar privilegios de administrador a un usuario miembro del grupo
``` gherkin
Dado que el usuario es administrador de un grupo
Y accede a la Vista de Gestión de Grupo
Cuando vea la lista de miembros del grupo
Y haga clic en "Hacer Admin" en la fila de uno de los miembros
Y se abra un modal pidiendo confirmación
Y haga clic en "Aceptar"
Entonces el sistema da privilegios de administrador al usuario elegido
Y el sistema informa que el usuario ahora es administrador
```
#### Escenario 3 : Quitar privilegios de administrador a un usuario administrador miembro del grupo
``` gherkin
Dado que el usuario es administrador de un grupo
Y accede a la Vista de Gestión de Grupo
Cuando vea la lista de miembros del grupo
Y haga clic en "Quitar Admin" en la fila de uno de los miembros
Y se abra un modal pidiendo confirmación
Y haga clic en "Aceptar"
Entonces el sistema da privilegios de administrador al usuario elegido
Y el sistema informa que el usuario ahora es administrador
```

#### Escenario 5 : Salir de un grupo como usuario no administrador
``` gherkin
Dado que el usuario no es administrador de un grupo
Y accede a la Vista de Gestión de Grupo
Cuando haga clic en el botón "Abandonar grupo"
Y se abra un modal pidiendo confirmación
Y haga clic en "Aceptar"
Entonces el sistema quita a usuario de ese grupo
Y el sistema informa que el usuario abandonó exitosamente el grupo
```

#### Escenario 6 : Eliminar grupo como administrador
``` gherkin
Dado que el usuario es administrador de un grupo
Y accede a la Vista de Gestión de Grupo
Cuando haga clic en el botón "Eliminar grupo"
Y se abra un modal pidiendo confirmación
Y haga clic en "Aceptar"
Entonces el sistema elimina ese grupo
Y el sistema deja a todos los usuario sin pertenencia a un grupo
```

#### Criterios de aceptación
- Si el usuario no pertenece a ningún grupo entonces en la Vista de Gestión de grupo aparecerá un mensaje que dice "Aún no perteneces a ningún grupo" y debajo aparezca un botón de "Crear un nuevo grupo".
- Si el usuario pertenece a un grupo entonces en la Vista de Gestión de grupo aparecerá la siguiente información:
    - Nombre del grupo
    - Descripción del grupo
    - Listado de miembros del grupo
- Si el usuario no es administrador entonces solo podrá visualizar la información sin opciones de modificar.
- Si el usuario no es administrador entonces al final de la Vista aparecerá un botón llamado "Abandonar grupo".
- Al hacer clic en el botón "Abandonar grupo" debe aparecer uan confirmación con los botones "Aceptar" y "Cancelar"
    - Botón Aceptar: El usuario abandona el grupo y queda sin grupo.
    - Botón Cancelar: Se devuelve a la Vista de Gestión de Grupo.
- Si el usuario es administrador entonces al final de las filas de cada uno de los miembros del grupo se ubiquen los botones:
    - Quitar: Aparece una confirmación con los botones "Aceptar" y "Cancelar"
        - Aceptar: Expulsa al usuario seleccionado del grupo.
        - Cancelar: Se devuelve a la Vista de Gestión de Grupo.
    - Hacer Admin/Quitar Admin: Este botón dependerá de si el usuario de dicha fila es Admin o no.
        - Si no es Admin entonces el botón será "Hacer Admin".
        - Si es Admin entonces el botón será "Quitar Admin"
- Si el usuario no es administrador entonces al final de la Vista aparecerá un botón llamado "Eliminar grupo".
- Al hacer clic en el botón "Eliminar grupo" debe aparecer una confirmación con los botones "Aceptar" y "Cancelar".
    - Botón Aceptar: El usuario elimina el grupo y todos los miembros quedan sin grupo.
    - Botón Cancelar: Se devuelve a la Vista de Gestión de Grupo.


### HU-09 : Módulo de Finanzas

**Como** usuario de la aplicación
**Quiero** Ver la información de mis finanzas
**Para** gestionar mi comportamiento financiero

#### Escenario 1 : Visualizar resumen financiero
``` gherkin
Dado que el usuario accedió al Módulo de Finanzas
Cuando visualice la pantalla principal del Módulo
Entonces se deben mostrar los indicadores financieros
Y se debe mostrar un gráfico de torta de los gastos por concepto
```

#### Escenario 2 : Crear concepto
``` gherkin
Dado que el usuario accedió al Módulo de Finanzas
Y el usuario hizo clic en "Conceptos"
Y haga clic en "Agregar concepto"
Cuando ingrese la información del concepto
Y haga clic en "Agregar"
Entonces se agrega un concepto al modelo financiero
```


#### Escenario 3 : Gestionar presupuesto
``` gherkin
Dado que el usuario accedió al Módulo de Finanzas
Cuando el usuario hizo clic en "Presupuesto"
Y haga clic en "Gestionar presupuesto"
Entonces ingresa a la Vista de Presupuesto
```

#### Escenario 4 : Añadir ingreso
``` gherkin
Dado que el usuario accedió al Módulo de Finanzas
Y el usuario hizo clic en "Añadir ingreso"
Cuando se despliegue el formulario de detalle del ingreso
Y se ingrese el monto
Y se ingrese el concepto
Entonces se agrega el ingreso a la información financiera
```

#### Escenario 5 : Añadir gasto
``` gherkin
Dado que el usuario accedió al Módulo de Finanzas
Y el usuario hizo clic en "Añadir gasto"
Cuando se despliegue el formulario de detalle del gasto
Y se ingrese el monto
Y se ingrese el concepto
Entonces se agrega el ingreso a la información financiera
```

#### Escenario 5 : Ver movimientos
``` gherkin
Dado que el usuario accedió al Módulo de Finanzas
Cuando el usuario hizo clic en "Ver movimientos"
Entonces se ingresa a la Vista de Movimientos
```

### Criterios de Aceptación
- El Módulo de Finanzas es una vista compartida para todos los usuarios de un mismo grupo.
- Al ingresar al Módulo de finanzas se deben mostrar los siguientes indicadores financieros:
    - Gasto acumulado mensual : Suma de los montos de todos los gastos del mes
    - Saldo restante: Resta entre el Ingreso y los gastos
    - Desviación del presupuesto: Suma de los montos del presupuesto hasta la fecha menos los gastos hasta la fecha
- Al ingresar al Módulo de finanzas se debe mostrar un gráfico de torta con de los gastos por su concepto correspondiente.
    - Si hay más de 5 conceptos en el gráfico de torta entonces se muestran los 5 conceptos más altos y se crea un 6to concepto abstracto como "Otros" que contiene los otros conceptos de menor monto.
- El Módulo de finanzas debe contener los siguientes elementos con su disposición correspondiente:
    - Botón "Gestionar Presupuesto": Debe estar en la esquina superior izquierda de la pantalla. Debe ser de color azul.
    - Botón "Conceptos": Debe estar en la esquina superior izquierda de la pantalla a la derecha del botón "Gestionar Presupuesto". Debe ser de color azul.
    - Botón "Exportar": Debe estar en la esquina superior izquierda de la pantalla a la derecha del botón "Conceptos". Debe ser de color verde.
    - Indicadores financieros: Deben estar en la parte superior de la pantalla.
    - Gráfico de gastos: Debe estar debajo de los indicadores financieros.
    - ültimos movimientos: Debe mostrar los últimos 5 movimientos ya sean ingresos o gastos en una tabla con las siguientes columnas:
        - Concepto
        - Monto
        - Usuario
        - Fecha y hora
        - Botón "Ver detalle"
    - Barra inferior con las siguientes secciones:
        - Añadir Gasto
        - Ver movimientos
        - Añadir Ingreso
- El botón "Ver detalle" en la fila de un movimiento debe redirigir al detalle de un movimiento. Esta vista debe mostrar:
    - Nombre
    - Concepto
    - Detalle
    - Monto
    - Usuario
    - Fecha y hora
- El botón "Añadir gasto" debe abrir un formulario con los siguientes elementos:
    - Nombre - Obligatorio
    - Detalle - Opcional
    - Concepto - Obligatorio: Debe ser una lista desplegable de los conceptos de tipo "Gasto"
    - Monto - Obligatorio
    - Botón "Ingresar": Ingresa el gasto registrando la información ingresada más el nombre de usuario y la fecha y hora del ingreso de información.
- El botón "Añadir Ingreso" debe abrir un formulario con los siguientes elementos:
    - Nombre - Obigatorio
    - Detalle - Opcional
    - Concepto - Obligatorio: Debe ser una lista desplegable con los conceptos tipo "Ingreso"
    - Monto - Obligatorio
    - Botón "Ingresar": Ingresa el ingreso registrando la información ingresada más el nombre del usuario y la fecha y hora del ingreso de información.
- Al hacer clic en el botón "Gestionar presupuesto" se debe abrir la Vista de Presupuesto
- Al hacer clic en el botón "Conceptos" se debe abrir la Vista de Conceptos
- Al hacer clic en el botón "Exportar" se debe exportar un archivo .csv con la información de todos los movimientos históricos. Las columnas que debe tener el archivo exportado son las siguientes:
    - Tipo
    - Concepto
    - Nombre
    - Detalle
    - Monto
    - Usuario
    - Fecha y hora
- El archivo exportado debe estar con separador ";" y con el encoding utf-8 con BOM.
- Al ingresar un gasto se debe notificar a los miembros del grupo.
- Al ingresar un ingreso se debe notificar a los miembros del grupo.
- El tipo de un movimiento puede ser Gasto o Ingreso
- Todos los montos deben estar en CLP y con separador de miles con punto.

### HU-10 : Vista de Presupuesto

**Como** usuario de la aplicación
**Quiero** Ver el presupuesto asignado
**Para** gestionar mi presupuesto

#### Escenario 1 : Agregar un registro de presupuesto
``` gherkin
Dado que el usuario está en la Vista de Presupuesto
Cuando el usuario haga clic en "Agregar"
Y el usuario ingresa la información del presupuesto
Entonces se ingresa el registro de presupuesto al presupuesto
```

#### Escenario 2 : Quitar un registro de presupuesto
``` gherkin
Dado que el usuario está en la Vista de Presupuesto
Y visualiza el listado de registros de presupuesto
Cuando el usuario haga clic en "Quitar" al final de la fila de un registro de presupuesto
Y el usuario confirme la eliminación del registro de presupuesto
Entonces se elimina el registro de presupuesto
```

#### Escenario 3 : Modificar un registro de presupuesto
``` gherkin
Dado que el usuario está en la Vista de Presupuesto
Y visualiza el listado de registros de presupuesto
Cuando el usuario haga clic en "Modificar" al final de la fila de un registro de presupuesto
Y modifique la información del registro de presupuesto

Entonces se elimina el registro de presupuesto
```

### Criterios de Aceptación
- La Vista de presupuesto es una vista compartida para todos los usuarios de un mismo grupo.
- En la Vista de presupuesto debe aparecer un listado de los registros de presupuesto con su monto asociado.
- Los componentes y su disposición son los siguientes:
    - Botón de "Agregar" debe estar en la parte superior derecha de la Vista
    - Botón "Atrás" debe estar en la parte superior izquierda de la Vista
    - Se debe mostrar una tabla con las siguientes columnas:
        - Concepto: El concepto del registro de presupuesto
        - Monto: El monto del registro de presupuesto
    - Por cada fila deben existir dos botones al final de la fila:
        - Modificar: Modifica la información del registro de presupuesto
        - Eliminar: Elimina el registro de presupuesto
    - En al última fila debe existir un total con la sumatoria de los montos de la columna "Monto"
- Al hacer clic en el botón "Agregar" debe pedir la siguiente información:
    - Tipo - Obligatorio: Gasto o Ingreso
    - Concepto - Obligatorio: Lista dependiente del tipo. Si el Tipo es Gasto entonces muestra todos los conceptos de tipo Gasto. Mismo caso con los de Tipo Ingreso
    - Nombre - Obligatorio
    - Detalle - Opcional
    - Fecha - Obligatorio
    - Monto - Obligatorio
- Al hacer clic en "Modificar" solo se podrá cambiar el monto.
- Al hacer clic en el botón "Atrás" se debe dirigir al usuario al Módulo de Finanzas
- Todos los montos deben estar en CLP y con separador de miles con punto.
    
### HU-11 : Vista de Conceptos

**Como** usuario de la aplicación
**Quiero** Ver la información de los conceptos
**Para** clasificar los conceptos entre gastos e ingresos

#### Escenario 1 : Agregar un concepto
``` gherkin
Dado que el usuario está en la Vista de Conceptos
Cuando haga clic en "Agregar"
Y el usuario ingrese la información del concepto
Y haga clic en "Aceptar"
Entonces se agregue un nuevo concepto
```

#### Escenario 2 : Quitar un concepto
``` gherkin
Dado que el usuario está en la Vista de Conceptos
Cuando se ubique en la fila de un concepto
Y haga clic en "Quitar"
Y confirme la eliminación del concepto
Entonces se elimine el concepto
```

#### Escenario 3 : Modificar un concepto
``` gherkin
Dado que el usuario está en la Vista de Conceptos
Cuando se ubique en la fila de un concepto
Y haga clic en "Editar"
Y el usuario ingrese la información nueva del concepto
Entonces se modifique el concepto
```

#### Criterios de aceptación
- En la Vista de conceptos los componentes se deben disponer de la siguiente manera:
    - En la parte superior derecha de la pantalla debe aparecer el botón "Agregar"
    - En la parte superior izquierda de la pantalla debe aparecer el botón "Atrás"
    - Dentro de la Vista debe haber una tabla con la siguiente información:
        - Nombre: Nombre del Concepto
        - Tipo: Gasto o Ingreso
        - Botón "Editar"
        - "Botón "Eliminar
- Al hacer clic en el botón "Agregar" se debe mostrar un formulario que solicite:
    - Nombre del concepto - Obligatorio
    - Tipo - Obligatorio
- Al hacer clic en el botón "Editar" en la fila de un concepto entonces se debe mostrar un formulario donde solo se pueda editar el nombre del concepto
- Al hacer clic en el botón "Quitar" en la fila de un concepto entonces se debe validar si existan gastos o ingresos efectuados (No en el presupuesto) hasta ese momento.
    - Si existen gastos o ingresos incurridos con dicho concepto entonces se debe informar al usuario que puede eliminar los movimientos asociados o dejar sin concepto asociado a dichos movimientos. Ahí entonces el sistema debe mostrar los botones:
        - Eliminar movimientos asociados: Elimina el concepto y todos los gastos e ingresos asociados.
        - Mantener movimientos: Elimina el concepto y los movimientos de gastos o ingresos asociados a dicho concepto quedarán con un concepto llamado "Desconocido".
- Un concepto puede ser de tipo Gasto o Ingreso.
- Al hacer clic en el botón "Atrás" se debe dirigir al usuario al Módulo de Finanzas

### HU-12 : Vista de Movimientos

**Como** usuario de la aplicación
**Quiero** Ver el detalle de los movimientos registrados
**Para** tener un histórico de los movimientos efectuados


#### Escenario 1 : Ver el detalle de un movimiento
``` gherkin
Dado que el usuario está en la Vista de Movimientos
Cuando se ubique en la fila de un movimiento
Y haga clic en "Ver detalle"
Entonces se despliegue la información del detalle del movimiento
```

#### Criterios de aceptación:
- La vista de movimientos es una vista compartida para todos los usuarios de un mismo grupo.
- En al Vista de movimientos debe existir un listado de todos los movimientos efectuados. Se debe mostrar:
    - Tipo (Gasto o Ingreso)
    - Concepto
    - Nombre
    - Monto
    - Usuario
    - Fecha y Hora
    - Botón "Ver detalle"
- Los movimientos están paginados en un máximo de 15 movimientos ordenados de manera descendente en función de la fecha y hora.
- Al hacer clic en el botón "Ver detalle" se debe mostrar toda la información del movimiento
- Debe existir un filtro que permita filtrar por concepto.


### HU-13 : Módulo de Documentos

**Como** usuario de la aplicación
**Quiero** subir documentos en la aplicación
**Para** disponer al grupo los documentos subidos

#### Escenario 1 : Subir un archivo
``` gherkin
Dado que el usuario está en el Módulo de Documentos
Cuando haga clic en "Subir archivo"
Y seleccione el archivo a subir
Entonces se suba el archivo a la aplicación web
Y se envíe una notificación a los usuarios del grupo
```

#### Escenario 2 : Eliminar un archivo
``` gherkin
Dado que el usuario está en el Módulo de Documentos
Y el usuario subió un archivo en el pasado
Cuando se posicione en el detalle de un archivo que subió
Y haga clic en "Eliminar"
Y confirme la eliminación
Entonces el archivo será eliminado de la aplicación web
```

#### Criterios de aceptación
- El módulo de documentos es una vista compartida para todos los usuarios de un mismo grupo.
- Se debe mostrar un listado de todos los archivos subidos con el siguiente detalle:
    - Nombre del archivo
    - Descripción
    - Fecha de subida
    - Usuario
- El botón "Agregar" debe desplegar un formulario con la siguiente información
    - Nombre
    - Adjuntar Archivo
    - Descripción
- Solo se pueden subir archivos en formato .pdf, .csv, .xlsx o .png
- Un documento solo puede ser eliminado por el usuario que lo creó.

### HU-14 : Módulo de Anuncios

**Como** usuario de la aplicación
**Quiero** subir anuncios
**Para** compartir información con el resto de los miembros de un grupo

#### Escenario 1 : Crear un anuncio
``` gherkin
Dado que el usuario está en el Módulo de Anuncios
Y el usuario haga clic en "Crear anuncio"
Cuando llene los datos del formulario desplegado
Y haga clic en "Publicar"
Entonces se publique el Anuncio dentro del módulo
Y se notifique a los miembros del grupo que el usuario subió un archivo
```

#### Escenario 2 : Eliminar un anuncio
``` gherkin
Dado que el usuario está en el Módulo de Anuncios
Y el usuario creó un anuncio en el pasado
Cuando se posicione en un anuncio que publicó
Y haga clic en "Eliminar"
Entonces se elimine el anuncio
```

#### Escenario 3 : Comentar un anuncio
``` gherkin
Dado que el usuario está en el Módulo de Anuncios
Y el usuario hace clic en el botón "Ver"
Cuando ingrese un comentario en la caja de texto de comentarios
Y haga clic en "Comentar"
Entonces se agregue el comentario al anuncio
```

#### Criterios de aceptación
- El módulo de anuncios es una vista compartida para todos los usuarios de un mismo grupo.
- Se debe mostrar todos los anuncios creados con el siguiente detalle:
    - Nombre
    - Descripción
    - Fecha de creación
    - Usuario
- Al hacer clic en el botón "Crear anuncio" se debe mostrar un formulario que debe pedir:
    - Nombre
    - Descripción
- Por cada anuncio debe existir un botón "Ver".
- Si el anuncio fue creado por el usuario que esta visualizandolo, entonces también debe aparecer el botón "Eliminar" en el anuncio.
- Al hacer clic en el botón "Ver" se debe acceder al detalle del anuncio.
- En el detalle del anuncio debe existir una sección de comentarios con una caja de texto dispuesta para ingresar un comentario.
- En la sección de comentarios debe estar el botón "Comentar" el cual sube el comentario al anuncio.
- Los comentarios solo son visibles cuando se muestra el detalle de un anuncio.
- Un anuncio solo puede ser eliminado por el usuario que lo creó.


####