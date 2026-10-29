# La Pizarra Peluda

> Gestor de convocatorias, disponibilidad y estadísticas para un club deportivo amateur. Sustituye el "¿quién puede el jueves?" de WhatsApp por un enlace donde cada jugador marca cuándo **no puede**, y el club ve al instante qué franja horaria tiene menos bajas.

![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Status](https://img.shields.io/badge/status-en%20desarrollo-orange)

---

## Índice

- [¿Qué es esto?](#qué-es-esto)
- [Cómo funciona: disponibilidad inversa](#cómo-funciona-disponibilidad-inversa)
- [Funcionalidades](#funcionalidades)
- [Stack técnico](#stack-técnico)
- [Arquitectura](#arquitectura)
- [Modelo de datos](#modelo-de-datos-resumen)
- [Rutas principales](#rutas-principales)
- [Licencia](#licencia)

---

## ¿Qué es esto?

Un club de fútbol 7 amateur coordina sus partidos y entrenamientos por WhatsApp, a ciegas: alguien pregunta "¿quién puede el jueves a las 20h?" y espera respuestas sueltas sin ninguna visión de conjunto. **La Pizarra Peluda** sustituye eso por una herramienta ligera, pensada para usarse sobre todo desde el móvil, sin fricción de registro para la mayoría del equipo.

Además de la convocatoria, la aplicación lleva las **estadísticas de la plantilla** (goles, asistencias, tarjetas…) y las publica en una página abierta con rankings.

## Cómo funciona: disponibilidad inversa

En vez de preguntar "¿cuándo puedes?", la aplicación pregunta **"¿cuándo NO puedes?"**. Cada jugador marca sus franjas imposibles sobre un calendario semanal; la aplicación calcula automáticamente qué franja tiene menos bajas, y el staff del club confirma el horario final con un toque.

## Funcionalidades

### Club y cuentas
- **Alta del club** (`/create_club`): la primera persona que entra crea el club y su cuenta de administrador en un único paso.
- **Cuentas solo para el staff**: los jugadores nunca inician sesión. El admin genera un enlace de activación por cada miembro del staff (válido 14 días), que fija su contraseña sin poder cambiar su nombre. Generar uno nuevo invalida el anterior.
- **Dos niveles de permisos**: cualquier miembro activo del staff puede consultar el panel; solo el **administrador** puede crear y borrar eventos, gestionar la plantilla, editar estadísticas, cambiar el nombre del club o borrarlo.

### Eventos y disponibilidad
- **Tipos de evento**: partido, partido amistoso, entrenamiento, reunión u otro, con rival opcional.
- **Generador de franjas horarias** (`/staff/events/new`): en vez de crear franjas una a una, el admin indica una horquilla de fechas, qué días de la semana, una ventana horaria diaria y la duración de cada franja (30 min, 1 h, 1 h 30 min o 2 h). El sistema genera todas las combinaciones y muestra cuántas franjas saldrán antes de guardar.
- **Enlace público por evento** (`/e/{token}`), sin necesidad de iniciar sesión: el jugador elige su nombre en la lista del club y marca sus franjas imposibles sobre una rejilla paginada por semanas. Puede volver a entrar y modificar sus marcas.
- **Mapa de bajas** para el staff: rejilla semanal coloreada de verde (pocas bajas) a rojo (muchas). Al tocar una franja se ve quién tiene baja en ella.
- **Mejores franjas**: ranking de las 10 franjas con menos bajas, con el número de jugadores disponibles sobre el total de la plantilla.
- **Confirmación del horario** en un toque desde la franja elegida. Una vez confirmado, el enlace público muestra el horario definitivo en lugar de la rejilla.
- **Botón "Añadir a mi calendario"** en el enlace público de un evento confirmado (plantilla de Google Calendar, sin conectar ninguna cuenta).
- **Copiar enlace** del evento al portapapeles desde el detalle del evento.

### Plantilla
- **Gestión de la plantilla** en la pestaña *Plantilla*: nombre, dorsal y roles (jugador, capitán, staff). Los roles son informativos y no controlan permisos; el capitán se marca con una **C** junto al dorsal.

### Estadísticas
- **Estadísticas por jugador**: partidos jugados, titularidades, goles, asistencias, tarjetas amarillas, tarjetas rojas y "Jugador Estrella Damm" (MVP del partido).
- **Página pública** (`/stats`, o `/{club}/stats`), sin sesión: rankings Top 3 de goleadores, asistentes, G + A, Estrellas Damm, amarillas y rojas (con "Ver más" para el ranking completo) y la lista de la plantilla con sus números clave. Al tocar un jugador se abre el detalle de todas sus estadísticas.
- **Edición** solo para el admin: desde la pestaña *Plantilla*, al tocar a un jugador se abre un diálogo editable con todos los contadores.

### Otros
- **Panel de staff** (`/staff`) con tres pestañas: Club · Plantilla · Eventos.
- **Health check** en `/ping`, que responde `pong` en texto plano.
- Diseño pensado para móvil y con la paleta e identidad del club.

## Stack técnico

| Capa                    | Tecnología                                                                               |
| ----------------------- | ---------------------------------------------------------------------------------------- |
| Interfaz                | [NiceGUI](https://nicegui.io) 3.x (Python sobre Vue/Quasar)                              |
| Lenguaje                | Python 3.11+                                                                             |
| ORM                     | SQLAlchemy 2.0 (declarative, sin SQLModel)                                               |
| Base de datos           | PostgreSQL ([Supabase](https://supabase.com)) en producción · SQLite en desarrollo local |
| Autenticación           | Contraseñas con hash (Werkzeug), sesión vía almacenamiento de NiceGUI                    |
| Despliegue              | [Render](https://render.com)                                                             |
| Gestión de dependencias | [Poetry](https://python-poetry.org)                                                      |
| Tests                   | pytest (dependencia de desarrollo)                                                       |

### Variables de entorno

| Variable         | Obligatoria | Descripción                                                                                                        |
| ---------------- | ----------- | ------------------------------------------------------------------------------------------------------------------ |
| `STORAGE_SECRET` | Sí          | Clave con la que NiceGUI firma el almacenamiento de sesión.                                                        |
| `DATABASE_URL`   | No          | URL de conexión a PostgreSQL. Si no se define, se usa SQLite en `data/gyp.db`. Acepta el prefijo `postgres://`.    |
| `PORT`           | No          | Puerto de escucha (por defecto `8080`).                                                                            |

> Las tablas se crean automáticamente al arrancar (`create_all`). No hay sistema de migraciones: añadir tablas nuevas funciona solo, pero cambiar columnas de tablas existentes requiere actualizar la base de datos a mano.

## Arquitectura

El proyecto sigue una arquitectura en tres capas estrictas: **las vistas nunca abren una sesión de base de datos directamente** — siempre pasan por `services/`.

```
lapizarrapeluda/
├── core/                      # configuración y conexión a la base de datos
│   ├── config.py                # variables de entorno
│   └── database.py              # engine, Base declarativa, get_session(), init_db()
├── models/                    # tablas SQLAlchemy
│   ├── club.py, user.py, event.py, availability.py, token.py
│   └── user.py                  # incluye User, UserRole y PlayerStats
├── services/                  # lógica de negocio — una función por caso de uso
│   ├── auth_service.py          # login
│   ├── club_service.py          # alta/edición/borrado del club
│   ├── user_service.py          # jugadores y staff
│   ├── role_service.py          # roles (jugador/capitán/staff)
│   ├── event_service.py         # eventos, generación y confirmación de franjas
│   ├── token_service.py         # enlaces de activación y de evento
│   ├── availability_service.py  # disponibilidad inversa
│   └── stats_service.py         # estadísticas y rankings de jugadores
├── views/
│   ├── pages/                 # rutas @ui.page
│   │   ├── activate.py, create_club.py, login.py
│   │   ├── staff.py             # panel de staff
│   │   ├── create_event.py      # generador de franjas
│   │   ├── event.py             # enlace público del evento
│   │   └── stats.py             # página pública de estadísticas
│   ├── components/
│   │   ├── staff_tabs/          # pestañas del panel: club, squad, events
│   │   └── stats_dialog.py      # diálogo de estadísticas de un jugador
│   ├── layout.py                # cabecera y guardas de sesión compartidas
│   └── theme.py                 # paleta de colores del club
├── static/                    # escudo, favicon y logos de patrocinadores
├── main.py                    # punto de entrada
└── pyproject.toml
```

Cada función de servicio sigue el mismo patrón: abre su propia sesión (`with get_session() as session:`), y comunica errores de negocio con `raise ValueError("error_codigo")` en vez de devolver `None` o booleanos — las vistas traducen esos códigos a mensajes legibles.

## Modelo de datos (resumen)

| Tabla            | Para qué sirve                                                                                           |
| ---------------- | -------------------------------------------------------------------------------------------------------- |
| `Club`           | Una fila por despliegue (de momento, un solo club por instalación)                                       |
| `User`           | Jugadores y staff, con dorsal opcional. La mayoría no tiene `password_hash` ni `is_active=True` — nunca inician sesión. `is_admin` marca al administrador |
| `UserRole`       | Etiquetas (jugador/capitán/staff) — puramente informativas, no controlan permisos                        |
| `PlayerStats`    | Una fila por jugador con sus contadores: partidos jugados, titularidades, goles, asistencias, amarillas, rojas y MVP |
| `Event` / `Slot` | Un evento (tipo, rival opcional, estado abierto/confirmado/pasado) y sus franjas horarias candidatas     |
| `Unavailability` | El corazón del sistema: una fila = "este jugador no puede en esta franja". Ausencia de fila = disponible |
| `Token`          | Enlaces de dos tipos: activación de cuenta de staff (con caducidad) o acceso público a un evento         |

## Rutas principales

| Ruta                          | Quién la usa                  | Qué hace                                                             |
| ----------------------------- | ----------------------------- | -------------------------------------------------------------------- |
| `/`                           | Todos                         | Redirige a `/login` o a `/staff` según haya sesión                   |
| `/create_club`                | Nadie (una sola vez)          | Arranca el club y su admin                                           |
| `/login`                      | Staff                         | Nombre + contraseña (también como `/{club}/login`)                   |
| `/activate/{token}`           | Staff invitado                | Fija su contraseña, nombre no editable                               |
| `/staff`                      | Staff                         | Panel con Club · Plantilla · Eventos                                 |
| `/staff/events/new`           | Staff (admin)                 | Crear evento con franjas generadas                                   |
| `/e/{token}`                  | Cualquier jugador, sin sesión | Elegir nombre y marcar indisponibilidad, o ver el horario confirmado |
| `/stats`, `/{club}/stats`     | Cualquiera, sin sesión        | Rankings y estadísticas de la plantilla                              |
| `/ping`                       | Monitorización                | Health check, responde `pong`                                        |

## Licencia

El proyecto se encuentra bajo la licencia MIT — ver [LICENSE](LICENSE) para ver los detalles.

---

Built by [@angelrbl](https://github.com/angelrbl)
