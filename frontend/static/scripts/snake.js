var canvas = document.getElementById("SnakeCanvas");
var ctx = canvas.getContext("2d");

canvas.style.backgroundColor = "black";
canvas.width = canvas.closest(".card-body").clientWidth * 0.99;
canvas.height = canvas.closest(".card-body").clientHeight || 600;

var dx = 0;
var dy = 0;
var x = 100;
var y = 100;

var snakeLength = 1;
var segmentSize = 20;
var speed = segmentSize;
var growthRemaining = 0;

var lastUpdateTime = 0;
var gameSpeed = 100;

var snake = [];
var food = [];
var powerUps = [];

for (let i = 0; i < snakeLength; i++) {
    snake.push({ x: x, y: y });
}

function addFood(){
    const foodX = Math.floor(Math.random() * (canvas.width / segmentSize)) * segmentSize;
    const foodY = Math.floor(Math.random() * (canvas.height / segmentSize)) * segmentSize;
    return { x: foodX, y: foodY };
}

food.push(addFood());

function drawSnake() {
    ctx.fillStyle = 'white';
    for (let part of snake) {
        ctx.fillRect(part.x, part.y, segmentSize, segmentSize);
    }
}

function drawFood() {
    ctx.fillStyle = 'red';
    for (let part of food) {
        ctx.fillRect(part.x, part.y, segmentSize, segmentSize);
    }
}

function drawScore() {
    ctx.fillStyle = 'white';
    ctx.font = "20px Arial";
    ctx.fillText("Score: " + (snake.length - snakeLength), 10, 20);
}

function drawPowerUp(){
    ctx.fillStyle = 'blue';
    for (let part of powerUps) {
        ctx.fillRect(part.x, part.y, segmentSize, segmentSize);
    }
}

function isSnakeCollidingWithFood() {
    const head = snake[0];
    for (let part of food) {
        if (head.x < part.x + segmentSize && head.x + segmentSize > part.x && head.y < part.y + segmentSize && head.y + segmentSize > part.y){
            return true;
        }
    }
    return false;
}

function isSnakeCollidingWithPowerUp() {
    const head = snake[0];
    for (let part of powerUps) {
        if (head.x < part.x + segmentSize && head.x + segmentSize > part.x && head.y < part.y + segmentSize && head.y + segmentSize > part.y){
            return true;
        }
    }
    return false;
}

function isSnakeCollidingWithItself(){
    const head = snake[0];
    for (let i = 1; i < snake.length; i++) {
        if (head.x < snake[i].x + segmentSize && head.x + segmentSize > snake[i].x && head.y < snake[i].y + segmentSize && head.y + segmentSize > snake[i].y){
            return true;
        }
    }
    return false;
}

function setRandomPowerUp(){
    var random = Math.floor(Math.random() * 10);
    if (random < 4) {
        var originalSpeed = gameSpeed;

        gameSpeed -= 50;
        setTimeout(() => {
            gameSpeed = originalSpeed;
        }, 5000);
    }
    else {
        growthRemaining += 3;
    }
}

function updateSnake() {
    const head = { x: snake[0].x + dx, y: snake[0].y + dy };
    snake.unshift(head);
    snake.pop();
}

document.onkeydown = (e) => {
    switch (e.key) {
        case "ArrowUp":
            if (dy > 0) return;

            dy = -speed;
            dx = 0;
            break;
        case "ArrowDown":
            if (dy < 0) return;

            dy = speed;
            dx = 0;
            break;
        case "ArrowLeft":
            if (dx > 0) return;

            dx = -speed;
            dy = 0;
            break;
        case "ArrowRight":
            if (dx < 0) return;

            dx = speed;
            dy = 0;
            break;
    }
}

function draw(timestamp) {
    if (!lastUpdateTime) lastUpdateTime = timestamp;

    const delta = timestamp - lastUpdateTime;
    if (delta >= gameSpeed) {
        lastUpdateTime = timestamp;

        const head = { x: snake[0].x + dx, y: snake[0].y + dy };
        snake.unshift(head);

        if (growthRemaining > 0) {
            growthRemaining--;
        } else {
            snake.pop();
        }

        if (isSnakeCollidingWithFood()) {
            food = [addFood()];
            growthRemaining += 1;
        }

        if (isSnakeCollidingWithPowerUp()) {
            powerUps = [];
            setRandomPowerUp();
        }

        if (isSnakeCollidingWithItself()){
            snake = [head];
            dx = -dx;
            dy = -dy;
        }

        if (head.x < 0 && dx < 0) { 
            snake = [head];
            dx = -dx;
            powerUps = [addFood()];
            food = [addFood()];
        }
        if (head.x + segmentSize > canvas.width && dx > 0) {  
            snake = [head];
            dx = -dx;
            powerUps = [addFood()];
            food = [addFood()];
        }
        if (head.y < 0 && dy < 0) {  
            snake = [head];
            dy = -dy;
            powerUps = [addFood()];
            food = [addFood()];
        }
        if (head.y + segmentSize > canvas.height && dy > 0) {  
            snake = [head];
            dy = -dy;
            powerUps = [addFood()];
            food = [addFood()];
        }        
    }

    if (Math.random() < 0.001 && powerUps.length == 0) {
        powerUps.push(addFood());
    }

    ctx.clearRect(0, 0, canvas.width, canvas.height);
    drawSnake();
    drawFood();
    drawScore();
    drawPowerUp();

    requestAnimationFrame(draw);
}

requestAnimationFrame(draw);

draw();