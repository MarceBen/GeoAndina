from flask import Flask, render_template, request, redirect, url_for, session
from egm2008 import EGModel2008
from calculations import calculate_orthometric_height, dm_to_decimal, dms_to_decimal, calculate_ellipsoidal_height
from utm import utm_to_geodetic
from dotenv import load_dotenv
import os


MAX_QUANTITY = 50
MIN_QUANTITY = 1

load_dotenv()

ACCESS_PASSWORD = os.getenv("ACCESS_PASSWORD")
SECRET_KEY = os.getenv("SECRET_KEY")

app = Flask(__name__)

app.secret_key = SECRET_KEY

# Cargar el modelo una sola vez al iniciar la aplicación
model = EGModel2008()
model.load_model()

@app.route("/login", methods=["GET", "POST"])
def login():

    if session.get("Logged") == True:
        return redirect(url_for("index"))

    if request.method == "GET":
        return render_template("login.html")

    elif request.method == "POST":
        password = request.form.get("password")

        if password == ACCESS_PASSWORD:
            session["Logged"] = True
            return redirect(url_for("index"))
        
        else:
            return render_template("login.html", error = "Contraseña Incorrecta")



@app.route("/", methods=["GET", "POST"])

def index():

    if session.get("Logged") != True:
        return redirect(url_for("login"))
    

    results = None
    quantity = None

    if request.method == "POST":

        try:
            quantity = int(request.form.get("quantity", 1))
            action = request.form.get("action")

            if quantity > MAX_QUANTITY or quantity < MIN_QUANTITY:
                raise ValueError("La cantidad debe estar entre 1 y 50")


            if action  == "generate":
                return render_template("index.html", quantity=quantity)

            elif action == "calculate":

                results = []
            
                for i in range (quantity):
            
                    coordinate_type = request.form.get(f"CoordinateType_{i}")
                    calculation_type = request.form.get(f"CalculationType_{i}")
                    coordinate_format = request.form.get(f"CoordinateFormat_{i}")
            
                    if coordinate_type == "UTM":
            
                        east = float(request.form.get(f"East_{i}", 0 ))
                        north = float(request.form.get(f"North_{i}", 0 ))
                        utm_zone = int(request.form.get(f"UTMZone_{i}", 18 ))
            
                        if utm_zone < 17 or utm_zone > 19:
                            raise ValueError("La zona UTM debe estar entre 17 y 19")
            
                        latitude, longitude = utm_to_geodetic(east, north, utm_zone)
            
                    elif coordinate_type == "Geodetic":
            
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
            
                            latitude_degree = float(request.form.get(f"LatitudeDegree_{i}", 0 ))
                            latitude_minutes = float(request.form.get(f"LatitudeMinutes_{i}", 0 ))
                            latitude_seconds = float(request.form.get(f"LatitudeSeconds_{i}", 0 ))
            
                            latitude = dms_to_decimal(latitude_degree, latitude_minutes, latitude_seconds)
            
                            longitude_degree = float(request.form.get(f"LongitudeDegree_{i}", 0 ))
                            longitude_minutes = float(request.form.get(f"LongitudeMinutes_{i}", 0 ))
                            longitude_seconds = float(request.form.get(f"LongitudeSeconds_{i}", 0 ))
            
                            longitude = dms_to_decimal(longitude_degree, longitude_minutes, longitude_seconds)
            
                        else:
                            raise ValueError("Formato de coordenada no válido")

                    else:
                        raise ValueError("Tipo de coordenada no válido")

                    if calculation_type == "OrthometricHeight":
                                    
                        ellipsoidal_height = float(request.form.get(f"EllipsoidalHeight_{i}", 0 ))
                                    
                        orthometric_height = calculate_orthometric_height(model, latitude, longitude, ellipsoidal_height)
                                    
                    elif calculation_type == "EllipsoidalHeight":
                                    
                        orthometric_height = float(request.form.get(f"OrthometricHeight_{i}", 0 ))
                                        
                        ellipsoidal_height = calculate_ellipsoidal_height(model, latitude, longitude, orthometric_height)
                                    
                    else:
                        raise ValueError("Tipo de cálculo no válido")

                    results.append ({
                        "CalculationType": calculation_type,
                        "latitude": latitude,
                        "longitude": longitude,
                        "orthometric_height": orthometric_height,
                        "ellipsoidal_height": ellipsoidal_height
                        })
                                    
                return render_template("index.html", quantity = quantity, results=results) 
            
            else:
                raise ValueError("Accion Invalida")   

        except ValueError as e:
            return render_template("index.html", quantity = quantity, results = results,error=str(e))

    return render_template("index.html", quantity = quantity, results = results)


if __name__ == "__main__":
    app.run(debug=True)