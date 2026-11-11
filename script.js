/* =====================================================
   CAMPUS DIGITAL TWIN
   FRONTEND JAVASCRIPT
===================================================== */


/* =====================================================
   CAMPUS DATA
===================================================== */

const campusData = {

    library: {

        name: "Central Library",

        icon: "📚",

        capacity: 500,

        current: 438,

        occupancy: 87.6,

        status: "High",

        peakTime: "1:00 PM",

        average: "72%",

        description:
            "Main academic library and study area.",

        recommendation:
            "Library is approaching capacity. Additional seating may be useful during peak hours."

    },


    labs: {

        name: "CSE Labs",

        icon: "🧪",

        capacity: 300,

        current: 210,

        occupancy: 70,

        status: "Moderate",

        peakTime: "11:00 AM",

        average: "64%",

        description:
            "Computer science laboratory facilities.",

        recommendation:
            "Lab schedules can be balanced to reduce crowding during practical sessions."

    },


    canteen: {

        name: "Canteen",

        icon: "🍱",

        capacity: 250,

        current: 226,

        occupancy: 90.4,

        status: "Very High",

        peakTime: "1:00–2:00 PM",

        average: "69%",

        description:
            "Main campus food and dining area.",

        recommendation:
            "Consider additional seating and service capacity during lunch hours."

    },


    parking: {

        name: "Parking",

        icon: "🅿️",

        capacity: 300,

        current: 228,

        occupancy: 76,

        status: "Moderate",

        peakTime: "2:00 PM",

        average: "61%",

        description:
            "Main campus vehicle parking area.",

        recommendation:
            "Monitor parking demand during peak campus hours."

    }

};


/* =====================================================
   CROWD DATA
===================================================== */

const crowdData = {

    times: [

        "09:00",
        "10:00",
        "11:00",
        "12:00",
        "13:00",
        "14:00",
        "15:00",
        "16:00",
        "17:00"

    ],


    values: [

        335,
        480,
        625,
        720,
        820,
        840,
        770,
        690,
        575

    ]

};


/* =====================================================
   PAGE INFORMATION
===================================================== */

const pages = {

    home: {

        title: "Campus Overview",

        description:
            "Smart campus activity visualization and analysis"

    },


    campus: {

        title: "Campus Map",

        description:
            "Explore campus buildings and facilities"

    },


    crowd: {

        title: "Crowd Analysis",

        description:
            "Understand campus activity patterns"

    },


    facilities: {

        title: "Facilities",

        description:
            "View current facility utilization"

    },


    analytics: {

        title: "Analytics",

        description:
            "Visualize campus data"

    },


    insights: {

        title: "Insights",

        description:
            "Data-driven campus observations"

    }

};


/* =====================================================
   ELEMENTS
===================================================== */

const menuButton =
    document.getElementById("menuButton");


const closeMenu =
    document.getElementById("closeMenu");


const sideMenu =
    document.getElementById("sideMenu");


const menuOverlay =
    document.getElementById("menuOverlay");


const facilityModal =
    document.getElementById("facilityModal");


const modalClose =
    document.getElementById("modalClose");


const exploreModal =
    document.getElementById("exploreModal");


const exploreClose =
    document.getElementById("exploreClose");


const scanButton =
    document.getElementById("scanButton");


/* =====================================================
   OPEN SIDE MENU
===================================================== */

function openMenu() {

    sideMenu.classList.add("open");

    menuOverlay.classList.add("show");

}


/* =====================================================
   CLOSE SIDE MENU
===================================================== */

function closeSideMenu() {

    sideMenu.classList.remove("open");

    menuOverlay.classList.remove("show");

}


/* =====================================================
   MENU EVENTS
===================================================== */

menuButton.addEventListener(
    "click",
    openMenu
);


closeMenu.addEventListener(
    "click",
    closeSideMenu
);


menuOverlay.addEventListener(
    "click",
    closeSideMenu
);


/* =====================================================
   NAVIGATION BUTTONS
===================================================== */

const navigationButtons =
    document.querySelectorAll(
        "[data-page]"
    );


navigationButtons.forEach(
    button => {

        button.addEventListener(
            "click",
            function () {

                const page =
                    this.dataset.page;


                if (!page) {

                    return;

                }


                showPage(page);


                closeSideMenu();


                closeExploreModal();

            }
        );

    }
);


/* =====================================================
   SHOW PAGE
===================================================== */

function showPage(pageName) {


    /* Find page */

    const page =
        document.getElementById(
            pageName + "Page"
        );


    if (!page) {

        return;

    }


    /* Hide all pages */

    document
        .querySelectorAll(".page")
        .forEach(
            currentPage => {

                currentPage.classList.remove(
                    "active-page"
                );

            }
        );


    /* Show selected page */

    page.classList.add(
        "active-page"
    );


    /* Update menu */

    document
        .querySelectorAll(".menu-item")
        .forEach(
            button => {

                button.classList.remove(
                    "active"
                );


                if (
                    button.dataset.page ===
                    pageName
                ) {

                    button.classList.add(
                        "active"
                    );

                }

            }
        );


    /* Update bottom navigation */

    document
        .querySelectorAll(".bottom-item")
        .forEach(
            button => {

                button.classList.remove(
                    "active"
                );


                if (
                    button.dataset.page ===
                    pageName
                ) {

                    button.classList.add(
                        "active"
                    );

                }

            }
        );


    /* Scroll to top */

    window.scrollTo({

        top: 0,

        behavior: "smooth"

    });

}


/* =====================================================
   FACILITY BUTTONS
===================================================== */

const facilityButtons =
    document.querySelectorAll(
        "[data-location]"
    );


facilityButtons.forEach(
    button => {

        button.addEventListener(
            "click",
            function () {

                const location =
                    this.dataset.location;


                openFacility(location);

            }
        );

    }
);


/* =====================================================
   OPEN FACILITY
===================================================== */

function openFacility(location) {


    const facility =
        campusData[location];


    if (!facility) {

        return;

    }


    const modalBody =
        document.getElementById(
            "modalBody"
        );


    modalBody.innerHTML = `

        <div class="modal-title">

            <div class="modal-title-icon">

                ${facility.icon}

            </div>

            <div>

                <h2>
                    ${facility.name}
                </h2>

                <p>
                    ${facility.description}
                </p>

            </div>

        </div>


        <div class="modal-data-grid">


            <div class="modal-data">

                <small>
                    Capacity
                </small>

                <strong>
                    ${facility.capacity}
                </strong>

            </div>


            <div class="modal-data">

                <small>
                    Current Occupancy
                </small>

                <strong>
                    ${facility.current}
                </strong>

            </div>


            <div class="modal-data">

                <small>
                    Occupancy
                </small>

                <strong>
                    ${facility.occupancy}%
                </strong>

            </div>


            <div class="modal-data">

                <small>
                    Status
                </small>

                <strong>
                    ${facility.status}
                </strong>

            </div>


            <div class="modal-data">

                <small>
                    Peak Time
                </small>

                <strong>
                    ${facility.peakTime}
                </strong>

            </div>


            <div class="modal-data">

                <small>
                    Average
                </small>

                <strong>
                    ${facility.average}
                </strong>

            </div>


        </div>


        <div class="modal-recommendation">

            💡

            <strong>
                Recommendation:
            </strong>

            ${facility.recommendation}

        </div>

    `;


    facilityModal.classList.remove(
        "hidden"
    );

}


/* =====================================================
   CLOSE FACILITY MODAL
===================================================== */

function closeFacilityModal() {

    facilityModal.classList.add(
        "hidden"
    );

}


modalClose.addEventListener(
    "click",
    closeFacilityModal
);


facilityModal.addEventListener(
    "click",
    function (event) {

        if (
            event.target ===
            facilityModal
        ) {

            closeFacilityModal();

        }

    }
);


/* =====================================================
   EXPLORE BUTTON
===================================================== */

scanButton.addEventListener(
    "click",
    function () {

        exploreModal.classList.remove(
            "hidden"
        );

    }
);


/* =====================================================
   CLOSE EXPLORE MODAL
===================================================== */

function closeExploreModal() {

    exploreModal.classList.add(
        "hidden"
    );

}


exploreClose.addEventListener(
    "click",
    closeExploreModal
);


exploreModal.addEventListener(
    "click",
    function (event) {

        if (
            event.target ===
            exploreModal
        ) {

            closeExploreModal();

        }

    }
);


/* =====================================================
   SEARCH
===================================================== */

const searchInput =
    document.getElementById(
        "searchInput"
    );


const searchResults =
    document.getElementById(
        "searchResults"
    );


const clearSearch =
    document.getElementById(
        "clearSearch"
    );


/* Searchable data */

const searchableFacilities = [

    {

        id: "library",

        name: "Central Library",

        type: "Facility",

        icon: "📚"

    },

    {

        id: "labs",

        name: "CSE Labs",

        type: "Laboratory",

        icon: "🧪"

    },

    {

        id: "canteen",

        name: "Canteen",

        type: "Facility",

        icon: "🍱"

    },

    {

        id: "parking",

        name: "Parking",

        type: "Facility",

        icon: "🅿️"

    },

    {

        id: "campus",

        name: "Campus Map",

        type: "Map",

        icon: "🗺️"

    },

    {

        id: "crowd",

        name: "Crowd Analysis",

        type: "Analytics",

        icon: "👥"

    },

    {

        id: "analytics",

        name: "Campus Analytics",

        type: "Analytics",

        icon: "📊"

    },

    {

        id: "insights",

        name: "Campus Insights",

        type: "Information",

        icon: "💡"

    }

];


/* =====================================================
   SEARCH INPUT
===================================================== */

searchInput.addEventListener(
    "input",
    function () {

        const query =
            this.value
                .trim()
                .toLowerCase();


        if (query.length === 0) {

            searchResults.classList.add(
                "hidden"
            );

            clearSearch.classList.add(
                "hidden"
            );

            return;

        }


        clearSearch.classList.remove(
            "hidden"
        );


        const results =
            searchableFacilities.filter(
                item =>
                    item.name
                        .toLowerCase()
                        .includes(query)
            );


        displaySearchResults(
            results
        );

    }
);


/* =====================================================
   DISPLAY SEARCH RESULTS
===================================================== */

function displaySearchResults(
    results
) {


    searchResults.innerHTML = "";


    if (results.length === 0) {

        searchResults.innerHTML = `

            <div class="search-result">

                <div class="search-result-icon">
                    🔍
                </div>

                <div>

                    <strong>
                        No results found
                    </strong>

                    <small>
                        Try another search
                    </small>

                </div>

            </div>

        `;


        searchResults.classList.remove(
            "hidden"
        );

        return;

    }


    results.forEach(
        item => {

            const resultButton =
                document.createElement(
                    "button"
                );


            resultButton.className =
                "search-result";


            resultButton.innerHTML = `

                <div class="search-result-icon">

                    ${item.icon}

                </div>


                <div>

                    <strong>
                        ${item.name}
                    </strong>

                    <small>
                        ${item.type}
                    </small>

                </div>

            `;


            resultButton.addEventListener(
                "click",
                function () {

                    searchResults.classList.add(
                        "hidden"
                    );


                    searchInput.value =
                        item.name;


                    if (
                        campusData[item.id]
                    ) {

                        openFacility(
                            item.id
                        );

                    } else {

                        showPage(
                            item.id
                        );

                    }

                }
            );


            searchResults.appendChild(
                resultButton
            );

        }
    );


    searchResults.classList.remove(
        "hidden"
    );

}


/* =====================================================
   CLEAR SEARCH
===================================================== */

clearSearch.addEventListener(
    "click",
    function () {

        searchInput.value = "";

        searchResults.classList.add(
            "hidden"
        );

        clearSearch.classList.add(
            "hidden"
        );

        searchInput.focus();

    }
);


/* =====================================================
   CLICK OUTSIDE SEARCH
===================================================== */

document.addEventListener(
    "click",
    function (event) {

        const searchSection =
            document.querySelector(
                ".search-section"
            );


        if (
            !searchSection.contains(
                event.target
            )
        ) {

            searchResults.classList.add(
                "hidden"
            );

        }

    }
);


/* =====================================================
   NOTIFICATION BUTTON
===================================================== */

const notificationButton =
    document.getElementById(
        "notificationButton"
    );


notificationButton.addEventListener(
    "click",
    function () {

        showNotificationPanel();

    }
);


/* =====================================================
   NOTIFICATION PANEL
===================================================== */

function showNotificationPanel() {

    const modalBody =
        document.getElementById(
            "modalBody"
        );


    modalBody.innerHTML = `

        <div class="modal-title">

            <div class="modal-title-icon">

                🔔

            </div>

            <div>

                <h2>
                    Campus Alerts
                </h2>

                <p>
                    Current system notifications
                </p>

            </div>

        </div>


        <div class="modal-data-grid">


            <div class="modal-data">

                <small>
                    Canteen
                </small>

                <strong>
                    90.4% High
                </strong>

            </div>


            <div class="modal-data">

                <small>
                    Library
                </small>

                <strong>
                    87.6% High
                </strong>

            </div>


            <div class="modal-data">

                <small>
                    Parking
                </small>

                <strong>
                    72 spaces
                </strong>

            </div>


            <div class="modal-data">

                <small>
                    Peak Period
                </small>

                <strong>
                    1–2 PM
                </strong>

            </div>


        </div>


        <div class="modal-recommendation">

            🔔

            Canteen and library are currently
            the highest-utilization facilities.

        </div>

    `;


    facilityModal.classList.remove(
        "hidden"
    );

}


/* =====================================================
   ESCAPE KEY
===================================================== */

document.addEventListener(
    "keydown",
    function (event) {

        if (
            event.key === "Escape"
        ) {

            closeSideMenu();

            closeFacilityModal();

            closeExploreModal();

        }

    }
);


/* =====================================================
   INITIALIZATION
===================================================== */

function initializeApp() {

    showPage("home");


    console.log(
        "Campus Digital Twin frontend loaded successfully."
    );

}


/* =====================================================
   START APPLICATION
===================================================== */

initializeApp();  