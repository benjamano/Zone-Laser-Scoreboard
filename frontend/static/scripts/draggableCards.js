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

    const deleteBtn = document.createElement("i");
    deleteBtn.classList.add("fas", "fa-trash", "text-danger", "cursor-pointer");
    deleteBtn.addEventListener("click", () => deleteCard(card));
    footer.appendChild(deleteBtn);

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
                "top": "500px",
                "width": "100px",
                "height": "100px"
            },
            {
                "type": "scoreBoardCard",
                "left": "0px",
                "top": "0px",
                "width": "100px",
                "height": "100px"
            },
            {
                "type": "digitalClockCard",
                "left": "1000px",
                "top": "0px",
                "width": "100px",
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

function clearAllCards(){
    document.querySelectorAll(".movableItemsContainer .draggableCard").forEach(card => card.remove());
}

document.addEventListener("DOMContentLoaded", loadCardConfig);