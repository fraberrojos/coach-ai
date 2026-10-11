Coach AI - Fase FTP automática

Archivos actualizados:
- activity.py: lectura de serie temporal de potencia desde atributos HA o FIT Garmin.
- ftp_test.py: detección del mejor bloque continuo de 20 min, FTP 20min x 0,95, cobertura, estabilidad y recomendación informativa.
- coordinator.py: detección automática de actividad FTP, lectura de potencia, comparación opcional con eFTP de cualquier sensor de Intervals.icu y notificación del resultado.
- sensor.py: sensores FTP existentes + cobertura y atributos de diagnóstico.
- button.py: se mantiene el botón Test FTP.
- manifest.json: añade fitdecode==0.11.0 para leer FIT Garmin.

Importante:
- El FTP real de Garmin nunca se modifica automáticamente.
- El análisis solo recomienda un FTP cuando el bloque se considera válido.
- La actividad se reconoce por el nombre FTP o, como respaldo, por la fecha programada + una actividad ciclista de 50-70 min.
