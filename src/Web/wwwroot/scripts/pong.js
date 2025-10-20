let canvas = document.getElementById('pongCanvas');
let ctx = canvas.getContext('2d');
let ballRadius = 8;
let x = canvas.width / 2;
let y = canvas.height / 2;
let dx = 3.5;
let dy = 0.3;
let paddleHeight = 70;
let paddleWidth = 10;
let paddle1Y = (canvas.height - paddleHeight) / 1.5;
let paddle2Y = (canvas.height - paddleHeight) / 1.5;
let paddle1aiSpeed = Math.random() * 20;
let paddle2aiSpeed = Math.random() * 20;
let footer = document.getElementById('footer');

// Function to set canvas size based on viewport dimensions
function resizeCanvas() {
    canvas.width = window.innerWidth * 0.98;
    canvas.height = footer.clientHeight;
    paddle1Y = Math.min(paddle1Y, canvas.height - paddleHeight); // Ensure paddle 1 stays within canvas
    paddle2Y = Math.min(paddle2Y, canvas.height - paddleHeight); // Ensure paddle 2 stays within canvas
}

// Call resizeCanvas initially and on window resize
window.addEventListener('resize', resizeCanvas);
resizeCanvas();

// AI control for both paddles
function aiControl() {
    let paddle1Center = paddle1Y + paddleHeight / 2;
    let paddle2Center = paddle2Y + paddleHeight / 2;

    // Adjust paddle 1 position based on ball position
    if (paddle1Center < y - 15) {
        paddle1Y += paddle1aiSpeed;
    } else if (paddle1Center > y + 15) {
        paddle1Y -= paddle1aiSpeed;
    }

    // Adjust paddle 2 position based on ball position
    if (paddle2Center < y - 10) {
        paddle2Y += paddle2aiSpeed;
    } else if (paddle2Center > y + 10) {
        paddle2Y -= paddle2aiSpeed;
    }

    // Ensure paddles stay within canvas boundaries
    paddle1Y = Math.min(Math.max(paddle1Y, 0), canvas.height - paddleHeight);
    paddle2Y = Math.min(Math.max(paddle2Y, 0), canvas.height - paddleHeight);
}

// Drawing functions
function drawBall() {
    ctx.beginPath();
    ctx.arc(x, y, ballRadius, 0, Math.PI * 2);
    ctx.fillStyle = 'white';
    ctx.fill();
    ctx.closePath();
}

function drawPaddle1() {
    ctx.beginPath();
    ctx.rect(0, paddle1Y, paddleWidth, paddleHeight);
    ctx.fillStyle = 'white';
    ctx.fill();
    ctx.closePath();
}

function drawPaddle2() {
    ctx.beginPath();
    ctx.rect(canvas.width - paddleWidth, paddle2Y, paddleWidth, paddleHeight);
    ctx.fillStyle = 'white';
    ctx.fill();
    ctx.closePath();
}

function draw() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    drawBall();
    drawPaddle1();
    drawPaddle2();
    aiControl();

    // Ball collision with top and bottom walls
    if (y + dy > canvas.height - ballRadius || y + dy < ballRadius) {
        dy = -dy;
    }

    // Ball collision with paddles
    if ((x + dx > canvas.width - paddleWidth - ballRadius) && (y > paddle2Y && y < paddle2Y + paddleHeight) ||
        (x + dx < paddleWidth + ballRadius) && (y > paddle1Y && y < paddle1Y + paddleHeight)) {
        dx = -dx;
        paddle1aiSpeed = Math.random() * 20;
        paddle2aiSpeed = Math.random() * 20;
    }

    // Ball goes out of bounds
    if (x + dx > canvas.width - ballRadius || x + dx < ballRadius) {
        // Reset ball position
        x = canvas.width / 2;
        y = canvas.height / 2;
        // Reset paddle positions
        paddle1Y = (canvas.height - paddleHeight) / 2;
        paddle2Y = (canvas.height - paddleHeight) / 2;
        // Reverse ball direction
        dx = -dx;
        paddle1aiSpeed = Math.random() * (10 - (-10)) + (-10);
        paddle2aiSpeed = Math.random() * (10 - (-10)) + (-10);
    }

    x += dx;
    y += dy;

    requestAnimationFrame(draw);
}

draw();
