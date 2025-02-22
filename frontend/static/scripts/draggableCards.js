function addSmallCard() {
    const container = document.querySelector(".movableItemsContainer");

    card = createCard();

    card.classList.add("smallCard");

    container.appendChild(card);
}

function addLargeCard() {
    const container = document.querySelector(".movableItemsContainer");

    card = createCard();

    card.classList.add("largeCard");

    container.appendChild(card);
}

function addWideCard() {
    const container = document.querySelector(".movableItemsContainer");

    card = createCard();

    card.classList.add("wideCard");

    container.appendChild(card);
}

function addScoreBoardCard() {
    const container = document.querySelector(".movableItemsContainer");

    card = createCard();

    card.classList.add("scoreBoardCard");

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
}

function createRedTeamScoreCard(){
    const container = document.querySelector(".movableItemsContainer");

    card = createCard();

    card.classList.add("halfScoreBoardCard");

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
}

function createGreenTeamScoreCard() {
    const container = document.querySelector(".movableItemsContainer");

    card = createCard();

    card.classList.add("halfScoreBoardCard");

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
}

function createCard() {
    const container = document.querySelector(".movableItemsContainer");
    const card = document.createElement("div");

    card.classList.add("draggableCard");
    card.textContent = "Drag Me";
    card.style.left = "0px";
    card.style.top = "0px";
    card.draggable = true;

    card.addEventListener("dragstart", (e) => {
        e.dataTransfer.setData("text/plain", JSON.stringify({
            offsetX: e.offsetX,
            offsetY: e.offsetY
        }));
        card.classList.add("dragging");
    });

    container.addEventListener("dragover", (e) => {
        e.preventDefault(); 
    });

    container.addEventListener("drop", (e) => {
        e.preventDefault();
        let data = e.dataTransfer.getData("text/plain");
        if (!data) return;

        let { offsetX, offsetY } = JSON.parse(data);
        let containerRect = container.getBoundingClientRect();

        let x = Math.round((e.pageX - containerRect.left - offsetX) / 100) * 100;
        let y = Math.round((e.pageY - containerRect.top - offsetY) / 100) * 100;

        card.style.left = `${x}px`;
        card.style.top = `${y}px`;
    });

    return card;
}
