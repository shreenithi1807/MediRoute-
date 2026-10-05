let selectedHospital = "";

let hospitalRefreshInterval = null;


// ======================================================
// LOAD HOSPITALS
// ======================================================

async function loadHospitals() {

    try {

        const response =
            await fetch("/api/hospitals");

        const hospitals =
            await response.json();

        const select =
            document.getElementById(
                "hospitalSelect"
            );

        hospitals.forEach(hospital => {

            const option =
                document.createElement(
                    "option"
                );

            option.value =
                hospital.name;

            option.textContent =
                `${hospital.name} - ${hospital.location}`;

            select.appendChild(option);

        });

    } catch (error) {

        console.error(
            "Unable to load hospitals:",
            error
        );

    }
}


// ======================================================
// SELECT HOSPITAL
// ======================================================

function selectHospital() {

    const select =
        document.getElementById(
            "hospitalSelect"
        );

    selectedHospital =
        select.value;

    if (!selectedHospital) {

        document.getElementById(
            "hospitalContent"
        ).style.display = "none";

        return;
    }


    document.getElementById(
        "hospitalContent"
    ).style.display = "block";


    loadHospital();


    if (hospitalRefreshInterval) {

        clearInterval(
            hospitalRefreshInterval
        );

    }


    hospitalRefreshInterval =
        setInterval(
            loadHospital,
            3000
        );
}


// ======================================================
// LOAD HOSPITAL DATA
// ======================================================

async function loadHospital() {

    if (!selectedHospital) {
        return;
    }


    try {

        const response =
            await fetch(
                `/api/hospital/${
                    encodeURIComponent(
                        selectedHospital
                    )
                }`
            );


        if (!response.ok) {

            throw new Error(
                "Hospital data unavailable"
            );

        }


        const data =
            await response.json();


        renderHospital(
            data.hospital
        );


        renderIncomingCases(
            data.incoming || []
        );


    } catch (error) {

        console.error(
            "Hospital refresh error:",
            error
        );

    }
}


// ======================================================
// RENDER HOSPITAL
// ======================================================

function renderHospital(hospital) {

    document.getElementById(
        "hospitalName"
    ).textContent =
        hospital.name;


    document.getElementById(
        "hospitalLocation"
    ).textContent =
        hospital.location;


    const beds =
        document.getElementById(
            "bedsInput"
        );

    const icu =
        document.getElementById(
            "icuInput"
        );

    const trauma =
        document.getElementById(
            "traumaInput"
        );


    /*
        Do not overwrite a value while
        hospital staff are typing.
    */

    if (
        document.activeElement !== beds
    ) {
        beds.value =
            hospital.beds ?? 0;
    }


    if (
        document.activeElement !== icu
    ) {
        icu.value =
            hospital.icu ?? 0;
    }


    if (
        document.activeElement !== trauma
    ) {
        trauma.value =
            hospital.trauma ?? 0;
    }
}


// ======================================================
// UPDATE CAPACITY
// ======================================================

async function updateCapacity() {

    if (!selectedHospital) {

        alert(
            "Select a hospital first."
        );

        return;
    }


    const beds =
        Number(
            document.getElementById(
                "bedsInput"
            ).value
        );


    const icu =
        Number(
            document.getElementById(
                "icuInput"
            ).value
        );


    const trauma =
        Number(
            document.getElementById(
                "traumaInput"
            ).value
        );


    if (
        beds < 0 ||
        icu < 0 ||
        trauma < 0
    ) {

        alert(
            "Capacity cannot be negative."
        );

        return;
    }


    try {

        const hospitalResponse =
            await fetch(
                `/api/hospital/${
                    encodeURIComponent(
                        selectedHospital
                    )
                }`
            );


        const hospitalData =
            await hospitalResponse.json();


        const hospital =
            hospitalData.hospital;


        const response =
            await fetch(
                `/api/hospital/${
                    encodeURIComponent(
                        selectedHospital
                    )
                }/capacity`,
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body:
                        JSON.stringify({
                            name:
                                selectedHospital,

                            location:
                                hospital.location,

                            beds:
                                beds,

                            icu:
                                icu,

                            trauma:
                                trauma
                        })
                }
            );


        const data =
            await response.json();


        if (!response.ok) {

            throw new Error(
                data.detail ||
                "Update failed"
            );

        }


        alert(
            "Hospital capacity updated successfully."
        );


        await loadHospital();


    } catch (error) {

        console.error(error);

        alert(
            error.message ||
            "Unable to update capacity."
        );

    }
}


// ======================================================
// INCOMING EMERGENCIES
// ======================================================

function renderIncomingCases(cases) {

    const container =
        document.getElementById(
            "incomingCases"
        );


    if (!cases.length) {

        container.innerHTML = `
            <div class="empty">

                ✓ No incoming emergencies.

            </div>
        `;

        return;
    }


    let html = "";


    cases.forEach(item => {

        const severity =
            Number(
                item.severity || 0
            );


        let severityText =
            `${severity}/5`;


        if (severity >= 5) {

            severityText +=
                " • CRITICAL";

        }


        html += `

            <div class="emergency-card">

                <div class="emergency-top">

                    <div>

                        <strong>
                            Emergency
                            ${escapeHtml(
                                item.emergency_id
                            )}
                        </strong>

                    </div>

                    <div class="critical">

                        ${severityText}

                    </div>

                </div>


                <div class="case-grid">


                    <div>

                        <div class="case-label">
                            Emergency Type
                        </div>

                        <div class="case-value">

                            ${escapeHtml(
                                item.emergency_type
                            )}

                        </div>

                    </div>


                    <div>

                        <div class="case-label">
                            Ambulance
                        </div>

                        <div class="case-value">

                            🚑 ${escapeHtml(
                                item.ambulance_id
                            )}

                        </div>

                    </div>


                    <div>

                        <div class="case-label">
                            ETA
                        </div>

                        <div class="case-value">

                            ${escapeHtml(
                                item.eta_minutes
                            )} min

                        </div>

                    </div>


                    <div>

                        <div class="case-label">
                            Patient Location
                        </div>

                        <div class="case-value">

                            ${escapeHtml(
                                item.emergency_location
                            )}

                        </div>

                    </div>


                    <div>

                        <div class="case-label">
                            Required Facility
                        </div>

                        <div class="case-value">

                            ${
                                escapeHtml(
                                    item.required_facility
                                ) ||
                                "General"
                            }

                        </div>

                    </div>


                    <div>

                        <div class="case-label">
                            Ambulance Status
                        </div>

                        <div class="case-value">

                            ${formatStatus(
                                item.assignment_status
                            )}

                        </div>

                    </div>

                </div>

            </div>

        `;

    });


    container.innerHTML =
        html;
}


// ======================================================
// HELPERS
// ======================================================

function formatStatus(value) {

    return String(
        value || "-"
    )
    .replaceAll("_", " ")
    .replace(
        /\b\w/g,
        letter =>
            letter.toUpperCase()
    );
}


function escapeHtml(value) {

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
// START
// ======================================================

loadHospitals();