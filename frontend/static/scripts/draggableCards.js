const container = document.querySelector(".movableItemsContainer");
const GRID_SIZE = 100;

function createCard() {
    const card = document.createElement("div");
    card.classList.add("draggableCard", "resizable");
    card.style.left = "0px";
    card.style.top = "0px";
    card.style.position = "absolute"; 
    card.draggable = true;
    card.dataset.id = crypto.randomUUID 
        ? crypto.randomUUID() 
        : Date.now().toString() + Math.random().toString(36).substr(2, 9);

    card.addEventListener("dragstart", (e) => {
        e.dataTransfer.setData("text/plain", JSON.stringify({
            offsetX: e.offsetX,
            offsetY: e.offsetY,
            cardId: card.dataset.id
        }));
        card.classList.add("dragging");
    });

    card.addEventListener("dragend", () => {
        card.classList.remove("dragging");
    });

    const contentArea = document.createElement("div");
    contentArea.classList.add("cardContent");
    card.appendChild(contentArea);

    const footer = document.createElement("div");
    footer.classList.add("cardFooter");
    footer.style.position = "relative"; 
    card.appendChild(footer);

    // const deleteBtn = document.createElement("i");
    // deleteBtn.classList.add("fas", "fa-trash", "text-danger", "cursor-pointer");
    // deleteBtn.addEventListener("click", () => deleteCard(card));
    // footer.appendChild(deleteBtn);

    observeResizable(card);

    container.appendChild(card);

    return contentArea;
}

// Use a MutationObserver to watch for when "resizable" is added.
function observeResizable(card) {
    const observer = new MutationObserver((mutations) => {
        mutations.forEach((mutation) => {
            if (mutation.type === "attributes" && mutation.attributeName === "class") {
                if (card.classList.contains("resizable") && !card.dataset.resizableAttached) {
                    makeResizable(card);
                    card.dataset.resizableAttached = "true";
                }
            }
        });
    });
    observer.observe(card, { attributes: true });
    if (card.classList.contains("resizable") && !card.dataset.resizableAttached) {
        makeResizable(card);
        card.dataset.resizableAttached = "true";
    }
}

function makeResizable(card) {
    const footer = card.querySelector(".cardFooter");
    if (!footer) return;
    
    const resizer = document.createElement("div");
    resizer.classList.add("resizer");
    resizer.style.width = "10px";
    resizer.style.height = "10px";
    resizer.style.background = "gray";
    resizer.style.position = "absolute";
    resizer.style.right = "0";
    resizer.style.bottom = "0";
    resizer.style.cursor = "se-resize";
    
    footer.appendChild(resizer);

    resizer.addEventListener("mousedown", (e) => {
        e.preventDefault();
        window.addEventListener("mousemove", resize);
        window.addEventListener("mouseup", stopResize);
    });

    function resize(e) {
        let containerRect = container.getBoundingClientRect();
        // Calculate new width/height relative to the container, snapping to the grid.
        let newWidth = Math.round((e.pageX - card.offsetLeft - containerRect.left) / GRID_SIZE) * GRID_SIZE;
        let newHeight = Math.round((e.pageY - card.offsetTop - containerRect.top) / GRID_SIZE) * GRID_SIZE;
        card.style.width = `${Math.max(GRID_SIZE, newWidth)}px`;
        card.style.height = `${Math.max(GRID_SIZE, newHeight)}px`;
    }

    function stopResize() {
        window.removeEventListener("mousemove", resize);
        window.removeEventListener("mouseup", stopResize);
    }
}

// Save the configuration of all cards (type, position, and size) into localStorage.
function saveCardConfig() {
    const cards = container.querySelectorAll(".draggableCard");
    const config = Array.from(cards).map(card => ({
        type: card.dataset.type,
        left: card.style.left,
        top: card.style.top,
        width: card.style.width,
        height: card.style.height
    }));
    localStorage.setItem("cardConfig", JSON.stringify(config));
}

setInterval(saveCardConfig, 2000);

function loadCardConfig() {
    let configStr = localStorage.getItem("cardConfig");

    if (!configStr || configStr.trim() === "" || configStr === "[]" || configStr === "null") {
        console.log("No autosaved config found, generating new");
        configStr = JSON.stringify([
            {
                "type": "musicControlsCard",
                "left": "0px",
                "top": "600px",
                "width": "1000px",
                "height": "100px"
            },
            {
                "type": "scoreBoardCard",
                "left": "0px",
                "top": "0px",
                "width": "1000px",
                "height": "600px"
            },
            {
                "type": "albumCoverCard",
                "left": "1000px",
                "top": "0px",
                "width": "200px",
                "height": "200px"
            },
            {
                "type": "analogueClockCard",
                "left": "1200px",
                "top": "0px",
                "width": "200px",
                "height": "200px"
            },
            {
                "type": "digitalClockCard",
                "left": "1000px",
                "top": "200px",
                "width": "400px",
                "height": "100px"
            }
        ]);
    }

    let config;
    try {
        config = JSON.parse(configStr);
        if (!Array.isArray(config)) throw new Error("Invalid config format");
    } catch (error) {
        console.error("Failed to parse config:", error);
        return;
    }

    console.log("Loading from autosaved config", config);

    clearAllCards();

    config.forEach(cardConfig => {
        let contentArea;
        switch (cardConfig.type) {
            case "smallCard":
                contentArea = addSmallCard();
                break;
            case "largeCard":
                contentArea = addLargeCard();
                break;
            case "wideCard":
                contentArea = addWideCard();
                break;
            case "scoreBoardCard":
                contentArea = addScoreBoardCard();
                break;
            case "halfScoreBoardCard_red":
                contentArea = createRedTeamScoreCard();
                break;
            case "halfScoreBoardCard_green":
                contentArea = createGreenTeamScoreCard();
                break;
            case "digitalClockCard":
                contentArea = createClockCard();
                break;
            case "musicControlsCard":
                contentArea = createMusicControlsCard();
                break;
            case "albumCoverCard":
                contentArea = createMusicAlbumCard();
                break;
            case "analogueClockCard":
                contentArea = createAnalogueClockCard();
                break;
            default:
                contentArea = addSmallCard();
        }

        if (contentArea) {
            const cardContainer = contentArea.parentElement;
            cardContainer.style.left = cardConfig.left;
            cardContainer.style.top = cardConfig.top;
            if (cardConfig.width) cardContainer.style.width = cardConfig.width;
            if (cardConfig.height) cardContainer.style.height = cardConfig.height;
        }
    });
}

function deleteCard(card) {
    card.remove();
}

container.addEventListener("dragover", (e) => e.preventDefault());

container.addEventListener("drop", (e) => {
    e.preventDefault();
    let data = e.dataTransfer.getData("text/plain");
    if (!data) return;
    let { offsetX, offsetY, cardId } = JSON.parse(data);
    let droppedCard = [...document.querySelectorAll(".draggableCard")].find(c => c.dataset.id === cardId);
    if (!droppedCard) return;
    let containerRect = container.getBoundingClientRect();
    let x = Math.round((e.pageX - containerRect.left - offsetX) / GRID_SIZE) * GRID_SIZE;
    let y = Math.round((e.pageY - containerRect.top - offsetY) / GRID_SIZE) * GRID_SIZE;
    droppedCard.style.left = `${x}px`;
    droppedCard.style.top = `${y}px`;
});

function addSmallCard() {
    const contentArea = createCard();
    const card = contentArea.parentElement;
    contentArea.textContent = "Drag Me";
    card.classList.add("smallCard");
    card.dataset.type = "smallCard";
    return contentArea;
}

function addLargeCard() {
    const contentArea = createCard();
    const card = contentArea.parentElement;
    contentArea.textContent = "Drag Me";
    card.classList.add("largeCard");
    card.dataset.type = "largeCard";
    return contentArea;
}

function addWideCard() {
    const contentArea = createCard();
    const card = contentArea.parentElement;
    contentArea.textContent = "Drag Me";
    card.classList.add("wideCard");
    card.dataset.type = "wideCard";
    return contentArea;
}

function addResizableCard() {
    const contentArea = addSmallCard();
    const card = contentArea.parentElement;
    contentArea.textContent = "Drag and Resize Me";
    return contentArea;
}

function addScoreBoardCard() {
    const contentArea = createCard();
    const card = contentArea.parentElement;
    card.classList.add("scoreBoardCard");
    card.dataset.type = "scoreBoardCard";
    contentArea.innerHTML = `
        <table class="table table-bordered table-hover border-dark h-100" style="font-size: 0.8rem; margin: 0;">
            <thead>
                <tr>
                    <th class="text-center text-white bg-danger">Red Team</th>
                    <th class="text-center text-white bg-success">Green Team</th>
                </tr>
            </thead>
            <tbody id="scoresTable">
                <tr>
                    <td class="text-center text-white bg-dark p-0">
                        <table class="gunScoreTable gunScoreTableHeader" style="width: 100%;">
                            <td>Name</td>
                            <td>Score</td>
                            <td>Accuracy</td>
                        </table>
                    </td>
                    <td class="text-center text-white bg-dark p-0">
                        <table class="gunScoreTable gunScoreTableHeader" style="width: 100%;">
                            <td>Name</td>
                            <td>Score</td>
                            <td>Accuracy</td>
                        </table>
                    </td>
                </tr>
                ${Array.from({ length: 11 }, (_, i) => `
                <tr id="${i + 1}" class="bg-dark">
                    <td class="text-center text-white bg-dark">
                        <table class="gunScoreTable" style="width: 100%;">
                            <td>${['Alpha', 'Apollo', 'Chaos', 'Cipher', 'Cobra', 'Comet', 'Commander', 'Cyborg', 'Cyclone', 'Delta', ''][i]}</td>
                            <td id="gun-${i + 1}-score">0</td>
                            <td id="gun-${i + 1}-accuracy">0%</td>
                        </table>
                    </td>
                    <td class="text-center text-white bg-dark">
                        <table class="gunScoreTable" style="width: 100%;">
                            <td>${['Dodger', 'Dragon', 'Eagle', 'Eliminator', 'Elite', 'Falcon', 'Ghost', 'Gladiator', 'Hawk', 'Hyper', 'Inferno'][i]}</td>
                            <td id="gun-${i + 11}-score">0</td>
                            <td id="gun-${i + 11}-accuracy">0%</td>
                        </table>
                    </td>
                </tr>`).join('')}
            </tbody>
        </table>`;
    return contentArea;
}

function createRedTeamScoreCard() {
    const contentArea = createCard();
    const card = contentArea.parentElement;
    card.classList.add("halfScoreBoardCard");
    card.dataset.type = "halfScoreBoardCard_red";
    contentArea.innerHTML = `
        <table class="table table-bordered table-hover border-dark h-100" style="font-size: 0.8rem; margin: 0;">
            <thead>
                <tr>
                    <th class="text-center text-white bg-danger">Red Team</th>
                </tr>
            </thead>
            <tbody id="scoresTable">
                <tr>
                    <td class="text-center text-white bg-dark p-0">
                        <table class="gunScoreTable gunScoreTableHeader" style="width: 100%;">
                            <td>Name</td>
                            <td>Score</td>
                            <td>Accuracy</td>
                        </table>
                    </td>
                </tr>
                ${Array.from({ length: 11 }, (_, i) => `
                <tr id="${i + 1}" class="bg-dark">
                    <td class="text-center text-white bg-dark">
                        <table class="gunScoreTable" style="width: 100%;">
                            <td>${['Alpha', 'Apollo', 'Chaos', 'Cipher', 'Cobra', 'Comet', 'Commander', 'Cyborg', 'Cyclone', 'Delta', ''][i]}</td>
                            <td id="gun-${i + 1}-score">0</td>
                            <td id="gun-${i + 1}-accuracy">0%</td>
                        </table>
                    </td>
                </tr>`).join('')}
            </tbody>
        </table>`;
    return contentArea;
}

function createGreenTeamScoreCard() {
    const contentArea = createCard();
    const card = contentArea.parentElement;
    card.classList.add("halfScoreBoardCard");
    card.dataset.type = "halfScoreBoardCard_green";
    contentArea.innerHTML = `
        <table class="table table-bordered table-hover border-dark h-100" style="font-size: 0.8rem; margin: 0;">
            <thead>
                <tr>
                    <th class="text-center text-white bg-success">Green Team</th>
                </tr>
            </thead>
            <tbody id="scoresTable">
                <tr>
                    <td class="text-center text-white bg-dark p-0">
                        <table class="gunScoreTable gunScoreTableHeader" style="width: 100%;">
                            <td>Name</td>
                            <td>Score</td>
                            <td>Accuracy</td>
                        </table>
                    </td>
                </tr>
                ${Array.from({ length: 11 }, (_, i) => `
                <tr id="${i + 1}" class="bg-dark">
                    <td class="text-center text-white bg-dark">
                        <table class="gunScoreTable" style="width: 100%;">
                            <td>${['Dodger', 'Dragon', 'Eagle', 'Eliminator', 'Elite', 'Falcon', 'Ghost', 'Gladiator', 'Hawk', 'Hyper', 'Inferno'][i]}</td>
                            <td id="gun-${i + 11}-score">0</td>
                            <td id="gun-${i + 11}-accuracy">0%</td>
                        </table>
                    </td>
                </tr>`).join('')}
            </tbody>
        </table>`;
    return contentArea;
}

function createClockCard() {
    const contentArea = createCard();
    const card = contentArea.parentElement;
    card.classList.add("wideCard", "digitalClockCard");
    card.dataset.type = "digitalClockCard";

    const clock = document.createElement("div");
    clock.classList.add("digitalClock");
    contentArea.appendChild(clock);

    function updateClock() {
        const now = new Date();
        const timeString = now.toLocaleTimeString("en-GB", { hour12: false }) +
            `.${now.getMilliseconds().toString().padStart(3, "0")}`;
        clock.textContent = timeString;
    }
    setInterval(updateClock, 10);
    updateClock();

    return contentArea;
}

function createMusicControlsCard() {
    const contentArea = createCard();
    const card = contentArea.parentElement;
    card.classList.add("smallWideCard");
    card.dataset.type = "musicControlsCard";

    contentArea.innerHTML = `
    <div class="musicControls">
        <i role="button" onclick="restartSong()" class="fa-solid fa-backward" aria-hidden="true"></i>
        <i role="button" id="pauseplayButton" onclick="toggleMusic()" class="fa-regular fa-circle-play" aria-hidden="true"></i>
        <i role="button" onclick="nextSong()" class="fa-solid fa-forward" aria-hidden="true"></i>
        <div style="flex-grow: 1; height: 10px; background-color: #555; border-radius: 10px; overflow: hidden; margin-left: 10px; position: relative; width: 10rem;">
            <div id="progressBar" style="height: 100%; width: 0; background-color: #1db954;"></div>
        </div>
        <span id="timeLeft" style="color: #fff;">0:00</span>
    </div>`;
    return contentArea;
}

function createMusicAlbumCard(){
    const contentArea = createCard();
    const card = contentArea.parentElement;
    card.classList.add("albumCoverCard", "mediumSquareCard");
    card.dataset.type = "albumCoverCard";

    contentArea.innerHTML = `
    <div class="albumContainer" id="album-container">
        <span class="playingSongText" id="musicPlaying"></span>
        <div id="album-cover" style="width: 100%; height: 100%;"></div>
    </div>`;
    return contentArea;
}

function createAnalogueClockCard(){
    const contentArea = createCard();
    const card = contentArea.parentElement;
    card.classList.add("analogueClockCard", "mediumSquareCard");
    card.dataset.type = "analogueClockCard";

    const clockContainer = document.createElement("div");
    clockContainer.classList.add("analogueClock");
    clockContainer.style.position = "relative";
    clockContainer.style.width = "100%";
    clockContainer.style.height = "100%";
    clockContainer.style.border = "2px solid #333";
    clockContainer.style.borderRadius = "50%";
    clockContainer.style.boxSizing = "border-box";
    clockContainer.style.background = "#fff";

    // Create hour markers for each hour.
    for (let i = 0; i < 12; i++) {
        const marker = document.createElement("div");
        marker.classList.add("hourMarker");
        marker.style.position = "absolute";
        marker.style.width = "2px";
        marker.style.height = "26%"; 
        marker.style.background = "#333";
        marker.style.top = "24%";
        marker.style.left = "50%";
        marker.style.transformOrigin = "center bottom";
        marker.style.transform = `rotate(${i * 30}deg) translateY(-90%) translateX(-50%)`;
        clockContainer.appendChild(marker);
    }

    const hourHand = document.createElement("div");
    hourHand.classList.add("hourHand");
    const minuteHand = document.createElement("div");
    minuteHand.classList.add("minuteHand");
    const secondHand = document.createElement("div");
    secondHand.classList.add("secondHand");

    hourHand.style.position = "absolute";
    hourHand.style.width = "4px";
    hourHand.style.height = "30%";
    hourHand.style.background = "#333";
    hourHand.style.top = "20%";
    hourHand.style.left = "50%";
    hourHand.style.transformOrigin = "bottom center";
    hourHand.style.transform = "translateX(-50%)";

    minuteHand.style.position = "absolute";
    minuteHand.style.width = "3px";
    minuteHand.style.height = "40%";
    minuteHand.style.background = "#666";
    minuteHand.style.top = "10%";
    minuteHand.style.left = "50%";
    minuteHand.style.transformOrigin = "bottom center";
    minuteHand.style.transform = "translateX(-50%)";

    secondHand.style.position = "absolute";
    secondHand.style.width = "2px";
    secondHand.style.height = "45%";
    secondHand.style.background = "red";
    secondHand.style.top = "5%";
    secondHand.style.left = "50%";
    secondHand.style.transformOrigin = "bottom center";
    secondHand.style.transform = "translateX(-50%)";

    clockContainer.appendChild(hourHand);
    clockContainer.appendChild(minuteHand);
    clockContainer.appendChild(secondHand);

    contentArea.appendChild(clockContainer);

    function updateClock() {
        const now = new Date();
        const seconds = now.getSeconds();
        const minutes = now.getMinutes();
        const hours = now.getHours();
      
        const secondDeg = seconds * 6; // 360° / 60 = 6° per second.
        const minuteDeg = minutes * 6 + seconds * 0.1; // 6° per minute plus a smooth transition.
        const hourDeg = (hours % 12) * 30 + minutes * 0.5; // 360° / 12 = 30° per hour.
      
        secondHand.style.transform = `translateX(-50%) rotate(${secondDeg}deg)`;
        minuteHand.style.transform = `translateX(-50%) rotate(${minuteDeg}deg)`;
        hourHand.style.transform = `translateX(-50%) rotate(${hourDeg}deg)`;
    }
    updateClock();
    setInterval(updateClock, 1000);

    return contentArea;
}



function clearAllCards(){
    document.querySelectorAll(".movableItemsContainer .draggableCard").forEach(card => card.remove());
}

document.addEventListener("DOMContentLoaded", loadCardConfig)




let currentCard = null;

// Listen for right-click events on the container
container.addEventListener("contextmenu", function(e) {
    // Check if a draggable card (or a child of one) was right-clicked.
    const card = e.target.closest(".draggableCard");
    if (card) {
        e.preventDefault();
        currentCard = card;
        const customMenu = document.getElementById("customContextMenu");
        // Position the custom menu where the user right-clicked.
        customMenu.style.left = e.pageX + "px";
        customMenu.style.top = e.pageY + "px";
        customMenu.style.display = "block";
    }
});

// Hide the custom menu when clicking anywhere else on the page.
document.addEventListener("click", function(e) {
    const customMenu = document.getElementById("customContextMenu");
    customMenu.style.display = "none";
});

// When the "Delete Card" option is clicked, remove the card.
document.getElementById("deleteCardOption").addEventListener("click", function() {
    if (currentCard) {
        deleteCard(currentCard);
        document.getElementById("customContextMenu").style.display = "none";
    }
});