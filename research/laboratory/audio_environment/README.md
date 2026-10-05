# Comparación de entornos del motor

Protocolo sintético, hardware-free: mismos controles, 150 bloques de 256 muestras
48 kHz, voces afinadas, modulación de gain, shape/pan/offset de fase y liberación.
No llama AudioEngine.start ni abre dispositivos. Raw float estéreo, control hash,
archivos del motor y versiones permiten revisar la comparación.

```bash
cd ~/Projects/harmonic-weaver
.venv/bin/python research/laboratory/audio_environment/compare.py --weaver-python .venv/bin/python --shaper-python ../harmonic-shaper/.venv/bin/python --shaper-dir ../harmonic-shaper --output /tmp/pcm-environment-new-run
```

Output debe ser nuevo. `--voices` admite 1, 6 o 32; evidencia incluida corresponde
sólo a seis. Python 3.12.13/NumPy 2.5.1 frente a Python 3.13.5/NumPy 2.4.6: motor
coincidente y PCM exacto en esa secuencia. No implica paridad universal, estado
live idéntico, latencia acústica ni aceptación humana. Las capturas corporales
no participan ni se publican. Los requests de evaluación fijan entorno para no
convertir una diferencia de dependencias en una reproducción asumida.
