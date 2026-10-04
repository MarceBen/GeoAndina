import csv
import math
from calculations import dm_to_decimal, dms_to_decimal, calculate_ellipsoidal_height, calculate_orthometric_height
from utm import geodetic_to_utm
from utm import utm_to_geodetic

ALLOWED_EXTENSIONS = {"csv", "txt"}

# Rangos UTM hemisferio sur para Perú (zonas 17S, 18S y 19S)
UTM_MIN_EAST = 100000
UTM_MAX_EAST = 900000
UTM_MIN_NORTH = 7900000
UTM_MAX_NORTH = 10000000

# Ondulación geoidal máxima creíble (|h - H|, en metros) para detectar errores de digitación
MAX_ABS_UNDULATION = 100

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def detect_delimiter(lines):

    # Elige el separador según la primera línea con datos (tab > ; > ,).
    # Así funcionan archivos de Excel en español (separador ; y coma decimal).
    sample = lines[0]

    best = ","
    best_count = sample.count(",")

    for candidate in (";", "\t"):

        if sample.count(candidate) >= best_count and sample.count(candidate) > 0:
            best = candidate
            best_count = sample.count(candidate)

    return best


def is_number(text):

    try:
        float(text)
        return True

    except ValueError:
        return False


def read_rows(file):

    raw_bytes = file.read()

    file.seek(0)

    try:
        raw_text = raw_bytes.decode("utf-8-sig")

    except UnicodeDecodeError:
        raw_text = raw_bytes.decode("latin-1")

    lines = [line for line in raw_text.splitlines() if line.strip()]

    if not lines:
        raise ValueError("El archivo esta vacio o no tiene un formato valido")

    delimiter = detect_delimiter(lines)

    reader = csv.reader(lines, delimiter=delimiter)

    rows = []

    for row in reader:

        row = [cell.strip() for cell in row]

        # Con ; o tab, la coma es el separador decimal (275000,5 -> 275000.5)
        if delimiter != ",":
            row = [row[0]] + [cell.replace(",", ".") for cell in row[1:]]

        rows.append(row)

    # Si la primera fila es un encabezado (la segunda columna no es numérica), se omite
    if len(rows[0]) > 1 and not is_number(rows[0][1]):
        rows = rows[1:]

    if not rows:
        raise ValueError("El archivo esta vacio o no tiene un formato valido")

    return rows


def parse_geodetic_row(row, coordinate_format):

    number = row[0]

    if coordinate_format == "DD":

        if len(row) != 4:
            raise ValueError("El formato de la coordenada debe ser DD")

        try:

            latitude = float(row[1])
            longitude = float(row[2])
            height = float(row[3])

        except ValueError:
            raise ValueError(f"Error en el punto {number}")

        

    elif coordinate_format == "DM":

        if len(row) != 6:
            raise ValueError("El formato de la coordenada debe ser DM")

        try:

            latitude = dm_to_decimal(float(row[1]), float(row[2]))
            longitude = dm_to_decimal(float(row[3]), float(row[4]))
            height = float(row[5])

        except ValueError:
            raise ValueError(f"Error en el punto {number}")

       

    elif coordinate_format == "DMS":

        if len(row) != 8:
            raise ValueError("El formato de la coordenada debe ser DMS")

        try:

            latitude = dms_to_decimal(float(row[1]), float(row[2]), float(row[3]))
            longitude = dms_to_decimal(float(row[4]), float(row[5]), float(row[6]))
            height = float(row[7])

        except ValueError:
            raise ValueError(f"Error en el punto {number}")

    else:
        raise ValueError("Formato de coordenada inválido.")

    return number, latitude, longitude, height

def parse_utm_row(row):

    number = row[0]

    if len(row) != 4:
        raise ValueError ("El formato es invalido.")

    try:

        east = float(row[1])
        north = float(row[2])
        height = float(row[3])

    except ValueError:
        raise ValueError(f"Error en el punto {number}")

    if not all(math.isfinite(value) for value in (east, north, height)):
        raise ValueError(f"Error en el punto {number}: valor no válido")

    return number, east, north, height

def calculate_height(model, latitude, longitude, height, calculation_type):

    if calculation_type == "OrthometricHeight":

        ellipsoidal_height = height

        orthometric_height = calculate_orthometric_height(model, latitude, longitude, ellipsoidal_height)

    elif calculation_type == "EllipsoidalHeight":

        orthometric_height = height

        ellipsoidal_height = calculate_ellipsoidal_height(model, latitude, longitude, orthometric_height)

    else:

        raise ValueError ("Tipo de calculo inválido.")

    return orthometric_height, ellipsoidal_height


def parse_geodetic_file(file, model, coordinate_format, calculation_type):

    rows = read_rows(file)

    results = []

    for row in rows:

        number, latitude, longitude, height = parse_geodetic_row(row, coordinate_format)

        orthometric_height, ellipsoidal_height = calculate_height(model, latitude, longitude, height, calculation_type)

        results.append({

            "Number": number,

            "CalculationType": calculation_type,

            "Latitude": latitude,

            "Longitude": longitude,

            "OrthometricHeight": orthometric_height,

            "EllipsoidalHeight": ellipsoidal_height
        })

    return results

def parse_utm_file(file, model, utm_zone, calculation_type):

    rows = read_rows(file)

    results = []

    for row in rows:

        number, east, north, height = parse_utm_row(row)

        latitude, longitude = utm_to_geodetic(east, north, utm_zone)

        orthometric_height, ellipsoidal_height = calculate_height(model, latitude, longitude, height, calculation_type)

        results.append({

            "Number": number,

            "CalculationType": calculation_type,

            "Latitude": latitude,

            "Longitude": longitude,

            "OrthometricHeight": orthometric_height,

            "EllipsoidalHeight": ellipsoidal_height
        })

    return results

def parse_local_point_row(row):

    number = row[0] if row else ""

    if len(row) != 5:
        raise ValueError("El formato debe ser Punto, Este, Norte, Altura elipsoidal, Altura ortométrica")

    try:

        east = float(row[1])
        north = float(row[2])
        ellipsoidal_height = float(row[3])
        orthometric_height = float(row[4])

    except ValueError:
        raise ValueError(f"Error en el punto {number}")

    if not all(math.isfinite(value) for value in (east, north, ellipsoidal_height, orthometric_height)):
        raise ValueError(f"Error en el punto {number}: valor no válido (NaN o infinito)")

    if not (UTM_MIN_EAST <= east <= UTM_MAX_EAST) or not (UTM_MIN_NORTH <= north <= UTM_MAX_NORTH):
        raise ValueError(
            f"El punto {number} tiene coordenadas UTM fuera del rango de Perú "
            f"(Este {east}, Norte {north}). Verifique que no sean coordenadas geodésicas."
        )

    undulation = ellipsoidal_height - orthometric_height

    if abs(undulation) > MAX_ABS_UNDULATION:
        raise ValueError(
            f"El punto {number} tiene una ondulación h - H = {undulation:.2f} m, que no es creíble. "
            "Verifique el orden de las columnas: Punto, Este, Norte, Altura elipsoidal, Altura ortométrica."
        )

    return number, east, north, ellipsoidal_height, orthometric_height


def convert_geodetic_point_to_utm(latitude, longitude, utm_zone):


    east, north = geodetic_to_utm(longitude, latitude, utm_zone)

    return east, north


def parse_local_points_file(file, min_points, max_points):

    rows = read_rows(file)

    if not rows:
        raise ValueError("El archivo está vacío o no tiene un formato válido")

    if len(rows) > max_points or len(rows) < min_points:
        raise ValueError(f"La cantidad de puntos debe estar entre {min_points} y {max_points}")

    points = []
    seen_numbers = set()
    seen_coordinates = set()

    for row in rows:

        number, east, north, ellipsoidal_height, orthometric_height = parse_local_point_row(row)

        if number in seen_numbers:
            raise ValueError(f"El número de punto {number} está repetido.")

        if (east, north) in seen_coordinates:
            raise ValueError(f"El punto {number} repite las coordenadas de otro punto de control.")

        seen_numbers.add(number)
        seen_coordinates.add((east, north))

        points.append({

            "Number": number,

            "East": east,

            "North": north,

            "EllipsoidalHeight": ellipsoidal_height,

            "OrthometricHeight": orthometric_height
        })

    return points