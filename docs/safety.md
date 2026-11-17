# Seguridad

El servidor inicia desarmado. La API actual solo altera estado simulado. E-stop enclava `EMERGENCY_STOP` hasta reinicio explícito, y desarma. Esto es lógica de software, no un corte eléctrico físico. Nunca energizar ni mover actuadores sin revisar alimentación, polaridad, tierra común, Echo a 3.3 V, geometría y calibración; el desarrollo actual no habilita hardware real.
