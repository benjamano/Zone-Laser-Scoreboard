function addCard() {
    const container = document.querySelector(".movableItemsContainer");
    const card = document.createElement("div");
    card.classList.add("draggableCard");
    card.textContent = "Drag Me";
    card.style.left = "0px";
    card.style.top = "0px";
    card.draggable = true;
    container.appendChild(card);

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
        let x = Math.round((e.pageX - containerRect.left) / 100) * 100;
        let y = Math.round((e.pageY - containerRect.top) / 100) * 100;
        card.style.left = `${x}px`;
        card.style.top = `${y}px`;
    });
}