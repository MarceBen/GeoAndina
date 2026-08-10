import csv
from calculations import dm_to_decimal, dms_to_decimal, calculate_ellipsoidal_height, calculate_orthometric_height
from utm import geodetic_to_utm
from utm import utm_to_geodetic

ALLOWED_EXTENSIONS = {"csv", "txt"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def read_rows(file):

    filename = file.filename
    extension = filename.rsplit(".", 1)[1].lower()

    if extension == "txt":
        delimiter = "\t"

    else:
        delimiter = ","

    raw_bytes = file.read()

    file.seek(0)

    try:
        raw_text = raw_bytes.decode("utf-8-sig")

    except UnicodeDecodeError:
        raw_text = raw_bytes.decode("latin-1")

    reader = csv.reader(raw_text.splitlines(), delimiter=delimiter)

    rows = []

    for row in reader:

        rows.append(row)

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

def parse_local_point_row(row, coordinate_system, coordinate_order):

    number = row[0]

    if coordinate_system == "UTM":

        if len(row) != 4:
            raise ValueError("El formato debe ser Punto, Este, Norte, H o Punto, Norte, Este, H")

        try:

            value_1 = float(row[1])
            value_2 = float(row[2])
            height = float(row[3])

        except ValueError:
            raise ValueError(f"Error en el punto {number}")

        if coordinate_order == "EN":

            east = value_1
            north = value_2

        elif coordinate_order == "NE":

            north = value_1
            east = value_2

        else:
            raise ValueError("Orden de coordenadas inválido.")

        return number, east, north, height

    elif coordinate_system == "Geodetic":

        if len(row) != 4:
            raise ValueError("El formato debe ser Punto, Latitud, Longitud, H")

        try:

            latitude = float(row[1])
            longitude = float(row[2])
            height = float(row[3])

        except ValueError:
            raise ValueError(f"Error en el punto {number}")

        return number, latitude, longitude, height

    else:
        raise ValueError("Sistema de coordenadas inválido.")


def convert_geodetic_point_to_utm(latitude, longitude, utm_zone):

    

    east, north = geodetic_to_utm(longitude, latitude, utm_zone)

    return east, north


def parse_local_points_file(file, coordinate_system, coordinate_order, utm_zone, min_points, max_points):

    rows = read_rows(file)

    if not rows:
        raise ValueError("El archivo está vacío o no tiene un formato válido")

    if len(rows) > max_points or len(rows) < min_points:
        raise ValueError(f"La cantidad de puntos debe estar entre {min_points} y {max_points}")

    points = []

    for row in rows:

        if coordinate_system == "UTM":

            number, east, north, height = parse_local_point_row(row, coordinate_system, coordinate_order)

        elif coordinate_system == "Geodetic":

            number, latitude, longitude, height = parse_local_point_row(row, coordinate_system, coordinate_order)

            if utm_zone is None:
                raise ValueError("Debe especificar la zona UTM para convertir coordenadas geodésicas")

            east, north = convert_geodetic_point_to_utm(latitude, longitude, utm_zone)

        else:
            raise ValueError("Sistema de coordenadas inválido.")

        points.append({

            "Number": number,

            "East": east,

            "North": north,

            "Height": height
        })

    return points