const container = document.querySelector(".movableItemsContainer");

function createCard() {
    const card = document.createElement("div");
    card.classList.add("draggableCard");
    card.style.left = "0px";
    card.style.top = "0px";
    card.draggable = true;
    card.dataset.id = Date.now(); // Unique ID

    const deleteBtn = document.createElement("i");
    deleteBtn.classList.add("fas", "fa-trash", "bg-danger", "trash-icon");
    deleteBtn.addEventListener("click", () => deleteCard(card));

    card.appendChild(deleteBtn);

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

    return card;
}

function addSmallCard() {
    const card = createCard();
    card.textContent = "Drag Me";
    card.classList.add("smallCard");
    card.dataset.type = "smallCard";
    container.appendChild(card);
    return card;
}

function addLargeCard() {
    const card = createCard();
    card.textContent = "Drag Me";
    card.classList.add("largeCard");
    card.dataset.type = "largeCard";
    container.appendChild(card);
    return card;
}

function addWideCard() {
    const card = createCard();
    card.textContent = "Drag Me";
    card.classList.add("wideCard");
    card.dataset.type = "wideCard";
    container.appendChild(card);
    return card;
}

function addScoreBoardCard() {
    const card = createCard();
    card.classList.add("scoreBoardCard");
    card.dataset.type = "scoreBoardCard";
    card.innerHTML = `
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
    container.appendChild(card);
    return card;
}

function createRedTeamScoreCard(){
    const card = createCard();
    card.classList.add("halfScoreBoardCard");
    card.dataset.type = "halfScoreBoardCard_red";
    card.innerHTML = `
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
    container.appendChild(card);
    return card;
}

function createGreenTeamScoreCard() {
    const card = createCard();
    card.classList.add("halfScoreBoardCard");
    card.dataset.type = "halfScoreBoardCard_green";
    card.innerHTML = `
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
    container.appendChild(card);
    return card;
}

function createClockCard() {
    const card = createCard();
    card.classList.add("wideCard", "digitalClockCard");
    card.dataset.type = "digitalClockCard";

    const clock = document.createElement("div");
    clock.classList.add("digitalClock");
    card.appendChild(clock);

    function updateClock() {
        const now = new Date();
        const timeString = now.toLocaleTimeString("en-GB", { hour12: false }) + `.${now.getMilliseconds().toString().padStart(3, "0")}`;
        clock.textContent = timeString;
    }

    setInterval(updateClock, 10);
    updateClock();

    container.appendChild(card);
    return card;
}

function createMusicControlsCard() {
    const card = createCard();
    card.classList.add("smallWideCard");
    card.dataset.type = "musicControlsCard";

    card.innerHTML = `
    <div class="musicControls">
        <i role="button" onclick="restartSong()" class="fa-solid fa-backward" aria-hidden="true"></i>
        <i role="button" id="pauseplayButton" onclick="toggleMusic()" class="fa-regular fa-circle-play" aria-hidden="true"></i>
        <i role="button" onclick="nextSong()" class="fa-solid fa-forward" aria-hidden="true"></i>
                                                    
        <div style="flex-grow: 1; height: 10px; background-color: #555; border-radius: 10px; overflow: hidden; margin-left: 10px; position: relative; width: 10rem;">
            <div id="progressBar" style="height: 100%; width: 0; background-color: #1db954;"></div>
        </div>
															
        <span id="timeLeft" style="color: #fff;">0:00</span>
    </div>`;

    container.appendChild(card);
    return card;
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
    let x = Math.round((e.pageX - containerRect.left - offsetX) / 100) * 100;
    let y = Math.round((e.pageY - containerRect.top - offsetY) / 100) * 100;

    droppedCard.style.left = `${x}px`;
    droppedCard.style.top = `${y}px`;
});

function clearAllCards(){
    document.querySelectorAll(".movableItemsContainer .draggableCard").forEach(card => card.remove());
}

// Save the configuration of all cards (type and position) into localStorage.
function saveCardConfig() {
    const cards = container.querySelectorAll(".draggableCard");
    const config = Array.from(cards).map(card => ({
        type: card.dataset.type,
        left: card.style.left,
        top: card.style.top
    }));
    localStorage.setItem("cardConfig", JSON.stringify(config));
}

setInterval(saveCardConfig, 2000);

function loadCardConfig() {
    var configStr = localStorage.getItem("cardConfig");

    if (!configStr || configStr.trim() === "" || configStr === "[]" || configStr === "null") {
        console.log("No autosaved config found, generating new");
        configStr = JSON.stringify([
            {
                "type": "musicControlsCard",
                "left": "0px",
                "top": "500px"
            },
            {
                "type": "scoreBoardCard",
                "left": "0px",
                "top": "0px"
            },
            {
                "type": "digitalClockCard",
                "left": "1000px",
                "top": "0px"
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
        let card;
        switch (cardConfig.type) {
            case "smallCard":
                card = addSmallCard();
                break;
            case "largeCard":
                card = addLargeCard();
                break;
            case "wideCard":
                card = addWideCard();
                break;
            case "scoreBoardCard":
                card = addScoreBoardCard();
                break;
            case "halfScoreBoardCard_red":
                card = createRedTeamScoreCard();
                break;
            case "halfScoreBoardCard_green":
                card = createGreenTeamScoreCard();
                break;
            case "digitalClockCard":
                card = createClockCard();
                break;
            case "musicControlsCard":
                card = createMusicControlsCard();
                break;
            default:
                card = addSmallCard();
        }

        if (card) {
            card.style.left = cardConfig.left;
            card.style.top = cardConfig.top;
        }
    });
}

document.addEventListener("DOMContentLoaded", loadCardConfig);