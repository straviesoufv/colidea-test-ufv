# Identidad visual UFV para colidea-test-ufv

## Referencia
Basado en la homepage pública `https://www.ufv.es`. El portal usa una estética sobria pero fresca: fondo claro, tipografía con remates para titulares y una paleta azul/naranja/verde con mucho contraste. Ese estilo es el que replicaremos en la interfaz del MVP (landing + controles) para que el profesorado lo perciba como continuidad institucional.

---

## Paleta principal
| Rol | Color | Uso sugerido |
| --- | --- | --- |
| **Fondo oscuro institucional** | `#001a33` | Header, footer, bloques resaltados y fondo de cards principales. |
| **Azul corporativo** | `#004773` | Botones primarios, títulos principales, iconografía educativa. |
| **Verde vibrante** | `#00d084` | Acciones secundarias, indicadores positivos, estados activos. |
| **Naranja energético** | `#ff6900` | Call-to-action en hero, badges de alertas, enlaces importantes. |
| **Neutros claros** | `#f6f7f7`, `#ffffff`, `#efefef` | Fondos generales, secciones intermedias, tarjetas de texto. |
| **Gris ceniza** | `#abb8c3`, `#111111` | Textos secundarios, iconografía menos prioritaria. |
| **Púrpura suave** | `#9b51e0` | Destacar mensajes inspiradores o contadores de impacto.

También aparecen gradientes suaves entre `#004773` y `#001a33` que dan sensación de profundidad; se pueden aplicar como fondo hero o barra superior.

---

## Tipografías
- **Cuerpo**: stack `-apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen-Sans', 'Ubuntu', 'Cantarell', 'Helvetica Neue', sans-serif`. Tipografía neutra y legible para formularios y textos largos.
- **Titulares / Callouts**: `"Roboto Slab", serif`. Se usa para titulares hero, banners de impacto y botones principales.
- **Iconos**: `revicons` (si desarrollas iconografía propia, se puede sustituir por `Font Awesome` o SVGs, manteniendo el contraste alto).

### Aplicación práctica
- Usa `Roboto Slab` en secciones hero, secciones de preguntas generadas y cabeceras de panel lateral.
- Mantén el cuerpo con el stack sans-serif para asegurar compatibilidad y coherencia con el resto del portal UFV.

---

## Ejemplo de CSS base para el MVP
```css
:root {
  --ufv-deep: #001a33;
  --ufv-royal: #004773;
  --ufv-spring: #00d084;
  --ufv-orange: #ff6900;
  --ufv-snow: #f6f7f7;
  --ufv-smoke: #efefef;
  --ufv-grey: #abb8c3;
  --ufv-purple: #9b51e0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
}

body {
  background: var(--ufv-snow);
  color: #111111;
  min-height: 100vh;
  margin: 0;
}

header {
  background: linear-gradient(120deg, var(--ufv-deep), #00385a);
  color: white;
  font-family: 'Roboto Slab', serif;
  padding: 3rem 2rem;
}

h1, h2, h3 {
  font-family: 'Roboto Slab', serif;
  color: var(--ufv-royal);
}

.btn-primary {
  background: var(--ufv-orange);
  color: white;
  border: none;
  border-radius: 999px;
  padding: 0.8rem 1.6rem;
  font-weight: 600;
}

.btn-secondary {
  background: var(--ufv-spring);
  color: var(--ufv-deep);
}

.panel-card {
  background: white;
  border-radius: 1rem;
  padding: 1.5rem;
  box-shadow: 0 20px 45px rgba(0, 26, 51, 0.12);
}

.tag-ufv {
  display: inline-flex;
  gap: 0.35rem;
  align-items: center;
  padding: 0.2rem 0.6rem;
  border-radius: 999px;
  font-size: 0.75rem;
  background: var(--ufv-spring);
  color: var(--ufv-deep);
  font-weight: 600;
}
```

Este CSS puede incluirse en la carpeta `static/` o `templates/` si abordas una interfaz React/Vanilla. Las variables definen la paleta UFV y luego aplicamos la tipografía serif para titulares y la sans-serif para cuerpo. Los botones usan colores vivos y las tarjetas tienen sombras suaves para dar profundidad.

---

## Próximos pasos para adaptar la UI
1. Crear una landing simple (hero + subida de temario + panel de configuración) usando la paleta anterior.
2. Añadir componentes de feedback — chips con niveles Bloom, listas de preguntas, badges `UFV` — con `tag-ufv` y `panel-card`.
3. Probar la accesibilidad con contraste alto (revisar `a11y.dev`); la paleta UFV ya tiene contraste suficiente entre `#001a33` y `#ffffff`.
4. Si se exportan datos a Excel/Word, usa botones secundarios con outline `var(--ufv-royal)` para mantener coherencia.

Cuando quieras, los siguientes pasos serán construir la parte visual (¿prefieres React + Vite o un front-end en FastAPI con Jinja?).
