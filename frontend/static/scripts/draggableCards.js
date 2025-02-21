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

function createCard(){
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

    card.addEventListener("dragend", (e) => {
        card.classList.remove("dragging");
        let containerRect = container.getBoundingClientRect();
        let x = Math.round((e.pageX - containerRect.left - card.offsetWidth / 2) / 100) * 100;
        let y = Math.round((e.pageY - containerRect.top - card.offsetHeight / 2) / 100) * 100;
        card.style.left = `${x}px`;
        card.style.top = `${y}px`;
    });

    return card;
}