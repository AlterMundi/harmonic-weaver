# R07 · Membrana rectangular virtual

Primer núcleo experimental, separado del instrumento live. Implementación:
`harmonic_weaver.lab.research.membrane`. No cierra la investigación R07.

Modelo de ondas con bordes fijos, formas seno-producto y frecuencias
`f_mn = c/2 * sqrt((m/Lx)^2 + (n/Ly)^2)`. Referencia pedagógica primaria:
[Daniel Russell, Penn State: modos de membrana rectangular](https://www.acs.psu.edu/drussell/demos/membranesquare/square.html).

Cada modo satisface `q'' + 2γq' + ω²q = gain * shape(x_exc,y_exc) * PCM`.
Integración exacta por exponencial de matriz con fuerza constante durante
cada intervalo de muestra; salida en el extremo derecho del intervalo.
No hay keypoints, etiquetas corporales, interpolación de pose ni eventos.
Los bloques conservan estado; reset explícito comienza otra realización.

Configuración estricta: dimensiones en metros, velocidad de onda, cantidad
de modos por eje, amortiguación, frecuencia de muestreo, posición normalizada
de excitación y ganancia. Se rechazan modos sobre Nyquist e inputs no finitos.
PCM y ganancia representan fuerza sin calibración física: desplazamiento y
energía modal son proxies, no medidas de presión, metros o joules.
El truncamiento modal tampoco describe dinámica de arena o agua.

Verificación automática inicial: frecuencia/nodos/bordes, respuesta analítica
sin amortiguación a fuerza constante, decaimiento pasivo, igualdad exacta al
particionar bloques, reset y rechazo sin alterar estado. Cuatro pruebas:
`PYTHONPATH=src .venv/bin/python -m pytest tests/research/test_membrane.py -q`.

## Próximos cortes, necesarios para la entrega

- Adaptador de PCM verificado R05: frecuencia de muestreo declarada, ventana
  causal, preroll/reset y soporte temporal explícitos; no alimentar pose.
- Campo de desplazamiento y RMS temporal, nodos y controles con señales
  conocidas. Límites de memoria y duración; prueba de truncamiento modal.
- Worker, artifacts/manifest verificables, cancelación y recuperación de
  interrupciones siguiendo contratos R05/R06.
- API/UI con todos los parámetros, presets portables, visualización sincronizada
  y contraste entre estado de voces, mezcla final y membrana. No confundir estas
  rutas ni aplicar parámetros a live silenciosamente.
- Banco reproducible de señales/control y recuperación de atributos reservados.
  Las semejanzas de figuras no demuestran información conservada ni HIT.
- Medio físico: faltan actuador, membrana/material/bordes caracterizados,
  observación sincronizada y calibración. No se ha realizado escucha ni ensayo
  físico ni validación humana de esta implementación.
