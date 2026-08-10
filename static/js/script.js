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




function createProcessingOverlay()
{
    const overlay = document.createElement("div");
    overlay.className = "processing-overlay";
    overlay.id = "processingOverlay";

    overlay.innerHTML = `
        <div class="processing-spinner"></div>
        <p class="processing-eyebrow">GeoAndina</p>
        <p class="processing-text" id="processingText">Procesando...</p>
    `;

    document.body.appendChild(overlay);

    return overlay;
}

function showProcessingOverlay(message)
{
    let overlay = document.getElementById("processingOverlay");

    if (!overlay)
    {
        overlay = createProcessingOverlay();
    }

    const textEl = document.getElementById("processingText");

    if (textEl && message)
    {
        textEl.textContent = message;
    }

    overlay.classList.add("active");
}

document.addEventListener("DOMContentLoaded", () => {

    document.querySelectorAll("form").forEach(form => {

        form.addEventListener("submit", (event) => {

            const submitter = event.submitter;

            if (!submitter)
            {
                return;
            }

         
            if (submitter.value === "generate")
            {
                return;
            }

            // Botones de navegación, son solo redirects
            if (submitter.value === "main_menu" || submitter.value === "return_utmzone")
            {
                return;
            }

            if (submitter.value === "calculate")
            {
                showProcessingOverlay("Calculando alturas geodésicas...");
            }
            else if (submitter.value === "build")
            {
                showProcessingOverlay("Construyendo modelo geoidal local...");
            }
            else if (form.enctype === "multipart/form-data")
            {
                showProcessingOverlay("Importando y calculando...");
            }

        });

    });

});




const coordinateSystemSelect = document.getElementById("CoordinateSystem");

if (coordinateSystemSelect)
{
    const coordinateOrderField = document.getElementById("coordinateOrderField");

    function updateLocalModelFields()
    {
        if (coordinateSystemSelect.value === "UTM")
        {
            coordinateOrderField.classList.remove("d-none");
        }
        else if (coordinateSystemSelect.value === "Geodetic")
        {
            coordinateOrderField.classList.add("d-none");
        }
    }

    updateLocalModelFields();

    coordinateSystemSelect.addEventListener("change", updateLocalModelFields);
}