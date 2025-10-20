let beatCount = 0;
let beatInterval = 0;
let currentBPM = 0;
let isBeating = false;

const icons = Array.from(document.querySelectorAll(".sidebarIcon"));

socket.on("songBpm", function(msg) {
	const newBPM = msg.message / 2;

	if (isMusicPlaying === true) {
		if (newBPM !== currentBPM) {
			currentBPM = newBPM;
			startBeat(currentBPM);
		}
	} else {
		startBeat(0);
	}
});

function doBeat() {
	if ($("#pauseplayButton").hasClass("fa-circle-play")) return stopBeat();

	beatCount++;

	document.body.classList.add("beat");

	document.documentElement.classList.add("beat-pulse");

	setTimeout(() => {
		document.body.classList.remove("beat");
		document.documentElement.classList.remove("beat-pulse");
	}, 200);
}

function startBeat(bpm) {
	if (bpm === 0) {
		stopBeat();
		return;
	}

	clearInterval(beatInterval);

	const intervalMs = (60 / bpm) * 1000;
	beatCount = 0;

	document.documentElement.style.setProperty("--beat-duration", `${intervalMs}ms`);

	isBeating = true;

	icons.forEach((icon, index) => {
		const swingClass = (index % 2 === 0) ? "swing-left" : "swing-right";
		setTimeout(() => {
			if (isBeating) {
				icon.classList.add(swingClass);
			}
		}, index * 50);
	});

	doBeat();
	beatInterval = setInterval(doBeat, intervalMs);
}

function stopBeat() {
	clearInterval(beatInterval);
	isBeating = false;
	currentBPM = 0;

	document.body.classList.remove("beat");
	document.documentElement.classList.remove("beat-pulse");

	icons.forEach(icon => {
		icon.classList.remove("swing-left", "swing-right");
	});
}