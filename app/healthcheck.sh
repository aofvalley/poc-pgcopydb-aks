#!/bin/bash

# Verificar si pgcopydb está disponible
if command -v pgcopydb &> /dev/null; then
  # Intentar ejecutar pgcopydb --version
  if pgcopydb --version &> /dev/null; then
    echo "pgcopydb está funcionando correctamente"
    exit 0
  else
    echo "Error al ejecutar pgcopydb"
    exit 1
  fi
else
  echo "pgcopydb no está instalado o no está en el PATH"
  exit 1
fi