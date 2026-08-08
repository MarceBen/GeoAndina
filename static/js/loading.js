const loadingSteps = [

    {
        text: "Inicializando aplicación...",
        progress: 10
    },

    {
        text: "Cargando modelo geoidal EGM2008...",
        progress: 35
    },

    {
        text: "Preparando interpolación bilineal...",
        progress: 60
    },

    {
        text: "Verificando configuración...",
        progress: 85
    },

    {
        text: "Iniciando GeoAndina...",
        progress: 100
    }

];

let currentStep = 0;

const loadingMessage = document.getElementById("loading-message");
const progressBar = document.getElementById("progress-bar");

function updateLoadingScreen()
{
    if (currentStep >= loadingSteps.length)
        return;

    const step = loadingSteps[currentStep];

    loadingMessage.textContent = step.text;
    progressBar.style.width = step.progress + "%";

    currentStep++;
}

updateLoadingScreen();

const interval = setInterval(() => {

    updateLoadingScreen();

}, 1200);


fetch("/initialize")

.then(() => {

    
    clearInterval(interval);

    
    loadingMessage.textContent = "Aplicación lista.";
    progressBar.style.width = "100%";

   
    setTimeout(() => {

        window.location.href = "/login";

    }, 500);

})

.catch(error => {

    clearInterval(interval);

    loadingMessage.textContent = "Error al inicializar GeoAndina.";

    console.error(error);

});