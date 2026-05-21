```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import json
import subprocess
import os
import re
import requests
import shutil

def leer_exif(archivo):
    try:
        salida = subprocess.check_output(
            ["exiftool", "-json", archivo],
            timeout=5,
            stderr=subprocess.STDOUT
        ).decode()
        return json.loads(salida)[0]
    except subprocess.TimeoutExpired:
        print("Error: exiftool tardó demasiado y fue detenido.")
        exit(1)
    except FileNotFoundError:
        print("Error: El comando 'exiftool' no fue encontrado.")
        print("Asegúrate de que esté instalado y en el PATH del sistema.")
        exit(1)
    except Exception as e:
        print(f"Error ejecutando exiftool: {e}")
        exit(1)

def dms_to_decimal(dms_str):
    patron = r'([\d\.]+)\s*deg\s*([\d\.]+)\'\s*([\d\.]+)"\s*([NSEW])'
    m = re.match(patron, dms_str.strip())

    if not m:
        return None

    grados = float(m.group(1))
    minutos = float(m.group(2))
    segundos = float(m.group(3))
    ref = m.group(4).upper()

    decimal = grados + minutos / 60 + segundos / 3600

    if ref in ("S", "W"):
        decimal *= -1

    return decimal

def google_maps(lat, lon):
    return f"https://www.google.com/maps?q={lat},{lon}"

def reverse_geocode(lat, lon):
    try:
        url = (
            f"https://nominatim.openstreetmap.org/reverse"
            f"?format=json&lat={lat}&lon={lon}"
            f"&zoom=18&addressdetails=1"
        )

        headers = {
            "User-Agent": "Meta-OSINT-Tool/1.0"
        }

        r = requests.get(url, headers=headers, timeout=5)
        r.raise_for_status()

        data = r.json()

        return data.get("display_name", "No encontrado")

    except (requests.exceptions.RequestException, json.JSONDecodeError) as e:
        return f"Error obteniendo dirección: {e}"

if __name__ == "__main__":

    if not shutil.which("exiftool"):
        print("Error: El comando 'exiftool' no fue encontrado.")
        print("Instálalo y asegúrate de que esté en el PATH del sistema.")
        print("En Kali/Ubuntu: sudo apt install libimage-exiftool-perl")
        exit(1)

    parser = argparse.ArgumentParser(
        description="Meta-OSINT Tool - Análisis forense de metadatos EXIF para imágenes",
        epilog="Ejemplo: python3 meta_osint.py imagen.jpg"
    )

    parser.add_argument(
        "archivo",
        help="Ruta de la imagen a analizar"
    )

    args = parser.parse_args()

    print("Analizando imagen...")

    if not os.path.isfile(args.archivo):
        print("Archivo no encontrado.")
        exit(1)

    print("Ejecutando exiftool...")

    exif = leer_exif(args.archivo)

    marca = exif.get("Make", "Desconocido")
    modelo = exif.get("Model", "Desconocido")

    nombre_txt = (
        f"{marca}_{modelo}_analisis.txt"
        .replace(" ", "_")
        .replace("/", "_")
    )

    lat_dms = exif.get("GPSLatitude")
    lon_dms = exif.get("GPSLongitude")

    with open(nombre_txt, "w", encoding="utf-8") as f:

        f.write("=" * 60 + "\n")
        f.write("META-OSINT TOOL - REPORTE DE ANÁLISIS\n")
        f.write("=" * 60 + "\n\n")

        f.write(f"Marca: {marca}\n")
        f.write(f"Modelo: {modelo}\n\n")

        if lat_dms and lon_dms:

            lat = dms_to_decimal(lat_dms)
            lon = dms_to_decimal(lon_dms)

            f.write("INFORMACIÓN DE GEOLOCALIZACIÓN\n")
            f.write("-" * 40 + "\n")

            f.write(f"Latitud DMS : {lat_dms}\n")
            f.write(f"Longitud DMS: {lon_dms}\n")
            f.write(f"Latitud DEC : {lat}\n")
            f.write(f"Longitud DEC: {lon}\n\n")

            f.write(f"Google Maps: {google_maps(lat, lon)}\n")

            direccion = reverse_geocode(lat, lon)

            f.write(f"\nDirección aproximada: {direccion}\n\n")

        else:
            f.write("Geolocalización: NO DETECTADA\n\n")

        f.write("\n" + "=" * 60 + "\n")
        f.write("METADATOS COMPLETOS\n")
        f.write("=" * 60 + "\n\n")

        traducciones = {
            "ExifTool Version Number": "Versión de ExifTool",
            "File Name": "Nombre del Archivo",
            "Directory": "Directorio",
            "File Size": "Tamaño del Archivo",
            "File Modification Date/Time": "Fecha de Modificación",
            "File Access Date/Time": "Fecha de Acceso",
            "File Inode Change Date/Time": "Fecha de Cambio de Inodo",
            "File Permissions": "Permisos del Archivo",
            "File Type": "Tipo de Archivo",
            "File Type Extension": "Extensión del Archivo",
            "MIME Type": "Tipo MIME",
            "Make": "Marca",
            "Camera Model Name": "Modelo de Cámara",
            "Model": "Modelo",
            "X Resolution": "Resolución X",
            "Y Resolution": "Resolución Y",
            "Resolution Unit": "Unidad de Resolución",
            "Software": "Software",
            "Modify Date": "Fecha de Modificación",
            "Date/Time Original": "Fecha/Hora Original",
            "Create Date": "Fecha de Creación",
            "GPS Latitude Ref": "Referencia de Latitud GPS",
            "GPS Longitude Ref": "Referencia de Longitud GPS",
            "GPS Altitude Ref": "Referencia de Altitud GPS",
            "GPS Time Stamp": "Marca de Tiempo GPS",
            "GPS Img Direction Ref": "Referencia de Dirección de Imagen GPS",
            "GPS Img Direction": "Dirección de Imagen GPS",
            "GPS Date Stamp": "Fecha GPS",
            "GPS Latitude": "Latitud GPS (DMS)",
            "GPS Longitude": "Longitud GPS (DMS)",
            "GPS Position": "Posición GPS (DMS)",
            "Megapixels": "Megapíxeles",
            "Image Width": "Ancho de Imagen",
            "Image Height": "Alto de Imagen",
            "Encoding Process": "Proceso de Codificación",
            "Bits Per Sample": "Bits por Muestra",
            "Color Components": "Componentes de Color",
            "YCbCr Sub Sampling": "Submuestreo YCbCr",
            "Orientation": "Orientación",
            "Exposure Time": "Tiempo de Exposición",
            "F Number": "Número F",
            "ISO": "ISO",
            "Shutter Speed": "Velocidad de Obturación",
            "Aperture": "Apertura",
            "Light Value": "Valor de Luz"
        }

        for k, v in exif.items():
            clave_traducida = traducciones.get(k, k)
            f.write(f"{clave_traducida}: {v}\n")

    print("\n" + "=" * 60)
    print("RESUMEN DEL ANÁLISIS")
    print("=" * 60)

    print(f"\nDispositivo:")
    print(f"   • Marca: {marca}")
    print(f"   • Modelo: {modelo}")

    if lat_dms and lon_dms:

        lat = dms_to_decimal(lat_dms)
        lon = dms_to_decimal(lon_dms)

        print(f"\nGeolocalización: DETECTADA")
        print(f"   • Latitud:  {lat_dms}")
        print(f"   • Longitud: {lon_dms}")
        print(f"   • Decimal:  {lat:.6f}°, {lon:.6f}°")
        print(f"   • Ver en mapa: {google_maps(lat, lon)}")

        direccion = reverse_geocode(lat, lon)

        if "Error" not in direccion:
            print(f"   • Ubicación: {direccion[:100]}...")

    else:
        print(f"\nGeolocalización: NO DETECTADA")

    fecha_original = (
        exif.get("Date/Time Original")
        or exif.get("Create Date")
    )

    if fecha_original:
        print(f"\nFecha de captura: {fecha_original}")

    if "Image Width" in exif and "Image Height" in exif:

        print(
            f"\nDimensiones: "
            f"{exif['Image Width']} × {exif['Image Height']} px"
        )

        if "Megapixels" in exif:
            print(f"   • Resolución: {exif['Megapixels']} MP")

    if "Software" in exif and exif["Software"] != "Desconocido":
        print(f"\nEditada con: {exif['Software']}")

    print(f"\nReporte completo guardado en:")
    print(f"   → {nombre_txt}")

    print("\n" + "=" * 60)
    print("Meta-OSINT Tool - Análisis completado")
    print("=" * 60)
```
