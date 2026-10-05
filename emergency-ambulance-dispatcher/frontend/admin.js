let adminData = {};
let currentTab = "ambulances";


async function loadAdminData() {
    try {
        const response = await fetch("/api/admin/data");

        if (!response.ok) {
            throw new Error(`Server returned ${response.status}`);
        }

        adminData = await response.json();
        showTab(currentTab);

    } catch (error) {
        console.error(error);

        document.getElementById("adminContent").textContent =
            "Unable to load database.";
    }
}


function showTab(tab) {
    currentTab = tab;

    const content =
        document.getElementById("adminContent");

    const records =
        adminData[tab] || [];


    /* ==========================================
       AMBULANCE MANAGEMENT
    ========================================== */

    if (tab === "ambulances") {
        showAmbulances(records);
        return;
    }


    /* ==========================================
       OTHER ADMIN TABLES
    ========================================== */

    if (records.length === 0) {
        content.innerHTML = `
            <h2>${formatTitle(tab)}</h2>
            <p>No records available.</p>
        `;
        return;
    }

    let html =
        `<h2>${formatTitle(tab)}</h2>`;

    html += `<div class="admin-table-wrapper">`;
    html += `<table class="admin-table">`;

    const columns =
        Object.keys(records[0]);

    html += "<thead><tr>";

    columns.forEach(column => {
        html += `<th>${formatTitle(column)}</th>`;
    });

    html += "<th>Action</th>";
    html += "</tr></thead>";
    html += "<tbody>";

    records.forEach((record, index) => {
        html += "<tr>";

        columns.forEach(column => {
            html += `
                <td>
                    <input
                        value="${escapeValue(record[column])}"
                        data-column="${column}"
                        data-index="${index}"
                    >
                </td>
            `;
        });

        html += `
    <td>

        <button
            onclick="saveRecord('${tab}', ${index})"
        >
            Save
        </button>

        ${
            tab === "emergencies" &&
            !["cancelled", "completed"].includes(
                String(record.status || "").toLowerCase()
            )
                ? `
                    <button
                        type="button"
                        onclick="cancelAdminEmergency(
                            '${escapeValue(record.id)}'
                        )"
                        style="
                            margin-left:8px;
                            background:#b42318;
                            color:white;
                        "
                    >
                        Cancel Emergency
                    </button>
                `
                : ""
        }

    </td>
`;
        html += "</tr>";
    });

    html += "</tbody></table></div>";

    content.innerHTML = html;
}


/* =====================================================
   AMBULANCE MANAGEMENT TABLE
===================================================== */
function showAmbulances(records) {

    const content =
        document.getElementById("adminContent");

    let html = `
        <div class="admin-section-header">

            <div>
                <h2>Ambulance Management</h2>
                <p>
                    Add, pause, resume or remove ambulances.
                </p>
            </div>

            <button onclick="showAddAmbulance()">
                + Add Ambulance
            </button>

        </div>


        <div
            id="addAmbulanceForm"
            class="add-ambulance-card"
            style="display:none;"
        >

            <div class="add-ambulance-heading">

                <div class="add-ambulance-icon">
                    🚑
                </div>

                <div>
                    <h3>Add New Ambulance</h3>
                    <p>
                        Register a new ambulance for emergency dispatch.
                    </p>
                </div>

            </div>


            <div class="add-ambulance-fields">

                <div class="admin-field">

                    <label for="newAmbulanceId">
                        Ambulance ID
                    </label>

                    <input
                        id="newAmbulanceId"
                        type="text"
                        placeholder="e.g. A05"
                        autocomplete="off"
                    >

                </div>


                <div class="admin-field">

                    <label for="newAmbulanceLocation">
                        Current Location
                    </label>

                    <input
                        id="newAmbulanceLocation"
                        type="text"
                        placeholder="e.g. Peelamedu"
                        autocomplete="off"
                    >

                </div>

            </div>


            <div class="add-ambulance-status">
                <span></span>
                New ambulance will be added as Available
            </div>


            <div class="add-ambulance-actions">

                <button
                    type="button"
                    class="admin-cancel-button"
                    onclick="hideAddAmbulance()"
                >
                    Cancel
                </button>

                <button
                    type="button"
                    class="admin-add-button"
                    onclick="addAmbulance()"
                >
                    + Add Ambulance
                </button>

            </div>

        </div>
    `;


    if (records.length === 0) {

        html += `
            <p>No ambulances available.</p>
        `;

        content.innerHTML = html;
        return;
    }


    html += `
        <div class="admin-table-wrapper">

            <table class="admin-table">

                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Location</th>
                        <th>Status</th>
                        <th>Service</th>
                        <th>Delete</th>
                    </tr>
                </thead>

                <tbody>
    `;


    records.forEach(record => {

        const id =
            escapeValue(record.id);

        const location =
            escapeValue(record.location);

        const status =
            String(record.status || "available")
                .toLowerCase();


        let serviceButton = "";


        if (status === "available") {

            serviceButton = `
                <button
                    onclick="pauseAmbulance('${id}')"
                >
                    Pause Service
                </button>
            `;

        } else if (status === "paused") {

            serviceButton = `
                <button
                    onclick="resumeAmbulance('${id}')"
                >
                    Resume Service
                </button>
            `;

        } else {

            serviceButton = `
                <button disabled>
                    Active Case
                </button>
            `;
        }


        const deleteDisabled =
            !["available", "paused"].includes(status);


        html += `
            <tr>

                <td>
                    <strong>${id}</strong>
                </td>

                <td>
                    ${location}
                </td>

                <td>
                    <strong>
                        ${formatTitle(status)}
                    </strong>
                </td>

                <td>
                    ${serviceButton}
                </td>

                <td>

                    <button
                        onclick="deleteAmbulance('${id}')"
                        ${deleteDisabled ? "disabled" : ""}
                    >
                        Delete
                    </button>

                </td>

            </tr>
        `;
    });


    html += `
                </tbody>
            </table>
        </div>
    `;


    content.innerHTML = html;
}

/* =====================================================
   SHOW / HIDE ADD FORM
===================================================== */

function showAddAmbulance() {
    const form =
        document.getElementById("addAmbulanceForm");

    if (form) {
        form.style.display = "block";
    }
}


function hideAddAmbulance() {
    const form =
        document.getElementById("addAmbulanceForm");

    if (form) {
        form.style.display = "none";
    }
}

   

/* =====================================================
   PAUSE AMBULANCE
===================================================== */

async function pauseAmbulance(id) {
    const confirmed = confirm(
        `Pause service for ${id}?`
    );

    if (!confirmed) {
        return;
    }

    await changeAmbulanceStatus(
        id,
        "paused"
    );
}


/* =====================================================
   RESUME AMBULANCE
===================================================== */

async function resumeAmbulance(id) {
    await changeAmbulanceStatus(
        id,
        "available"
    );
}


/* =====================================================
   CHANGE AMBULANCE STATUS
===================================================== */

async function changeAmbulanceStatus(
    id,
    status
) {
    try {
        const response =
            await fetch(
                `/api/ambulances/${encodeURIComponent(id)}/status`,
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({
                        status: status
                    })
                }
            );


        if (!response.ok) {
            const message =
                await response.text();

            throw new Error(message);
        }


        await loadAdminData();

    } catch (error) {
        console.error(error);

        alert(
            "Unable to change ambulance status."
        );
    }
}


/* =====================================================
   DELETE AMBULANCE
===================================================== */

async function deleteAmbulance(id) {
    const confirmed = confirm(
        `Delete ambulance ${id}?\n\nThis action cannot be undone.`
    );

    if (!confirmed) {
        return;
    }


    try {
        const response =
            await fetch(
                `/api/admin/ambulances/${encodeURIComponent(id)}`,
                {
                    method: "DELETE"
                }
            );


        if (!response.ok) {
            const message =
                await response.text();

            throw new Error(message);
        }


        alert(`${id} deleted.`);

        await loadAdminData();

    } catch (error) {
        console.error(error);

        alert(
            "Unable to delete ambulance."
        );
    }
}

/* =====================================================
   CANCEL EMERGENCY FROM ADMIN
===================================================== */

async function cancelAdminEmergency(emergencyId) {

    const confirmed = confirm(
        `Cancel emergency ${emergencyId}?\n\n` +
        `The assigned ambulance will be released and returned to service.`
    );

    if (!confirmed) {
        return;
    }


    try {

        const response = await fetch(
            `/api/emergencies/${encodeURIComponent(emergencyId)}/cancel`,
            {
                method: "POST"
            }
        );


        const data = await response.json();


        if (!response.ok) {

            throw new Error(
                data.detail ||
                "Unable to cancel emergency."
            );
        }


        alert(
            `Emergency ${emergencyId} cancelled successfully.`
        );


        // Reload database information
        // and keep the Emergencies tab open.

        currentTab = "emergencies";

        await loadAdminData();


    } catch (error) {

        console.error(
            "Admin emergency cancellation error:",
            error
        );

        alert(
            error.message ||
            "Unable to cancel emergency."
        );
    }
}
/* =====================================================
   ORIGINAL SAVE FUNCTION
===================================================== */

async function saveRecord(tab, index) {
    const record =
        adminData[tab][index];

    const row =
        document.querySelectorAll(
            ".admin-table tbody tr"
        )[index];

    const inputs =
        row.querySelectorAll("input");


    inputs.forEach(input => {
        const column =
            input.dataset.column;

        record[column] =
            convertValue(
                input.value,
                record[column]
            );
    });


    try {
        const response =
            await fetch(
                `/api/admin/${tab}`,
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body:
                        JSON.stringify(record)
                }
            );


        if (!response.ok) {
            const message =
                await response.text();

            throw new Error(message);
        }


        alert("Saved successfully.");

        await loadAdminData();

    } catch (error) {
        console.error(error);

        alert(
            "Unable to save this record."
        );
    }
}


/* =====================================================
   HELPERS
===================================================== */

function convertValue(value, original) {
    if (typeof original === "number") {
        const number =
            Number(value);

        return Number.isNaN(number)
            ? value
            : number;
    }

    return value;
}


function formatTitle(value) {
    return String(value)
        .replaceAll("_", " ")
        .replace(/\b\w/g, letter =>
            letter.toUpperCase()
        );
}


function escapeValue(value) {
    if (
        value === null ||
        value === undefined
    ) {
        return "";
    }

    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;");
}


/* =====================================================
   START ADMIN DASHBOARD
===================================================== */

loadAdminData();
