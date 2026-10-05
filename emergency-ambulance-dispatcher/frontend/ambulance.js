const params = new URLSearchParams(window.location.search);
const ambulanceId = params.get("id") || "A01";

document.getElementById("ambulanceName").textContent = ambulanceId;

let currentAssignment = null;
  // =====================================================
// RESPONSE COUNTDOWN TIMER
// =====================================================

const RESPONSE_TIMEOUT_SECONDS = 10;

let responseTimerInterval = null;
let responseTimerAssignmentId = null;


function stopResponseTimer() {

    if (responseTimerInterval) {
        clearInterval(responseTimerInterval);
        responseTimerInterval = null;
    }

    responseTimerAssignmentId = null;

    const timer = document.getElementById(
        "responseCountdown"
    );

    if (timer) {
        timer.remove();
    }
}


function startResponseTimer(assignment) {

    if (!assignment || assignment.status !== "assigned") {
        stopResponseTimer();
        return;
    }

    // Do not restart the interval every time
    // loadAssignment() polls the backend.
    if (
    responseTimerAssignmentId === assignment.id &&
    responseTimerInterval &&
    document.getElementById("responseCountdown")
) {
    return;
}
    stopResponseTimer();

    responseTimerAssignmentId = assignment.id;

    const assignmentBox =
        document.getElementById("assignment");

    if (!assignmentBox) {
        return;
    }

    const timerBox = document.createElement("div");

    timerBox.id = "responseCountdown";

    timerBox.style.marginBottom = "18px";
    timerBox.style.padding = "16px";
    timerBox.style.borderRadius = "12px";
    timerBox.style.textAlign = "center";
    timerBox.style.background = "#fff3cd";
    timerBox.style.border = "1px solid #ffc107";

    assignmentBox.prepend(timerBox);


    // Use backend assignment creation time.
    let createdTime = new Date(
        assignment.created_at
    ).getTime();

    // Fallback only if timestamp cannot be parsed.
    if (Number.isNaN(createdTime)) {
        createdTime = Date.now();
    }

    const deadline =
        createdTime +
        RESPONSE_TIMEOUT_SECONDS * 1000;


    function updateTimer() {

        const remainingMilliseconds =
            deadline - Date.now();

        const remainingSeconds = Math.max(
            0,
            Math.ceil(
                remainingMilliseconds / 1000
            )
        );

        const timer =
            document.getElementById(
                "responseCountdown"
            );

        if (!timer) {
            return;
        }

        timer.innerHTML = `
            <div style="
                font-size:13px;
                font-weight:700;
                margin-bottom:6px;
            ">
                ⚠ RESPONSE REQUIRED
            </div>

            <div style="
                font-size:32px;
                font-weight:800;
            ">
                00:${String(
                    remainingSeconds
                ).padStart(2, "0")}
            </div>

            <div style="
                font-size:13px;
                margin-top:5px;
            ">
                Start Journey before automatic reassignment
            </div>
        `;


        if (remainingSeconds <= 0) {

            clearInterval(
                responseTimerInterval
            );

            responseTimerInterval = null;

            timer.innerHTML = `
                <div style="
                    font-size:14px;
                    font-weight:800;
                ">
                    ⏱ RESPONSE TIME EXPIRED
                </div>

                <div style="
                    margin-top:5px;
                    font-size:13px;
                ">
                    Checking for automatic reassignment...
                </div>
            `;

            // Immediately ask backend for latest assignment.
            setTimeout(
                loadAssignment,
                500
            );
        }
    }


    updateTimer();

    responseTimerInterval = setInterval(
        updateTimer,
        250
    );
 }

/* =====================================================
   LOAD CURRENT ASSIGNMENT
===================================================== */

async function loadAssignment() {

    const box = document.getElementById("assignment");
    const badge = document.getElementById("crewStatusBadge");

    try {

        const response = await fetch(
            `/api/ambulances/${ambulanceId}/assignment`
        );

        if (!response.ok) {
            throw new Error(`Server returned ${response.status}`);
        }

        const data = await response.json();

        currentAssignment = data.assignment;


        /* ---------------------------------------------
           NO ACTIVE ASSIGNMENT
        --------------------------------------------- */

        if (!data.assignment) {
            stopResponseTimer();
            badge.textContent = "AVAILABLE";
            badge.className =
                "crew-status-badge available-badge";

            box.innerHTML = `
                <div class="no-assignment">

                    <div class="waiting-icon">✓</div>

                    <h2>Ready for Assignment</h2>

                    <p>
                        No active emergency is currently
                        assigned to ${escapeHtml(ambulanceId)}.
                    </p>

                    <p class="waiting-text">
                        Waiting for the next emergency...
                    </p>

                </div>
            `;

            updateActionButtons(null);

            return;
        }


        /* ---------------------------------------------
           ACTIVE ASSIGNMENT
        --------------------------------------------- */

        const a = data.assignment;
        const emergency = data.emergency || {};

        badge.textContent = formatStatus(a.status);
        badge.className =
            "crew-status-badge active-badge";


        /* ---------------------------------------------
           PATIENT LIVE LOCATION
        --------------------------------------------- */

let locationSection = "";


/* =====================================================
   NAVIGATION DESTINATION
===================================================== */

/*
    Before patient pickup:
        Navigate to patient's live GPS.

    After patient pickup:
        Navigate to the hospital already selected
        by MediRoute.
*/


if (
    a.status === "with_patient" ||
    a.status === "at_hospital"
) {

    /* ---------------------------------------------
       PATIENT HAS BEEN PICKED UP
       NAVIGATE TO HOSPITAL
    --------------------------------------------- */

    const hospitalName =
        a.hospital_name || "Selected Hospital";

    const hospitalMapsUrl =
        `https://www.google.com/maps/dir/?api=1&destination=${encodeURIComponent(hospitalName)}`;


    if (a.status === "with_patient") {

        locationSection = `
            <div class="patient-location-card">

                <div>

                    <span class="small-label">
                        CURRENT DESTINATION
                    </span>

                    <h3>
                        🏥 ${escapeHtml(hospitalName)}
                    </h3>

                    <p>
                        Patient picked up.
                        Proceed to the selected hospital.
                    </p>

                </div>

                <a
                    class="navigation-button"
                    href="${hospitalMapsUrl}"
                    target="_blank"
                    rel="noopener noreferrer"
                >
                    🧭 Navigate to Hospital
                </a>

            </div>
        `;

    } else {

        locationSection = `
            <div class="patient-location-card">

                <div>

                    <span class="small-label">
                        DESTINATION REACHED
                    </span>

                    <h3>
                        🏥 ${escapeHtml(hospitalName)}
                    </h3>

                    <p>
                        Ambulance has reached
                        the selected hospital.
                    </p>

                </div>

            </div>
        `;
    }

} else if (
    emergency.latitude !== null &&
    emergency.latitude !== undefined &&
    emergency.longitude !== null &&
    emergency.longitude !== undefined
) {

    /* ---------------------------------------------
       BEFORE PICKUP
       NAVIGATE TO PATIENT
    --------------------------------------------- */

    const lat =
        Number(emergency.latitude);

    const lon =
        Number(emergency.longitude);

    const patientMapsUrl =
        `https://www.google.com/maps/dir/?api=1&destination=${lat},${lon}`;


    locationSection = `
        <div class="patient-location-card">

            <div>

                <span class="small-label">
                    PATIENT LIVE LOCATION
                </span>

                <h3>
                    📍 Patient Location Received
                </h3>

                <p>
                    ${lat.toFixed(6)},
                    ${lon.toFixed(6)}
                </p>

            </div>

            <a
                class="navigation-button"
                href="${patientMapsUrl}"
                target="_blank"
                rel="noopener noreferrer"
            >
                🧭 Navigate to Patient
            </a>

        </div>
    `;

} else {

    /* ---------------------------------------------
       WAITING FOR PATIENT GPS
    --------------------------------------------- */

    locationSection = `
        <div class="patient-location-card waiting-location">

            <div>

                <span class="small-label">
                    PATIENT LIVE LOCATION
                </span>

                <h3>
                    ⏳ Waiting for Patient GPS
                </h3>

                <p>
                    Ask the patient to tap
                    Share Location.
                </p>

            </div>

        </div>
    `;
}
        /* ---------------------------------------------
           ASSIGNMENT DISPLAY
        --------------------------------------------- */

        box.innerHTML = `

            <div class="emergency-banner">

                <div>

                    <span class="small-label">
                        ACTIVE EMERGENCY
                    </span>

                    <h2>
                        🚨 ${escapeHtml(
                            emergency.emergency_type ||
                            "Emergency"
                        )}
                    </h2>

                </div>

                <div class="severity-display">

                    Severity

                    <strong>
                        ${emergency.severity || "-"} / 5
                    </strong>

                </div>

            </div>


            <div class="assignment-grid">

                <div class="info-box">

                    <span class="small-label">
                        EMERGENCY ID
                    </span>

                    <strong>
                        ${escapeHtml(a.emergency_id)}
                    </strong>

                </div>


                <div class="info-box">

                    <span class="small-label">
                        AREA
                    </span>

                    <strong>
                        ${escapeHtml(
                            emergency.location ||
                            "Location pending"
                        )}
                    </strong>

                </div>


                <div class="info-box">

                    <span class="small-label">
                        ETA
                    </span>

                    <strong>
                        ⏱ ${a.eta_minutes} min
                    </strong>

                </div>


                <div class="info-box">

                    <span class="small-label">
                        STATUS
                    </span>

                    <strong>
                        ${formatStatus(a.status)}
                    </strong>

                </div>

            </div>


            ${locationSection}


            <div class="route-card">

                <span class="small-label">
                    OPTIMAL ROUTE
                </span>

                <h3>
                    🛣 Route to Patient
                </h3>

                <p>
                    ${escapeHtml(a.route)}
                </p>

                <div class="algorithm-note">
                    Route calculated using A*
                    with current road and traffic data.
                </div>

            </div>


            <div class="hospital-card">

                <span class="small-label">
                    DESTINATION HOSPITAL
                </span>

                <h2>
                    🏥 ${escapeHtml(a.hospital_name)}
                </h2>

            </div>
        `;

        
        /* IMPORTANT:
           Only enable the correct next action.
        */

        updateActionButtons(a.status);

        if (a.status === "assigned") {
            startResponseTimer(a);
         } else {
              stopResponseTimer();
         }

    } catch (error) {

        console.error(error);

        badge.textContent = "CONNECTION ERROR";

        box.innerHTML = `
            <div class="no-assignment">

                <h2>
                    ⚠ Unable to load assignment
                </h2>

                <p>
                    Check the server connection and retry.
                </p>

            </div>
        `;

        updateActionButtons(null);
    }
}


/* =====================================================
   UPDATE AMBULANCE STATUS
===================================================== */

async function setStatus(status) {

    if (!currentAssignment) {
        return;
    }
    if (status === "en_route") {
         stopResponseTimer();
     }
    try {

        const response = await fetch(
            `/api/ambulances/${ambulanceId}/status`,
            {
                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({
                    status: status
                })
            }
        );

        if (!response.ok) {

            const text = await response.text();

            throw new Error(
                `Server returned ${response.status}: ${text}`
            );
        }

        await loadAssignment();

    } catch (error) {

        console.error(error);

        alert(
            "Unable to update ambulance status."
        );
    }
}


/* =====================================================
   COMPLETE CASE
===================================================== */

async function returnDuty() {

    if (!currentAssignment) {
        return;
    }

    const confirmed = confirm(
        "Complete this emergency and return the ambulance to duty?"
    );

    if (!confirmed) {
        return;
    }

    try {

        const response = await fetch(
            `/api/ambulances/${ambulanceId}/return-duty`,
            {
                method: "POST"
            }
        );

        if (!response.ok) {

            const text = await response.text();

            throw new Error(
                `Server returned ${response.status}: ${text}`
            );
        }

        await loadAssignment();

    } catch (error) {

        console.error(error);

        alert(
            "Unable to complete the case."
        );
    }
}


/* =====================================================
   BUTTON WORKFLOW
===================================================== */

function updateActionButtons(status) {

    const startButton =
        document.getElementById("startButton");

    const pickupButton =
        document.getElementById("pickupButton");

    const hospitalButton =
        document.getElementById("hospitalButton");

    const completeButton =
        document.getElementById("completeButton");


    if (
        !startButton ||
        !pickupButton ||
        !hospitalButton ||
        !completeButton
    ) {
        return;
    }


    /* Disable everything first */

    startButton.disabled = true;
    pickupButton.disabled = true;
    hospitalButton.disabled = true;
    completeButton.disabled = true;


    /* Reset labels */

    startButton.innerHTML = `
        <span class="action-icon">🚑</span>
        <span>
            <strong>Start Journey</strong>
            <small>Begin travelling to patient</small>
        </span>
    `;

    pickupButton.innerHTML = `
        <span class="action-icon">👤</span>
        <span>
            <strong>Patient Picked Up</strong>
            <small>Patient is inside ambulance</small>
        </span>
    `;

    hospitalButton.innerHTML = `
        <span class="action-icon">🏥</span>
        <span>
            <strong>Reached Hospital</strong>
            <small>Confirm hospital arrival</small>
        </span>
    `;

    completeButton.innerHTML = `
        <span class="action-icon">✓</span>
        <span>
            <strong>Complete Case</strong>
            <small>Return ambulance to duty</small>
        </span>
    `;


    /* No assignment */

    if (!status) {
        return;
    }


    /* ---------------------------------------------
       ASSIGNED
       Only Start Journey is available
    --------------------------------------------- */

    if (status === "assigned") {

        startButton.disabled = false;

        return;
    }


    /* ---------------------------------------------
       EN ROUTE
       Start completed
       Pickup becomes available
    --------------------------------------------- */

    if (status === "en_route") {

        startButton.innerHTML = `
            <span class="action-icon">✓</span>
            <span>
                <strong>Journey Started</strong>
                <small>Ambulance is en route</small>
            </span>
        `;

        pickupButton.disabled = false;

        return;
    }


    /* ---------------------------------------------
       WITH PATIENT
       Start + pickup completed
       Reached Hospital becomes available
    --------------------------------------------- */

    if (status === "with_patient") {

        startButton.innerHTML = `
            <span class="action-icon">✓</span>
            <span>
                <strong>Journey Started</strong>
                <small>Completed</small>
            </span>
        `;

        pickupButton.innerHTML = `
            <span class="action-icon">✓</span>
            <span>
                <strong>Patient Picked Up</strong>
                <small>Patient is in ambulance</small>
            </span>
        `;

        hospitalButton.disabled = false;

        return;
    }


    /* ---------------------------------------------
       AT HOSPITAL
       First three stages completed
       Complete Case becomes available
    --------------------------------------------- */

    if (status === "at_hospital") {

        startButton.innerHTML = `
            <span class="action-icon">✓</span>
            <span>
                <strong>Journey Started</strong>
                <small>Completed</small>
            </span>
        `;

        pickupButton.innerHTML = `
            <span class="action-icon">✓</span>
            <span>
                <strong>Patient Picked Up</strong>
                <small>Completed</small>
            </span>
        `;

        hospitalButton.innerHTML = `
            <span class="action-icon">✓</span>
            <span>
                <strong>Reached Hospital</strong>
                <small>Hospital arrival confirmed</small>
            </span>
        `;

        completeButton.disabled = false;

        return;
    }
}


/* =====================================================
   FORMAT STATUS
===================================================== */

function formatStatus(status) {

    if (!status) {
        return "UNKNOWN";
    }

    return String(status)
        .replaceAll("_", " ")
        .toUpperCase();
}


/* =====================================================
   HTML SAFETY
===================================================== */

function escapeHtml(value) {

    if (
        value === null ||
        value === undefined
    ) {
        return "";
    }

    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}


/* =====================================================
   START DASHBOARD
===================================================== */

loadAssignment();


setInterval(
    loadAssignment,
    3000
);