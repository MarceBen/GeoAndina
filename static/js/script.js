const coordinateType = document.getElementById("CoordinateType");
const ddFields = document.getElementById("ddFields");
const dmFields = document.getElementById("dmFields");
const dmsFields = document.getElementById("dmsFields");
const utmFields = document.getElementById("utmFields");



function updateCoordinateType()
{
    utmFields.style.display = "none";
    dmsFields.style.display = "none";
    dmFields.style.display = "none";
    ddFields.style.display = "none";

    if(coordinateType.value === "DD")
    {
        ddFields.style.display = "block";
    }

    else if(coordinateType.value === "DM")
    {
        dmFields.style.display = "block";
    }

    else if(coordinateType.value === "DMS")
    {
        dmsFields.style.display = "block";
    }

    else if(coordinateType.value === "UTM")
    {
        utmFields.style.display = "block";
    }

    else
    {
        throw new Error("Tipo de coordenada no reconocido");
    }

}

coordinateType.addEventListener("change", updateCoordinateType);

updateCoordinateType();




