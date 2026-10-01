# La Pizarra Peluda

> Gestor de convocatorias y disponibilidad para un club deportivo amateur. Sustituye el "¿quién puede el jueves?" de WhatsApp por un enlace donde cada jugador marca cuándo **no puede**, y el club ve al instante qué franja horaria tiene menos bajas.

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

## Cómo funciona: disponibilidad inversa

En vez de preguntar "¿cuándo puedes?", la aplicación pregunta **"¿cuándo NO puedes?"**. Cada jugador marca sus franjas imposibles sobre un calendario semanal; la aplicación calcula automáticamente qué franja tiene menos bajas, y el staff del club confirma el horario final con un toque.

## Funcionalidades

- **Alta del club** (`/create_club`): la primera persona que entra crea el club y su cuenta de administrador en un único paso.
- **Cuentas solo para el staff**: el resto de jugadores nunca inician sesión. El admin genera un enlace de activación de un solo uso por cada miembro del staff, que fija su contraseña sin poder cambiar su nombre.
- **Generador de franjas horarias**: en vez de crear franjas una a una, el staff indica una horquilla de fechas, qué días de la semana, una ventana horaria diaria y la duración de cada franja — el sistema genera todas las combinaciones automáticamente.
- **Enlace público por evento** (`/e/{token}`), sin necesidad de iniciar sesión: el jugador elige su nombre en la lista del club y marca sus franjas imposibles sobre un calendario en rejilla, paginado por semanas.
- **Mapa de bajas** por franja para el staff, coloreado de verde (pocas bajas) a rojo (muchas), con confirmación del horario definitivo en un solo toque (con paso de confirmación explícito, para evitar confirmar por error).
- **Botón "Añadir a mi calendario"**, una vez confirmado el horario (plantilla de Google Calendar, sin necesidad de conectar una cuenta).
- **Panel de staff** (`/staff`): gestión del club, la plantilla de jugadores y los eventos. El admin del club puede crear y modificar estos datos.

## Stack técnico

| Capa | Tecnología |
|---|---|
| Interfaz | [NiceGUI](https://nicegui.io) (Python sobre Vue/Quasar) |
| Lenguaje | Python 3.11+ |
| ORM | SQLAlchemy 2.0 (declarative, sin SQLModel) |
| Base de datos | PostgreSQL ([Supabase](https://supabase.com)) en producción · SQLite en desarrollo local |
| Autenticación | Contraseñas con hash (Werkzeug), sesión vía almacenamiento de NiceGUI |
| Despliegue | [Render](https://render.com) |
| Gestión de dependencias | [Poetry](https://python-poetry.org) |
| Tests | pytest (dependencia de desarrollo) |

## Arquitectura

El proyecto sigue una arquitectura en tres capas estrictas: **las vistas nunca abren una sesión de base de datos directamente** — siempre pasan por `services/`.

```
lapizarrapeluda/
├── core/                     # configuración y conexión a la base de datos
│   ├── config.py               # variables de entorno
│   └── database.py             # engine, Base declarativa, get_session()
├── models/                   # tablas SQLAlchemy
│   ├── club.py, user.py, event.py, availability.py, token.py
├── services/                  # lógica de negocio — una función por caso de uso
│   ├── auth_service.py          # login, cambio de contraseña
│   ├── club_service.py           # alta/edición del club
│   ├── user_service.py            # jugadores y staff
│   ├── role_service.py             # roles (jugador/capitán/staff)
│   ├── event_service.py             # eventos y generación de franjas
│   ├── token_service.py              # enlaces de activación y de evento
│   ├── availability_service.py        # disponibilidad inversa
│   └── calendar_service.py             # enlace de Google Calendar
├── views/
│   ├── pages/                 # rutas @ui.page
│   ├── components/
│   │   └── staff_tabs/          # pestañas del panel de administración
│   ├── layout.py                # cabecera y guardas de sesión compartidas
│   └── theme.py                  # paleta de colores del club
├── static/                    # escudo del club y otros activos
├── main.py                     # punto de entrada
└── pyproject.toml
```

Cada función de servicio sigue el mismo patrón: abre su propia sesión (`with get_session() as session:`), y comunica errores de negocio con `raise ValueError("error_codigo")` en vez de devolver `None` o booleanos — las vistas traducen esos códigos a mensajes legibles.

## Modelo de datos (resumen)

| Tabla | Para qué sirve |
|---|---|
| `Club` | Una fila por despliegue (de momento, un solo club por instalación) |
| `User` | Jugadores y staff. La mayoría no tiene `password_hash` ni `is_active=True` — nunca inician sesión |
| `UserRole` | Etiquetas (jugador/capitán/staff) — puramente informativas, no controlan permisos |
| `Event` / `Slot` | Un evento y sus franjas horarias candidatas |
| `Unavailability` | El corazón del sistema: una fila = "este jugador no puede en esta franja". Ausencia de fila = disponible |
| `Token` | Enlaces de un solo uso, de dos tipos: activación de cuenta de staff, o acceso público a un evento |

## Rutas principales

| Ruta | Quién la usa | Qué hace |
|---|---|---|
| `/create_club` | Nadie (una sola vez) | Arranca el club y su admin |
| `/login` | Staff | Nombre + contraseña |
| `/activate/{token}` | Staff invitado | Fija su contraseña, nombre no editable |
| `/staff` | Staff | Club · Plantilla · Eventos |
| `/staff/events/new` | Staff | Crear evento con franjas generadas |
| `/staff/events/{id}` | Staff | Enlace, mapa de bajas, confirmar horario |
| `/e/{token}` | Cualquier jugador, sin sesión | Elegir nombre y marcar indisponibilidad, o ver el horario confirmado |

## Licencia

El proyecto se encuentra bajo la licencia MIT — ver [LICENSE](LICENSE) para ver los detalles.

---

<div align="center">
Built by <a href="https://github.com/angelrbl">@angelrbl</a>
</div>