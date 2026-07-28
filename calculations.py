from interpolation import bilinear_interpolation

MAX_LATITUDE = 2
MIN_LATITUDE = -20

MAX_LONGITUDE = -66
MIN_LONGITUDE = -83


def calculate_orthometric_height(model, latitude, longitude, h):
    
    if(latitude < MIN_LATITUDE or latitude > MAX_LATITUDE):
        raise ValueError("La latitud esta fuera de los limites del modelo ")
    
    if(longitude < MIN_LONGITUDE or longitude > MAX_LONGITUDE):
        raise ValueError("La longitud esta fuera de los limites del modelo ")
    
    i, j, i_trunc, j_trunc = model.calculate_indices(latitude, longitude)

    NA, NB, NC, ND = model.get_vertices(i_trunc, j_trunc)

    t, u = model.calculate_tu(latitude, longitude, NA, NB, ND)

    N = bilinear_interpolation(NA, NB, NC, ND, t, u)

    orthometric_height = h - N

    return orthometric_height

def dm_to_decimal(degree, minutes):

    if minutes < 0 or minutes >= 60:
        raise ValueError("Los minutos deben estar entre 0 y 59.9999.")

    if degree < 0:
        decimal = -(abs(degree) + minutes / 60)
    else:
        decimal = degree + minutes / 60

    return decimal

def dms_to_decimal(degree, minutes, seconds):

    if seconds < 0 or seconds >= 60:
        raise ValueError("Los segundos deben estar entre 0 y 59.9999.")

    if minutes < 0 or minutes >= 60:
        raise ValueError("Los minutos deben estar entre 0 y 59.9999.")

    if degree < 0:
        decimal = -(abs(degree) + minutes / 60 + seconds / 3600)
    else:
        decimal = degree + minutes / 60 + seconds / 3600

    return decimal

def calculate_ellipsoidal_height(model, latitude, longitude, h):
    
    if(latitude < MIN_LATITUDE or latitude > MAX_LATITUDE):
        raise ValueError("La latitud esta fuera de los limites del modelo ")
    
    if(longitude < MIN_LONGITUDE or longitude > MAX_LONGITUDE):
        raise ValueError("La longitud esta fuera de los limites del modelo ")
    
    i, j, i_trunc, j_trunc = model.calculate_indices(latitude, longitude)

    NA, NB, NC, ND = model.get_vertices(i_trunc, j_trunc)

    t, u = model.calculate_tu(latitude, longitude, NA, NB, ND)

    N = bilinear_interpolation(NA, NB, NC, ND, t, u)

    ellipsoidal_height = h + N

    return ellipsoidal_height





    










    