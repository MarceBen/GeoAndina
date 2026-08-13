from flask import Flask, render_template, request, redirect, url_for, session
from egm2008 import EGModel2008
from calculations import calculate_orthometric_height, dm_to_decimal, dms_to_decimal, calculate_ellipsoidal_height
from utm import utm_to_geodetic
from imports import parse_geodetic_file, parse_utm_file, allowed_file, parse_local_points_file, convert_geodetic_point_to_utm, read_rows, parse_geodetic_row, parse_utm_row
from geoidlocalmodel import LocalModel
from dotenv import load_dotenv
from pathlib import Path

import os
import threading
import webview
import time
import sys
from verifier import load_embedded_public_key, verify_license_file
from machine_id import get_machine_id



MAX_QUANTITY = 10000
MIN_QUANTITY = 1


LOCAL_MODEL_K = 4

if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys._MEIPASS)
else:
    BASE_DIR = Path(__file__).parent

env_path = BASE_DIR / ".env"

load_dotenv(env_path)

ACCESS_PASSWORD = os.getenv("ACCESS_PASSWORD")
SECRET_KEY = os.getenv("SECRET_KEY")


app = Flask(__name__)

app.secret_key = SECRET_KEY

def verify_geoandina_license():
    license_path = BASE_DIR / "GeoAndina.lic"
    public_key_path = BASE_DIR / "geoandina_public_key.pem"

    if not license_path.exists():
        return False, "No se encontró el archivo de licencia."

    if not public_key_path.exists():
        return False, "No se encontró la clave pública."

    try:
        public_key = load_embedded_public_key(
            public_key_path.read_bytes()
        )

        current_machine_id = get_machine_id()

        return verify_license_file(
            license_path,
            public_key,
            current_machine_id,
            expected_product="GeoAndina"
        )

    except Exception as exc:
        return False, f"No se pudo verificar la licencia: {exc}"


model = EGModel2008()


local_model = None

@app.route("/initialize")
def initialize():

    model.load_model()

    return "", 204


def normalize_imported_results(raw_results):
    normalized = []

    for row in raw_results:

        normalized.append({
            "PointNumber": row.get("Number"),
            "CalculationType": row["CalculationType"],
            "latitude": row["Latitude"],
            "longitude": row["Longitude"],
            "orthometric_height": float(row["OrthometricHeight"]),
            "ellipsoidal_height": float(row["EllipsoidalHeight"]),
        })

    return normalized


@app.route("/")
def home():
    return render_template("loading.html")

@app.route("/login", methods=["GET", "POST"])
def login():

    if session.get("Logged") == True:
        return redirect(url_for("premain_menu"))

    if request.method == "GET":
        return render_template("login.html")

    elif request.method == "POST":
        password = request.form.get("password")

        if password == ACCESS_PASSWORD:
            session["Logged"] = True
            return redirect(url_for("premain_menu"))
        
        else:
            return render_template("login.html", error = "Contraseña Incorrecta")


@app.route("/premain_menu", methods=["GET", "POST"])
def premain_menu():

    if session.get("Logged") != True:
        return redirect(url_for("login"))

    if request.method == "GET":
        return render_template("premain_menu.html")

    height_model = request.form.get("HeightModel")

    if height_model not in ("EGM2008", "Local"):
        return render_template("premain_menu.html", error="Seleccione un modelo geoidal válido.")

    session["HeightModel"] = height_model

    if height_model == "Local":
  
        return redirect(url_for("utm_zone"))

    return redirect(url_for("main_menu"))


@app.route("/main_menu", methods=["GET", "POST"])
def main_menu():

    if session.get("Logged") != True:
        return redirect(url_for("login"))

    if request.method == "GET":
        return render_template("main_menu.html")

    coordinate_type = request.form.get("CoordinateType")

    if coordinate_type == "Geodetic":
        return redirect(url_for("geodetic"))

    elif coordinate_type == "UTM":
        return redirect(url_for("utm_zone"))

    return render_template("main_menu.html")



@app.route("/geodetic", methods=["GET", "POST"])

def geodetic():

    if session.get("Logged") != True:
        return redirect(url_for("login"))
    

    results = None
    quantity = None

    if request.method == "POST":

        try:

            action = request.form.get("action")

            if action == "main_menu":
                return redirect(url_for("main_menu"))   

            quantity = int(request.form.get("quantity", 1))

            if quantity > MAX_QUANTITY or quantity < MIN_QUANTITY:
                raise ValueError("La cantidad debe estar entre 1 y 10000")



            if action  == "generate":

                return render_template("geodetic.html", quantity=quantity)

            elif action == "calculate":

                results = []
            
                for i in range (quantity):
                    
                    calculation_type = request.form.get(f"CalculationType_{i}")
                    coordinate_format = request.form.get(f"CoordinateFormat_{i}")

                    if coordinate_format == "DD":
            
                        latitude = float(request.form.get(f"Latitude_{i}", 0 ))
                        longitude = float(request.form.get(f"Longitude_{i}", 0 ))
            
                    elif coordinate_format == "DM":
            
                        latitude_degree = float(request.form.get(f"LatitudeDegree_{i}", 0 ))
                        latitude_minutes = float(request.form.get(f"LatitudeMinutes_{i}", 0 ))
            
                        latitude = dm_to_decimal(latitude_degree, latitude_minutes)
            
                        longitude_degree = float(request.form.get(f"LongitudeDegree_{i}", 0 ))
                        longitude_minutes = float(request.form.get(f"LongitudeMinutes_{i}", 0 ))
            
                        longitude = dm_to_decimal(longitude_degree, longitude_minutes)
            
            
                    elif coordinate_format == "DMS":
            
                        latitude_degree = float(request.form.get(f"LatitudeDegreeDMS_{i}", 0 ))
                        latitude_minutes = float(request.form.get(f"LatitudeMinutesDMS_{i}", 0 ))
                        latitude_seconds = float(request.form.get(f"LatitudeSecondsDMS_{i}", 0 ))
            
                        latitude = dms_to_decimal(latitude_degree, latitude_minutes, latitude_seconds)
            
                        longitude_degree = float(request.form.get(f"LongitudeDegreeDMS_{i}", 0 ))
                        longitude_minutes = float(request.form.get(f"LongitudeMinutesDMS_{i}", 0 ))
                        longitude_seconds = float(request.form.get(f"LongitudeSecondsDMS_{i}", 0 ))
            
                        longitude = dms_to_decimal(longitude_degree, longitude_minutes, longitude_seconds)
            
                    else:
                        raise ValueError("Formato de coordenada no válido")

               

                    if session.get("HeightModel") == "Local":

                        if local_model is None:
                            raise ValueError("Debe importar o construir los puntos del modelo geoidal local antes de calcular")

                        local_zone = session.get("UTMZone")

                        if local_zone is None:
                            raise ValueError("Debe seleccionar una zona UTM para el modelo local")

                        point_east, point_north = convert_geodetic_point_to_utm(latitude, longitude, local_zone)

                        if calculation_type == "OrthometricHeight":
                            height_value = float(request.form.get(f"EllipsoidalHeight_{i}", 0 ))
                        elif calculation_type == "EllipsoidalHeight":
                            height_value = float(request.form.get(f"OrthometricHeight_{i}", 0 ))
                        else:
                            raise ValueError("Tipo de cálculo no válido")

                        local_result = local_model.calculate_result(point_east, point_north, height_value, calculation_type, LOCAL_MODEL_K)

                        orthometric_height = local_result["OrthometricHeight"]
                        ellipsoidal_height = local_result["EllipsoidalHeight"]

                    elif calculation_type == "OrthometricHeight":
                                    
                        ellipsoidal_height = float(request.form.get(f"EllipsoidalHeight_{i}", 0 ))
                                    
                        orthometric_height = calculate_orthometric_height(model, latitude, longitude, ellipsoidal_height)
                                    
                    elif calculation_type == "EllipsoidalHeight":
                                    
                        orthometric_height = float(request.form.get(f"OrthometricHeight_{i}", 0 ))
                                        
                        ellipsoidal_height = calculate_ellipsoidal_height(model, latitude, longitude, orthometric_height)
                                    
                    else:
                        raise ValueError("Tipo de cálculo no válido")

                    

                    results.append ({
                            "CalculationType": calculation_type,
                            "latitude": latitude,
                            "longitude": longitude,
                            "orthometric_height": float(orthometric_height), 
                            "ellipsoidal_height": float(ellipsoidal_height)
                            })

                                    
                return render_template("geodetic.html", quantity = quantity, results=results)

            elif action == "main_menu":
                return redirect(url_for("main_menu"))
            
            else:
                raise ValueError("Accion Invalida")   

        except ValueError as e:
            return render_template("geodetic.html", quantity = 1, results = results, error = str(e))

        except Exception as e:
            return render_template("geodetic.html", quantity = quantity, results = results, error = "Ocurrio un error inesperado")

    return render_template("geodetic.html", quantity = quantity, results = results)


@app.route("/geodetic/import", methods=["POST"])
def geodetic_import():

    if session.get("Logged") != True:
        return redirect(url_for("login"))

    try:

        uploaded_file = request.files.get("file")
        coordinate_format = request.form.get("CoordinateFormat")
        calculation_type = request.form.get("CalculationType")

        if not uploaded_file or uploaded_file.filename == "":
            raise ValueError("Debe seleccionar un archivo para importar")

        if not allowed_file(uploaded_file.filename):
            raise ValueError("Formato de archivo no soportado. Use .csv o .txt")

        if session.get("HeightModel") == "Local":

            if local_model is None:
                raise ValueError("Debe importar o construir los puntos del modelo geoidal local antes de calcular")

            local_zone = session.get("UTMZone")

            if local_zone is None:
                raise ValueError("Debe seleccionar una zona UTM para el modelo local")

            rows = read_rows(uploaded_file)

            results = []

            for row in rows:

                number, latitude, longitude, height = parse_geodetic_row(row, coordinate_format)

                point_east, point_north = convert_geodetic_point_to_utm(latitude, longitude, local_zone)

                local_result = local_model.calculate_result(point_east, point_north, height, calculation_type, LOCAL_MODEL_K)

                results.append({
                    "PointNumber": number,
                    "CalculationType": calculation_type,
                    "latitude": latitude,
                    "longitude": longitude,
                    "orthometric_height": float(local_result["OrthometricHeight"]),
                    "ellipsoidal_height": float(local_result["EllipsoidalHeight"]),
                })

        else:

            raw_results = parse_geodetic_file(uploaded_file, model, coordinate_format, calculation_type)

            results = normalize_imported_results(raw_results)

        return render_template("geodetic.html", quantity=len(results), results=results)

    except ValueError as e:
        return render_template("geodetic.html", quantity=None, results=None, error=str(e))

    except Exception:
        return render_template(
            "geodetic.html", quantity=None, results=None,
            error="Ocurrio un error inesperado al importar el archivo"
        )


@app.route("/utm_zone", methods=["GET", "POST"])
def utm_zone():

    if session.get("Logged") != True:
        return redirect(url_for("login"))

    if request.method == "GET":
        return render_template("utm_zone.html")

    if request.method == "POST":

        global local_model

        utm_zone = request.form.get("UTMZone")

        if utm_zone not in ["17", "18", "19"]:
            return render_template("utm_zone.html", error="Seleccione una zona válida.")

        previous_zone = session.get("UTMZone")
        zone_changed = previous_zone != int(utm_zone)

        session["UTMZone"] = int(utm_zone)

        if session.get("HeightModel") == "Local":

            if local_model is None or zone_changed:
                local_model = None
                return redirect(url_for("local_model_page"))

            return redirect(url_for("utm"))

        return redirect(url_for("utm"))

@app.route("/utm", methods=["GET", "POST"])

def utm():

    if session.get("Logged") != True:
        return redirect(url_for("login"))

    results = None
    quantity = None

    if request.method == "POST":
         
        try:
        
            action = request.form.get("action")

            if action == "main_menu":
                return redirect(url_for("main_menu"))

            if action == "return_utmzone":
                return redirect(url_for("utm_zone"))
            
            quantity = int(request.form.get("quantity", 1))
        
            if quantity > MAX_QUANTITY or quantity < MIN_QUANTITY:
                raise ValueError("La cantidad debe estar entre 1 y 10000")
        
            if action  == "generate":
        
                return render_template("utm.html", quantity=quantity)
        
            elif action == "calculate":
        
                        results = []
                    
                        for i in range (quantity):
                            
                            calculation_type = request.form.get(f"CalculationType_{i}")

                            east = float(request.form.get(f"East_{i}", 0))
                            north = float(request.form.get(f"North_{i}", 0))

                            utm_zone = session.get("UTMZone")

                            latitude, longitude = utm_to_geodetic(east, north, utm_zone)
                            

                            if session.get("HeightModel") == "Local":

                                if local_model is None:
                                    raise ValueError("Debe importar o construir los puntos del modelo geoidal local antes de calcular")

                                if calculation_type == "OrthometricHeight":
                                    height_value = float(request.form.get(f"EllipsoidalHeight_{i}", 0 ))
                                elif calculation_type == "EllipsoidalHeight":
                                    height_value = float(request.form.get(f"OrthometricHeight_{i}", 0 ))
                                else:
                                    raise ValueError("Tipo de cálculo no válido")

                                local_result = local_model.calculate_result(east, north, height_value, calculation_type, LOCAL_MODEL_K)

                                orthometric_height = local_result["OrthometricHeight"]
                                ellipsoidal_height = local_result["EllipsoidalHeight"]

                            elif calculation_type == "OrthometricHeight":
                                            
                                ellipsoidal_height = float(request.form.get(f"EllipsoidalHeight_{i}", 0 ))
                                            
                                orthometric_height = calculate_orthometric_height(model, latitude, longitude, ellipsoidal_height)
                                            
                            elif calculation_type == "EllipsoidalHeight":
                                            
                                orthometric_height = float(request.form.get(f"OrthometricHeight_{i}", 0 ))
                                                
                                ellipsoidal_height = calculate_ellipsoidal_height(model, latitude, longitude, orthometric_height)
                                            
                            else:
                                raise ValueError("Tipo de cálculo no válido")
        
                            
        
                            results.append ({
                                    "CalculationType": calculation_type,
                                    "latitude": latitude,
                                    "longitude": longitude,
                                    "orthometric_height": float(orthometric_height), 
                                    "ellipsoidal_height": float(ellipsoidal_height)
                                    })
        
                                            
                        return render_template("utm.html", quantity = quantity, results=results)
             
            elif action == "main_menu":
                    return redirect(url_for("main_menu"))
            
            elif action == "return_utmzone":
                    return redirect(url_for("utm_zone"))
                   
            else:
                raise ValueError("Accion Invalida")   
        
        except ValueError as e:
                    return render_template("utm.html", quantity = 1, results = results, error = str(e))
        
        except Exception as e:
            return render_template("utm.html", quantity = quantity, results = results, error = "Ocurrio un error inesperado")
        
    return render_template("utm.html", quantity = quantity, results = results)


@app.route("/utm/import", methods=["POST"])
def utm_import():

    if session.get("Logged") != True:
        return redirect(url_for("login"))

    try:

        uploaded_file = request.files.get("file")
        utm_zone_value = request.form.get("UTMZone")
        calculation_type = request.form.get("CalculationType")

        if not uploaded_file or uploaded_file.filename == "":
            raise ValueError("Debe seleccionar un archivo para importar")

        if not allowed_file(uploaded_file.filename):
            raise ValueError("Formato de archivo no soportado. Use .csv o .txt")

        if session.get("HeightModel") == "Local":

            if local_model is None:
                raise ValueError("Debe importar o construir los puntos del modelo geoidal local antes de calcular")

            local_zone = session.get("UTMZone")

            if local_zone is None:
                raise ValueError("Debe seleccionar una zona UTM para el modelo local")

            rows = read_rows(uploaded_file)

            results = []

            for row in rows:

                number, east, north, height = parse_utm_row(row)

                latitude, longitude = utm_to_geodetic(east, north, local_zone)

                local_result = local_model.calculate_result(east, north, height, calculation_type, LOCAL_MODEL_K)

                results.append({
                    "PointNumber": number,
                    "CalculationType": calculation_type,
                    "latitude": latitude,
                    "longitude": longitude,
                    "orthometric_height": float(local_result["OrthometricHeight"]),
                    "ellipsoidal_height": float(local_result["EllipsoidalHeight"]),
                })

        else:

            if utm_zone_value not in ["17", "18", "19"]:
                raise ValueError("Seleccione una zona UTM válida")

            session["UTMZone"] = int(utm_zone_value)

            raw_results = parse_utm_file(uploaded_file, model, session["UTMZone"], calculation_type)

            results = normalize_imported_results(raw_results)

        return render_template("utm.html", quantity=len(results), results=results)

    except ValueError as e:
        return render_template("utm.html", quantity=None, results=None, error=str(e))

    except Exception:
        return render_template(
            "utm.html", quantity=None, results=None,
            error="Ocurrio un error inesperado al importar el archivo"
        )


@app.route("/local_model", methods=["GET", "POST"])
def local_model_page():

    if session.get("Logged") != True:
        return redirect(url_for("login"))

    global local_model

    quantity = None
    point_count = len(local_model.points) if local_model is not None else None

    if request.method == "POST":

        try:

            action = request.form.get("action")

            if action == "main_menu":
                return redirect(url_for("main_menu"))

            if action == "return_utmzone":
                return redirect(url_for("utm_zone"))

            quantity = int(request.form.get("quantity", 1))

            if quantity > MAX_QUANTITY or quantity < MIN_QUANTITY:
                raise ValueError("La cantidad debe estar entre 1 y 10000")

            if action == "generate":

                return render_template("local_model.html", quantity=quantity, point_count=point_count)

            elif action == "build":

                utm_zone_value = session.get("UTMZone")

                if utm_zone_value is None:
                    raise ValueError("Debe seleccionar una zona UTM antes de construir el modelo local")

                points = []

                for i in range(quantity):

                    east = float(request.form.get(f"East_{i}", 0))
                    north = float(request.form.get(f"North_{i}", 0))
                    height = float(request.form.get(f"Height_{i}", 0))

                    points.append({
                        "Number": i + 1,
                        "East": east,
                        "North": north,
                        "Height": height
                    })

                new_local_model = LocalModel(points)
                new_local_model.vertices = model.vertices
                new_local_model.buildkd_tree()
                new_local_model.calculate_points_geoid(utm_zone_value)

                local_model = new_local_model

                return render_template("local_model.html", quantity=None, point_count=len(points))

            else:
                raise ValueError("Accion Invalida")

        except ValueError as e:
            return render_template("local_model.html", quantity = 1, point_count=point_count, error=str(e))

        except Exception:
            return render_template("local_model.html", quantity=quantity, point_count=point_count, error="Ocurrio un error inesperado")

    return render_template("local_model.html", quantity=quantity, point_count=point_count)


@app.route("/local_model/import", methods=["POST"])
def local_model_import():

    if session.get("Logged") != True:
        return redirect(url_for("login"))

    global local_model

    try:

        uploaded_file = request.files.get("file")
        coordinate_system = request.form.get("CoordinateSystem")
        coordinate_order = request.form.get("CoordinateOrder")
        utm_zone_value = session.get("UTMZone")

        if not uploaded_file or uploaded_file.filename == "":
            raise ValueError("Debe seleccionar un archivo para importar")

        if not allowed_file(uploaded_file.filename):
            raise ValueError("Formato de archivo no soportado. Use .csv o .txt")

        if utm_zone_value is None:
            raise ValueError("Debe seleccionar una zona UTM antes de importar los puntos")

        points = parse_local_points_file(
            uploaded_file, coordinate_system, coordinate_order, utm_zone_value,
            MIN_QUANTITY, MAX_QUANTITY
        )

        new_local_model = LocalModel(points)
        new_local_model.vertices = model.vertices
        new_local_model.buildkd_tree()
        new_local_model.calculate_points_geoid(utm_zone_value)

        local_model = new_local_model

        return render_template("local_model.html", point_count=len(points))

    except ValueError as e:
        return render_template("local_model.html", point_count=None, error=str(e))

    except Exception:
        return render_template(
            "local_model.html", point_count=None,
            error="Ocurrio un error inesperado al importar los puntos del modelo local"
        )


def run_flask():
    app.run(host="127.0.0.1", port=5000, debug=False, use_reloader=False)
        
if __name__ == "__main__":

    valid, message = verify_geoandina_license()
    if not valid:
        print(f"\nERROR DE LICENCIA: {message}")
        input("\nPresione ENTER para cerrar...")
        sys.exit(1)
        
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    time.sleep(2)

    webview.create_window(title="GeoAndina v1.1", url="http://127.0.0.1:5000", width=1280, height=800, resizable=True)

    webview.start()