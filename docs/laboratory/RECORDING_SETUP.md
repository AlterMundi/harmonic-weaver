# Recording setup and destinations

The **Grabar** tab is beside **Captura**. It configures the next quick take;
Grabar / Detener y guardar remains beside the camera. This surface reuses the
existing capture/export engine and preserves instrument tuning, voice mappings,
listening volume and the large camera/figure layout.

## Where things run

Recording preferences, chosen folder handles and copy receipts belong to the
**browser and origin where the web page is open**. Nico and Annie can choose
their own destination without changing a server folder or another browser's
preferences. Google accounts are selected individually; there is no institutional
account hardcoded in source. Existing server-side destination preferences are
not imported automatically.

Camera tracking, audio synthesis and original capture archives still run on the
computer hosting the laboratory. Opening its page remotely does not move that
camera or audio engine to the browser's computer. The laboratory remains one
shared instrument, not an isolated multi-user recording service. To use another
computer's camera, run the existing laboratory on that computer.

## Composition

- Sound in the exported video is optional. Original PCM remains in the existing
  capture archive because its sample clock aligns the video. No microphone is
  added by this feature.
- The body overlay uses observed joints and existing projection/identity/gap
  rules. No interpolated pose is manufactured.
- The optional harmonic figure uses recorded pre-shape/limiter oscillator
  telemetry and the take's initial visual configuration. It is a geometric
  representation, not physical cymatics.
- Solo video y música disables both overlays and includes instrument sound.
- Quick takes remain bounded to 300 seconds. MP4 is convenient for playback;
  MKV retains uncompressed audio when sound is included. Both can be copied.

Settings and destination handles are retained in IndexedDB (`weaver-recording-v1`).
Clearing site data or changing browser profile/origin removes these choices and
receipts; original server recordings remain. Read/write permission can expire and
must be renewed with the explicit Autorizar carpeta button. Storage errors are
visible and do not silently reset the chosen destination.

## Save on the computer viewing the page

1. Open Grabar and choose Descargar en esta computadora, or Carpeta de esta
   computadora. Save the recording configuration.
2. For a folder, the browser's native picker grants read/write access on **this
   computer**. The selected FileSystemDirectoryHandle stays in this browser.
3. Record and stop. Keep the page open until Video listo and, for a folder,
   Copia en carpeta verificada. The copy is checked against the exported SHA-256
   and read back before reporting success.
4. For Descargar, open Tomas and click Descargar MP4 or Descargar original MKV.
   The browser's download preferences determine whether it asks for a folder.
   This route works when directory picking is unavailable.

Direct directory selection requires a supporting browser (Chrome/Edge) and a
secure context: HTTPS, localhost or a browser-recognized loopback origin.
Firefox/Safari, embedded browsers and plain-HTTP remote pages may offer only
normal downloads. A folder synchronized by Google Drive Desktop can be selected
like any other client folder; synchronization is handled by that application and
is not reported as a verified cloud upload by HarmoCap.

## Google Drive in the browser

Each person explicitly authorizes their own Google account and chooses a writable
**My Drive** folder using Google Picker. Institution accounts may be used if their
administrator permits this app. Shared Drives are currently rejected explicitly.
No OAuth token is sent to the laboratory backend or persisted in browser storage.
Tokens live in memory until disconnection, expiry or page close; reconnect after
reload. Disconnect clears this page's token; it does not revoke the entire Google
app grant. Google Account settings can revoke that grant separately.

One authorized maintainer must register the web application with Google:

1. In one Google Cloud project, enable Google Drive API and Google Picker API.
2. Configure OAuth consent and a **Web application** OAuth client. Register each
   exact JavaScript origin used, including the local development origin when
   appropriate. While in testing, admit the actual intended test accounts;
   external use depends on Google's app publishing and organization policies.
3. Create a browser API key restricted to the application's website origins,
   `https://docs.google.com/*` (Picker's iframe), and Drive/Picker APIs. Use the
   same project's numeric project number as the Picker App ID.
4. Copy `laboratory-ui/.env.example` to `.env.local`, then set
   `VITE_GOOGLE_CLIENT_ID`, `VITE_GOOGLE_API_KEY`, `VITE_GOOGLE_APP_ID`.
   These are **public browser identifiers**. Never put a client secret, access
   token, refresh token, service-account key or another application's credentials
   into a VITE variable. `.env.local` is ignored by Git.
5. Build using the existing startup command or `npm run build` in laboratory-ui.
   No second backend, account database or native desktop package is required.

Until this deployment configuration exists, Drive is visibly unavailable;
downloads and supported client folder saving still work. Configuring this code
is not proof of an actual OAuth login or upload. Connecting ChatGPT's Drive plugin
or a server's Online Accounts does not configure browser OAuth.

In the UI: Preparar Drive loads Google's SDK only on that explicit action, then
Conectar Drive opens account selection on a fresh click. The app requests
`drive.file`, plus `openid email` for account confirmation. It does not request
access to every Drive file. Choosing a Picker folder authorizes access to it;
connecting alone starts no recording and uploads no file. Choose the folder,
save the configuration, then make a take.

The app reserves file IDs before a resumable upload and persists those IDs before
writing bytes. It verifies Drive's size, SHA-256, filename and parent folder.
Missing checksum or uncertain acknowledgement remains unconfirmed. There is no
automatic retransmission or silent account switch; Verificar guardado reads the
same planned file ID. Browser upload URLs and tokens are never logged/stored.
Keep the page open through the verified result; background/mobile suspension and
five-minute sustained capacity have not been qualified. Browser transfers hash
one exported artifact in memory at a time; available memory limits large copies.

Primary API contracts: [File System Access](https://developer.chrome.com/docs/capabilities/web-apis/file-system-access),
[Google token model](https://developers.google.com/identity/oauth2/web/guides/use-token-model),
[Picker setup](https://developers.google.com/workspace/drive/picker/guides/web-picker-sample),
[Drive uploads](https://developers.google.com/workspace/drive/api/guides/manage-uploads),
[file checksums](https://developers.google.com/workspace/drive/api/reference/rest/v3/files).

## Existing native adapters

The local-only advanced recording-destination API remains compatible for existing
operator integrations: GTK/GIO picker, private provider/desktop bindings and
verified server-side copies. The Grabar web tab no longer invokes that picker or
uses its account/destination preferences. Native account bindings and tokens are
not migrated into browsers. Existing captures, exports and native receipts remain
on the host, without deletion or reinterpretation.

## Qualification boundaries

Browser tests use isolated browser storage, actual browser OPFS folder handles and
real synthetic media bytes. Google authorization, Picker and upload endpoints are
controlled fixtures: they test account choice, request scope, copy/checksum and
lost acknowledgement handling, not a production Google login. Actual OS folder
selection, Google project configuration, real provider consent/upload and physical
camera/audio acceptance remain separate from those tests.
