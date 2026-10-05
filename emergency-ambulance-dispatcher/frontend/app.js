// ======================================================
// MEDIROUTE AI
// PATIENT CHAT + TWO-WAY LIVE LOCATION TRACKING
// ======================================================


// ======================================================
// GLOBAL VARIABLES
// ======================================================

let locationWatchId = null;
let currentEmergencyId = null;

let latestLatitude = null;
let latestLongitude = null;

let trackingIntervalId = null;
// ======================================================
// PATIENT LIVE AMBULANCE MAP
// ======================================================

let patientMap = null;
let ambulanceMapMarker = null;
let patientMapMarker = null;
let trackingRouteLine = null;

// ======================================================
// SEND CHAT
// ======================================================

async function sendChat() {

    const input =
        document.getElementById("chatInput");

    const messages =
        document.getElementById("chatMessages");

    if (!input || !messages) {
        return;
    }

    const message =
        input.value.trim();

    if (!message) {
        return;
    }


    // ==================================================
    // SHOW USER MESSAGE
    // ==================================================

    const userBox =
        document.createElement("div");

    userBox.className =
        "user-message";


    const userText =
        document.createElement("p");

    userText.textContent =
        message;


    userBox.appendChild(
        userText
    );

    messages.appendChild(
        userBox
    );


    input.value = "";

    scrollChat();


    // ==================================================
    // SHOW AI LOADING MESSAGE
    // ==================================================

    const aiBox =
        document.createElement("div");

    aiBox.className =
        "ai-message";


    const aiTitle =
        document.createElement("strong");

    aiTitle.textContent =
        "MediRoute AI";


    const aiText =
        document.createElement("p");

    aiText.textContent =
        "Analyzing emergency...";


    aiBox.appendChild(
        aiTitle
    );

    aiBox.appendChild(
        aiText
    );

    messages.appendChild(
        aiBox
    );


    scrollChat();


    // ==================================================
    // SEND MESSAGE TO FASTAPI
    // ==================================================

    try {

        const response =
            await fetch(
                "/api/chat",
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({
                        message: message
                    })
                }
            );


        if (!response.ok) {

            throw new Error(
                `Server returned ${response.status}`
            );
        }


        const data =
            await response.json();


        console.log(
            "MediRoute response:",
            data
        );


        // ==================================================
        // FIND THE CORRECT EMERGENCY ID
        // ==================================================

        if (
            data.result &&
            data.result.emergency &&
            data.result.emergency.id
        ) {

            currentEmergencyId =
                data.result.emergency.id;
        }

        else if (
            data.emergency &&
            data.emergency.id
        ) {

            currentEmergencyId =
                data.emergency.id;
        }

        else if (
            data.created_emergency &&
            data.created_emergency.id
        ) {

            currentEmergencyId =
                data.created_emergency.id;
        }


        console.log(
            "Current emergency:",
            currentEmergencyId
        );

         // ==================================================
// ENABLE CANCEL BUTTON FOR NEW EMERGENCY
// ==================================================

if (currentEmergencyId) {

    const cancelButton =
        document.getElementById("cancelEmergencyButton");

    if (cancelButton) {
        cancelButton.disabled = false;
        cancelButton.textContent =
            "✕ Cancel Emergency";
    }
}
        // ==================================================
        // SEND SAVED PATIENT GPS
        // ==================================================

        if (
            currentEmergencyId &&
            latestLatitude !== null &&
            latestLongitude !== null
        ) {

            await sendLocationToBackend();
        }


        // ==================================================
        // START TRACKING AMBULANCE
        // ==================================================

        if (currentEmergencyId) {

            startAmbulanceTracking();
        }


        // ==================================================
        // DISPLAY AI RESPONSE
        // ==================================================

        aiText.textContent =
            data.reply ||
            "Command completed successfully.";


        if (
            data.action === "dispatch"
        ) {

            aiTitle.textContent =
                "✓ MediRoute Dispatch";
        }


        else if (
            data.action ===
            "emergency_created"
        ) {

            aiTitle.textContent =
                "✓ Emergency Registered";
        }


        else if (
            data.action ===
            "dispatch_failed"
        ) {

            aiTitle.textContent =
                "⚠ Dispatch Status";
        }


        else {

            aiTitle.textContent =
                "MediRoute AI";
        }


    } catch (error) {

        console.error(
            "Chat error:",
            error
        );


        aiTitle.textContent =
            "⚠ MediRoute AI";


        aiText.textContent =
            "Unable to process the request. Please check the backend.";
    }


    scrollChat();
}


// ======================================================
// QUICK PROMPT BUTTONS
// ======================================================

function quickPrompt(text) {

    const input =
        document.getElementById(
            "chatInput"
        );


    if (!input) {
        return;
    }


    input.value =
        text;


    // This automatically sends the selected emergency.
    sendChat();
}


// ======================================================
// PATIENT SHARE LOCATION
// ======================================================

function shareLocation() {

    const status =
        document.getElementById(
            "locationStatus"
        );


    const button =
        document.getElementById(
            "locationButton"
        );


    if (!navigator.geolocation) {

        if (status) {

            status.textContent =
                "⚠ Location is not supported by this browser.";
        }

        return;
    }


    if (status) {

        status.textContent =
            "● Requesting location permission...";
    }


    if (button) {

        button.textContent =
            "Locating...";
    }


    // Prevent duplicate GPS watchers.

    if (
        locationWatchId !== null
    ) {

        navigator.geolocation.clearWatch(
            locationWatchId
        );

        locationWatchId = null;
    }


    locationWatchId =
        navigator.geolocation.watchPosition(

            async (position) => {

                latestLatitude =
                    position.coords.latitude;

                latestLongitude =
                    position.coords.longitude;


                console.log(
                    "Patient GPS:",
                    latestLatitude,
                    latestLongitude
                );


                if (button) {

                    button.textContent =
                        "✓ Location Shared";
                }


                // Emergency already exists.
                // Send location immediately.

                if (currentEmergencyId) {

                    if (status) {

                        status.textContent =
                            "● Sending location to ambulance...";
                    }


                    await sendLocationToBackend();

                }

                else {

                    // Location is remembered until
                    // emergency is created.

                    if (status) {

                        status.textContent =
                            "● Location ready — send your emergency";
                    }
                }
            },


            (error) => {

                console.error(
                    "Patient GPS error:",
                    error
                );


                if (button) {

                    button.textContent =
                        "📍 Share Location";
                }


                if (!status) {
                    return;
                }


                if (error.code === 1) {

                    status.textContent =
                        "⚠ Location permission denied. Allow Location in browser settings.";
                }

                else if (error.code === 2) {

                    status.textContent =
                        "⚠ Current location unavailable.";
                }

                else if (error.code === 3) {

                    status.textContent =
                        "⚠ Location request timed out. Try again.";
                }

                else {

                    status.textContent =
                        "⚠ Unable to get your location.";
                }
            },


            {
                enableHighAccuracy: true,
                maximumAge: 3000,
                timeout: 15000
            }
        );
}


// ======================================================
// SEND PATIENT LOCATION TO BACKEND
// ======================================================

async function sendLocationToBackend() {

    if (
        !currentEmergencyId ||
        latestLatitude === null ||
        latestLongitude === null
    ) {

        return;
    }


    const status =
        document.getElementById(
            "locationStatus"
        );


    try {

        const response =
            await fetch(
                `/api/emergencies/${currentEmergencyId}/location`,
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({

                        latitude:
                            latestLatitude,

                        longitude:
                            latestLongitude
                    })
                }
            );


        if (!response.ok) {

            throw new Error(
                `Location server returned ${response.status}`
            );
        }


        const data =
            await response.json();


        console.log(
            "Patient location saved:",
            data
        );


        if (status) {

            status.textContent =
                "● Live location shared with ambulance";
        }


    } catch (error) {

        console.error(
            "Patient location update failed:",
            error
        );


        if (status) {

            status.textContent =
                "⚠ GPS found but could not send location";
        }
    }
}


// ======================================================
// STOP PATIENT LOCATION SHARING
// ======================================================

function stopLocationSharing() {

    if (
        locationWatchId !== null
    ) {

        navigator.geolocation.clearWatch(
            locationWatchId
        );


        locationWatchId =
            null;
    }


    const status =
        document.getElementById(
            "locationStatus"
        );


    const button =
        document.getElementById(
            "locationButton"
        );


    if (status) {

        status.textContent =
            "Location sharing stopped";
    }


    if (button) {

        button.textContent =
            "📍 Share Location";
    }
}


// ======================================================
// START PATIENT -> AMBULANCE TRACKING
// ======================================================

function startAmbulanceTracking() {

    // Stop previous timer if one exists.

    if (
        trackingIntervalId !== null
    ) {

        clearInterval(
            trackingIntervalId
        );
    }


    // Run immediately.

    updateAmbulanceTracking();


    // Then refresh every 3 seconds.

    trackingIntervalId =
        setInterval(
            updateAmbulanceTracking,
            3000
        );
}


// ======================================================
// GET AMBULANCE LOCATION
// ======================================================

async function updateAmbulanceTracking() {

    if (!currentEmergencyId) {
        return;
    }


    try {

        const response =
            await fetch(
                `/api/emergencies/${currentEmergencyId}/tracking`
            );


        if (!response.ok) {

            console.error(
                "Tracking server returned:",
                response.status
            );

            return;
        }


        const data =
            await response.json();


        console.log(
            "Tracking data:",
            data
        );


        // Emergency exists but no ambulance
        // has been assigned yet.

        if (
            !data.assignment ||
            !data.ambulance
        ) {

            showWaitingForAmbulance();

            return;
        }


        showAmbulanceTracking(
            data
        );


    } catch (error) {

        console.error(
            "Ambulance tracking error:",
            error
        );
    }
}


// ======================================================
// WAITING FOR AMBULANCE UI
// ======================================================

function showWaitingForAmbulance() {

    const panel =
        getTrackingPanel();


    panel.innerHTML = `

        <div class="tracking-heading">

            <div>

                <span class="small-label">
                    AMBULANCE TRACKING
                </span>

                <h2>
                    🚑 Waiting for ambulance assignment
                </h2>

            </div>

        </div>

        <p>
            Your emergency has been registered.
            MediRoute is checking available ambulances.
        </p>
    `;
}


// ======================================================
// SHOW LIVE AMBULANCE TRACKING
// ======================================================

function showAmbulanceTracking(data) {

    const panel =
        getTrackingPanel();


    const ambulance =
        data.ambulance;


    const assignment =
        data.assignment;


    const emergency =
        data.emergency;


    let distanceText =
        "Waiting for ambulance GPS";


    let liveEta =
        assignment.eta_minutes;


    let navigationText =
        "Ambulance location pending";


    // ==================================================
    // BOTH PATIENT + AMBULANCE HAVE GPS
    // ==================================================

    if (
        ambulance.latitude !== null &&
        ambulance.latitude !== undefined &&
        ambulance.longitude !== null &&
        ambulance.longitude !== undefined &&
        emergency.latitude !== null &&
        emergency.latitude !== undefined &&
        emergency.longitude !== null &&
        emergency.longitude !== undefined
    ) {

        const ambulanceLat =
            Number(
                ambulance.latitude
            );


        const ambulanceLon =
            Number(
                ambulance.longitude
            );


        const patientLat =
            Number(
                emergency.latitude
            );


        const patientLon =
            Number(
                emergency.longitude
            );


        const distance =
            calculateDistanceKm(
                ambulanceLat,
                ambulanceLon,
                patientLat,
                patientLon
            );


        distanceText =
            `${distance.toFixed(2)} km away`;


        // Demo live ETA based on approximately
        // 30 km/h urban ambulance movement.

        const assumedSpeedKmH =
            30;


        liveEta =
            Math.max(
                1,
                Math.ceil(
                    (
                        distance /
                        assumedSpeedKmH
                    ) * 60
                )
            );


        navigationText =
            `${ambulanceLat.toFixed(5)}, ${ambulanceLon.toFixed(5)}`;
    }


    panel.innerHTML = `

        <div class="tracking-heading">

            <div>

                <span class="small-label">
                    AMBULANCE TRACKING
                </span>

                <h2>
                    🚑 ${escapeTracking(
                        ambulance.id
                    )} is responding
                </h2>

            </div>


            <div class="tracking-live">
                ● LIVE
            </div>

                    </div>


            <!-- LIVE AMBULANCE MAP -->

            <div
                id="patientAmbulanceMap"
                style="
                    width: 100%;
                    height: 360px;
                    margin: 18px 0;
                    border-radius: 16px;
                    overflow: hidden;
                    border: 1px solid #d8e2df;
                "
            ></div>


            <div class="tracking-grid">

            <div>

                <span>
                    DISTANCE REMAINING
                </span>

                <strong>
                    ${distanceText}
                </strong>

            </div>


            <div>

                <span>
                    ESTIMATED ARRIVAL
                </span>

                <strong>
                    ${liveEta} min
                </strong>

            </div>


            <div>

                <span>
                    AMBULANCE STATUS
                </span>

                <strong>
                    ${formatTrackingStatus(
                        ambulance.status
                    )}
                </strong>

            </div>


            <div>

                <span>
                    AMBULANCE
                </span>

                <strong>
                    ${escapeTracking(
                        ambulance.id
                    )}
                </strong>

            </div>


            <div>

                <span>
                    DESTINATION HOSPITAL
                </span>

                <strong>
                    ${escapeTracking(
                        assignment.hospital_name
                    )}
                </strong>

            </div>


            <div>

                <span>
                    AMBULANCE GPS
                </span>

                <strong>
                    ${navigationText}
                </strong>

            </div>


        </div>
    `;
    // ==================================================
// UPDATE LIVE MAP
// ==================================================

if (
    ambulance.latitude !== null &&
    ambulance.latitude !== undefined &&
    ambulance.longitude !== null &&
    ambulance.longitude !== undefined &&
    emergency.latitude !== null &&
    emergency.latitude !== undefined &&
    emergency.longitude !== null &&
    emergency.longitude !== undefined
) {

    updatePatientAmbulanceMap(
        Number(ambulance.latitude),
        Number(ambulance.longitude),
        Number(emergency.latitude),
        Number(emergency.longitude)
    );
}
}

// ======================================================
// PATIENT LIVE AMBULANCE MAP
// ======================================================

function updatePatientAmbulanceMap(
    ambulanceLat,
    ambulanceLon,
    patientLat,
    patientLon
) {

    const mapElement =
        document.getElementById("patientAmbulanceMap");

    if (!mapElement) {
        return;
    }

    if (typeof L === "undefined") {
        console.error("Leaflet map library not loaded.");
        return;
    }


    // Remove previous map before drawing the new GPS position.
    if (patientMap) {

        patientMap.remove();

        patientMap = null;
        ambulanceMapMarker = null;
        patientMapMarker = null;
        trackingRouteLine = null;
    }


    // CREATE MAP
    patientMap = L.map("patientAmbulanceMap");


    // OPENSTREETMAP
    L.tileLayer(
        "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
        {
            maxZoom: 19,
            attribution: "&copy; OpenStreetMap contributors"
        }
    ).addTo(patientMap);


    // ==================================================
    // PATIENT MARKER
    // ==================================================

    const patientIcon = L.divIcon({

        className: "",

        html: `
            <div style="font-size:32px;">
                📍
            </div>
        `,

        iconSize: [40, 40],
        iconAnchor: [20, 36]
    });


    patientMapMarker = L.marker(
        [patientLat, patientLon],
        {
            icon: patientIcon
        }
    )
    .addTo(patientMap)
    .bindPopup("<strong>Your Location</strong>");


    // ==================================================
    // AMBULANCE MARKER
    // ==================================================

    const ambulanceIcon = L.divIcon({

        className: "",

        html: `
            <div style="font-size:34px;">
                🚑
            </div>
        `,

        iconSize: [44, 44],
        iconAnchor: [22, 22]
    });


    ambulanceMapMarker = L.marker(
        [ambulanceLat, ambulanceLon],
        {
            icon: ambulanceIcon
        }
    )
    .addTo(patientMap)
    .bindPopup("<strong>Assigned Ambulance</strong>");


    // ==================================================
    // CONNECT AMBULANCE → PATIENT
    // ==================================================

    trackingRouteLine = L.polyline(
        [
            [ambulanceLat, ambulanceLon],
            [patientLat, patientLon]
        ],
        {
            weight: 5,
            opacity: 0.8,
            dashArray: "10, 8"
        }
    ).addTo(patientMap);


    // ==================================================
    // SHOW BOTH LOCATIONS
    // ==================================================

    const bounds = L.latLngBounds(
        [
            [ambulanceLat, ambulanceLon],
            [patientLat, patientLon]
        ]
    );


    patientMap.fitBounds(
        bounds,
        {
            padding: [50, 50],
            maxZoom: 16
        }
    );


    // Fix Leaflet sizing after dynamic insertion.
    setTimeout(
        () => {

            if (patientMap) {
                patientMap.invalidateSize();
            }

        },
        100
    );
}

// ======================================================
// GET / CREATE TRACKING PANEL
// ======================================================

function getTrackingPanel() {

    let panel =
        document.getElementById(
            "ambulanceTrackingPanel"
        );


    if (panel) {

        return panel;
    }


    panel =
        document.createElement(
            "div"
        );


    panel.id =
        "ambulanceTrackingPanel";


    panel.className =
        "ambulance-tracking-panel";


    const locationPanel =
        document.querySelector(
            ".emergency-location-panel"
        );


    if (locationPanel) {

        locationPanel.insertAdjacentElement(
            "afterend",
            panel
        );

    }

    else {

        const container =
            document.querySelector(
                ".chat-container"
            );


        if (container) {

            container.appendChild(
                panel
            );
        }
    }


    return panel;
}


// ======================================================
// GPS DISTANCE CALCULATION
// HAVERSINE FORMULA
// ======================================================

function calculateDistanceKm(
    lat1,
    lon1,
    lat2,
    lon2
) {

    const earthRadiusKm =
        6371;


    const dLat =
        degreesToRadians(
            lat2 - lat1
        );


    const dLon =
        degreesToRadians(
            lon2 - lon1
        );


    const a =
        Math.sin(
            dLat / 2
        ) *
        Math.sin(
            dLat / 2
        ) +

        Math.cos(
            degreesToRadians(lat1)
        ) *

        Math.cos(
            degreesToRadians(lat2)
        ) *

        Math.sin(
            dLon / 2
        ) *

        Math.sin(
            dLon / 2
        );


    const c =
        2 *
        Math.atan2(
            Math.sqrt(a),
            Math.sqrt(1 - a)
        );


    return (
        earthRadiusKm * c
    );
}


// ======================================================
// DEGREES -> RADIANS
// ======================================================

function degreesToRadians(
    value
) {

    return (
        value *
        Math.PI /
        180
    );
}


// ======================================================
// FORMAT AMBULANCE STATUS
// ======================================================

function formatTrackingStatus(
    status
) {

    if (!status) {

        return "Assigned";
    }


    return status

        .replaceAll(
            "_",
            " "
        )

        .replace(
            /\b\w/g,
            letter =>
                letter.toUpperCase()
        );
}


// ======================================================
// SAFE HTML
// ======================================================

function escapeTracking(
    value
) {

    if (
        value === null ||
        value === undefined
    ) {

        return "";
    }


    return String(value)

        .replaceAll(
            "&",
            "&amp;"
        )

        .replaceAll(
            "<",
            "&lt;"
        )

        .replaceAll(
            ">",
            "&gt;"
        )

        .replaceAll(
            '"',
            "&quot;"
        )

        .replaceAll(
            "'",
            "&#039;"
        );
}


// ======================================================
// SCROLL CHAT
// ======================================================

function scrollChat() {

    const messages =
        document.getElementById(
            "chatMessages"
        );


    if (messages) {

        messages.scrollTop =
            messages.scrollHeight;
    }
}


// ======================================================
// PAGE READY
// ======================================================

document.addEventListener(
    "DOMContentLoaded",
    () => {

        const input =
            document.getElementById(
                "chatInput"
            );


        if (input) {

            // ==========================================
            // ENTER KEY SENDS MESSAGE
            // ==========================================

            input.addEventListener(
                "keydown",
                event => {

                    if (
                        event.key === "Enter"
                    ) {

                        event.preventDefault();


                        // THIS IS THE sendChat()
                        // YOU WERE ASKING ABOUT.
                        sendChat();
                    }
                }
            );


            input.focus();
        }
    }
);
async function cancelEmergency() {

    if (!currentEmergencyId) {
        alert("No active emergency to cancel.");
        return;
    }

    const confirmed = confirm(
        "Are you sure you want to cancel this emergency request?"
    );

    if (!confirmed) {
        return;
    }

    try {

        const response = await fetch(
            `/api/emergencies/${currentEmergencyId}/cancel`,
            {
                method: "POST"
            }
        );

        const data = await response.json();

        if (!response.ok) {
            alert(
                data.detail ||
                "Unable to cancel emergency."
            );
            return;
        }

        alert("Emergency cancelled successfully.");

        currentEmergencyId = null;

        const cancelButton =
            document.getElementById("cancelEmergencyButton");

        if (cancelButton) {
            cancelButton.disabled = true;
            cancelButton.textContent =
                "Emergency Cancelled";
        }

    } catch (error) {

        console.error(error);

        alert(
            "Could not connect to the server."
        );
    }
}