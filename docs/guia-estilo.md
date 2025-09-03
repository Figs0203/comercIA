# Guía de estilo de programación

## Python / Django
- Nombres descriptivos; evita abreviaturas.
- Vistas del usuario final deben extender `products/base.html`.
- Separar lógica de negocio en servicios/módulos (evitar vistas “gordas”).
- Validar entradas, manejar errores con claridad.
- Mantener `migrations` versionadas.

## Templates
- HTML semántico; reutiliza bloques de `base.html`.
- No mezclar mucha lógica en templates; usar filtros y context.

## Git
- Commits pequeños y con mensaje claro.
- Pull Requests con descripción y relación a la tarea del Project.

## Estilo
- PEP8, 4 espacios de indentación, líneas < 100 caracteres cuando sea posible.

