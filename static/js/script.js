const inputCard = document.querySelectorAll(".coordinate-card");

function updateCard(inputCard)
{
    const geodeticFormat = inputCard.querySelector(".geodetic-format");
    const calculationType = inputCard.querySelector(".calculation-type");

    const ddFields = inputCard.querySelector(".dd-fields");
    const dmFields = inputCard.querySelector(".dm-fields");
    const dmsFields = inputCard.querySelector(".dms-fields");

    const ellipsoidalFields = inputCard.querySelector(".ellipsoidal-fields");
    const orthometricFields = inputCard.querySelector(".orthometric-fields");

    // Formato geodésico (solo existe en geodetic.html)
    if (geodeticFormat)
    {
        if (geodeticFormat.value === "DD")
        {
            ddFields.style.display = "block";
            dmFields.style.display = "none";
            dmsFields.style.display = "none";
        }
        else if (geodeticFormat.value === "DM")
        {
            ddFields.style.display = "none";
            dmFields.style.display = "block";
            dmsFields.style.display = "none";
        }
        else if (geodeticFormat.value === "DMS")
        {
            ddFields.style.display = "none";
            dmFields.style.display = "none";
            dmsFields.style.display = "block";
        }
        else
        {
            throw new Error("Formato geodesico invalido.");
        }
    }

    // Tipo de cálculo (existe tanto en geodetic.html como en utm.html)
    if (calculationType)
    {
        if (calculationType.value === "OrthometricHeight")
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

}


inputCard.forEach(card => {

    const geodeticFormat = card.querySelector(".geodetic-format");
    const calculationType = card.querySelector(".calculation-type");

    updateCard(card);

    if (geodeticFormat)
    {
        geodeticFormat.addEventListener("change", () => updateCard(card));
    }

    if (calculationType)
    {
        calculationType.addEventListener("change", () => updateCard(card));
    }

});