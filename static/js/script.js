const inputCard = document.querySelectorAll(".coordinate-card");

function updateCard(inputCard)
{
    const coordinateType = inputCard.querySelector(".coordinate-type");
    const geodeticFormat = inputCard.querySelector(".geodetic-format");
    const calculationType = inputCard.querySelector(".calculation-type");
    const utmFields = inputCard.querySelector(".utm-fields");

    const ddFields = inputCard.querySelector(".dd-fields");
    const dmFields = inputCard.querySelector(".dm-fields");
    const dmsFields = inputCard.querySelector(".dms-fields");

    const utmZoneFields = inputCard.querySelector(".utmzone-fields");
    const geodeticFormatCmbox = inputCard.querySelector(".geodeticformat-fields");


    const ellipsoidalFields = inputCard.querySelector(".ellipsoidal-fields");
    const orthometricFields = inputCard.querySelector(".orthometric-fields");



    if(coordinateType.value === "Geodetic")
    {
        if(geodeticFormat.value === "DD" )
        {
            ddFields.style.display = "block";
            dmFields.style.display = "none";
            dmsFields.style.display = "none";
            utmFields.style.display = "none";
            utmZoneFields.style.display = "none";
            geodeticFormatCmbox.style.display = "block";
        }
        else if (geodeticFormat.value === "DM")
        {
            ddFields.style.display = "none";
            dmFields.style.display = "block";
            dmsFields.style.display = "none";
            utmFields.style.display = "none";
            utmZoneFields.style.display = "none";
            geodeticFormatCmbox.style.display = "block";
        }
        else if (geodeticFormat.value === "DMS")
        {
            ddFields.style.display = "none";
            dmFields.style.display = "none";
            dmsFields.style.display = "block";
            utmFields.style.display = "none";
            utmZoneFields.style.display = "none";
            geodeticFormatCmbox.style.display = "block";

        }
        else
        {
            throw new Error("Formato geodesico invalido.");
        }
    }
    else if (coordinateType.value === "UTM")
    {
        utmFields.style.display = "block";
        geodeticFormatCmbox.style.display = "none";
        ddFields.style.display = "none";
        dmFields.style.display = "none";
        dmsFields.style.display = "none";
        utmZoneFields.style.display = "block";
    }
    else
    {
        throw new Error("Tipo de coordenada invalido.");
    }

    if(calculationType.value === "OrthometricHeight")
    {
        orthometricFields.style.display = "none";
        ellipsoidalFields.style.display = "block";
    }
    else if (calculationType.value === "EllipsoidalHeight")
    {
        orthometricFields.style.display = "block";
        ellipsoidalFields.style.display = "none";
    }
    else
    {
        throw new Error("Tipo de cálculo invalido.");
    }

    
        
    

}


inputCard.forEach(card => {

    const coordinateType = card.querySelector(".coordinate-type");
    const geodeticFormat = card.querySelector(".geodetic-format");
    const calculationType = card.querySelector(".calculation-type");
    const utmZoneFields = card.querySelector(".utmzone-fields");
    const geodeticFormatCmbox = card.querySelector(".geodeticformat-fields");
    

    updateCard(card);

    coordinateType.addEventListener("change", () => updateCard(card));
    geodeticFormat.addEventListener("change", () => updateCard(card));
    calculationType.addEventListener("change", () => updateCard(card));



});

