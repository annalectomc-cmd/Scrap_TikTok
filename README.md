# API de scraping

## Ejecución local con navegador visible

La imagen contiene una pantalla virtual, Chromium y noVNC. Cuando TikTok
solicita un CAPTCHA, el navegador no se cierra: se puede ver e interactuar
desde el navegador del usuario.

1. Configure las variables de Instagram en `.env` y conserve las credenciales
   de Firebase fuera del repositorio.
2. Inicie el servicio:

   ```powershell
   docker compose up --build
   ```

3. La API queda disponible en `http://localhost:5000` y noVNC, sólo para la
   máquina local, en `http://localhost:6080/vnc.html`.

## Trabajos asíncronos

Para permitir una intervención humana, use estos endpoints en lugar de
`GET /scrap/comments`:

```http
POST /scrap/jobs
Content-Type: application/json

{
  "platform": 1,
  "profile": "nombre_del_perfil",
  "cant": 5,
  "type": 1,
  "scroll": 10
}
```

La respuesta es `202 Accepted` e incluye un `id`. Consulte su progreso con
`GET /scrap/jobs/{id}`. Los estados posibles son `queued`, `running`,
`captcha_required`, `completed` y `failed`.

Cuando el estado es `captcha_required`, la respuesta contiene `browser_url`.
El frontend puede cargarla en un iframe, por ejemplo:

```html
<iframe
  title="Resolver CAPTCHA"
  src="{browser_url_recibida_del_api}"
  width="100%"
  height="720"
  allow="clipboard-read; clipboard-write">
</iframe>
```

Después de que el usuario resuelva el CAPTCHA, el worker detecta que
desapareció y vuelve automáticamente a `running`; el frontend sólo debe seguir
consultando el estado. El límite de espera se configura con
`CAPTCHA_TIMEOUT_SECONDS` (900 segundos por defecto).

## Restricciones de esta primera versión

- Hay una sola pantalla y un solo navegador, por lo que se ejecuta un trabajo
  de scraping a la vez.
- Los trabajos se mantienen en memoria; reiniciar el contenedor los elimina.
- La notificación de CAPTCHA está integrada inicialmente para TikTok. Instagram
  y YouTube ya se ven en noVNC mientras corren, pero requieren incorporar sus
  selectores de CAPTCHA para cambiar su estado automáticamente.
- El puerto 6080 está limitado a `localhost` en `docker-compose.yml`. No debe
  exponerse públicamente. Para un despliegue web, un reverse proxy autenticado
  debe publicar noVNC y `NOVNC_PUBLIC_URL` debe contener esa ruta protegida.
