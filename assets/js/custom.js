// Function to update content based on selected language
function updateContent(langData) {
    document.querySelectorAll('[data-i18n]').forEach(element => {
        const key = element.getAttribute('data-i18n');
        element.textContent = langData[key];
    });
}

// Function to set the language preference
function setLanguagePreference(lang) {
    localStorage.setItem('language', lang);
    location.reload();
}

// Function to fetch language data
async function fetchLanguageData(lang) {
    const response = await fetch(`/athinghedid/languages/${lang}.json`);
    return response.json();
}

// Function to change language
async function changeLanguage(lang) {
    await setLanguagePreference(lang);

    const langData = await fetchLanguageData(lang);
    updateContent(langData);
}

// Call updateContent() on page load
window.addEventListener('DOMContentLoaded', async () => {
    const userPreferredLanguage = localStorage.getItem('language') || 'pt';
    if(userPreferredLanguage == 'en'){
        document.getElementById('langPtOpt').style.display = 'block';
        document.getElementById('langEnOpt').style.display = 'none';
    } else {
        document.getElementById('langPtOpt').style.display = 'none';
        document.getElementById('langEnOpt').style.display = 'block';
    }
    const langData = await fetchLanguageData(userPreferredLanguage);
    updateContent(langData);
});