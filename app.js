BASE_URL = 'https://newsapi.org/v2'


async function displayCountries() {
    promise = await axios.get('/user/home')
}

async function getCountryPrefs(btn) {
    promise = await axios.post("/user/first_prefs");
    promise.then((response) => {
        outletPrefs = document.getElementById("outletPrefs");
        outletPrefs.appendChild(response);
    })
}