from flask import Flask, render_template, request, redirect, url_for, session
from egm2008 import EGModel2008
from calculations import calculate_orthometric_height, dm_to_decimal, dms_to_decimal, calculate_ellipsoidal_height
from utm import utm_to_geodetic
from imports import parse_geodetic_file, parse_utm_file, allowed_file
from dotenv import load_dotenv
from pathlib import Path

import os
import threading
import webview
import time
import sys



MAX_QUANTITY = 10000
MIN_QUANTITY = 1

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

# Cargar el modelo una sola vez al iniciar la aplicación
model = EGModel2008()
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
        return redirect(url_for("main_menu"))

    if request.method == "GET":
        return render_template("login.html")

    elif request.method == "POST":
        password = request.form.get("password")

        if password == ACCESS_PASSWORD:
            session["Logged"] = True
            return redirect(url_for("main_menu"))
        
        else:
            return render_template("login.html", error = "Contraseña Incorrecta")



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

               

                    if calculation_type == "OrthometricHeight":
                                    
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
            return render_template("geodetic.html", quantity = quantity, results = results, error = str(e))

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

        utm_zone = request.form.get("UTMZone")

        if utm_zone not in ["17", "18", "19"]:
            return render_template("utm_zone.html", error="Seleccione una zona válida.")

        session["UTMZone"] = int(utm_zone)

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
                raise ValueError("La cantidad debe estar entre 1 y 1000")
        
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
                            
        
                            if calculation_type == "OrthometricHeight":
                                            
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
                    return render_template("utm.html", quantity = quantity, results = results, error = str(e))
        
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


def run_flask():
    app.run(host="127.0.0.1", port=5000, debug=False, use_reloader=False)
        
if __name__ == "__main__":

    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    time.sleep(2)

    webview.create_window(title="GeoAndina v1.1", url="http://127.0.0.1:5000", width=1280, height=800, resizable=True)

    webview.start()