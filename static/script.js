function logEvent(text) {

    let log = document.getElementById("logList")

    let item = document.createElement("li")

    let time = new Date().toLocaleTimeString()

    item.innerHTML = "[" + time + "] " + text

    log.prepend(item)

}

let lastStatus = "SYSTEM NORMAL"

function updateStatus() {

    fetch("/status")
        .then(res => res.json())
        .then(data => {

            let banner = document.getElementById("alertBanner")

            if (data.status !== lastStatus) {

                banner.innerHTML = data.status

                if (data.status.includes("FIRE")) {

                    banner.style.background = "red"
                    logEvent("Fire detected")

                }

                else if (data.status.includes("COLLAPSE")) {

                    banner.style.background = "orange"
                    logEvent("Collapse detected")

                }

                else {

                    banner.style.background = "#009933"
                    logEvent("System normal")

                }

                lastStatus = data.status
            }

        })
}


// run every 3 seconds
setInterval(updateStatus, 3000)



function getLocationAndSend(type) {

    if (navigator.geolocation) {

        navigator.geolocation.getCurrentPosition(function (position) {

            let lat = position.coords.latitude
            let lon = position.coords.longitude

            fetch(`/${type}?lat=${lat}&lon=${lon}`)

            alert("Location shared with alert system")

            logEvent("Location sent : " + lat + "," + lon)

        })

    }
    else {

        alert("Geolocation not supported")

    }

}



function sendSMS() {

    getLocationAndSend("send_sms")

}



function sendEmail() {

    getLocationAndSend("send_email")

}



function simulateIncident() {

    let banner = document.getElementById("alertBanner")

    banner.innerHTML = "🚨 INCIDENT DETECTED"

    banner.style.background = "red"

    logEvent("Incident simulated")

}



function resetSystem() {

    let banner = document.getElementById("alertBanner")

    banner.innerHTML = "SYSTEM STATUS : NORMAL"

    banner.style.background = "#009933"

    logEvent("System reset")

}