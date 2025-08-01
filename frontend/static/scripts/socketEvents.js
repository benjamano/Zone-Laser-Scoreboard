var controlSpotify = true;
var gamePlayingStatus = "stopped";

var lastBPM = 0;
var totalDuration = 0;
var currentTime = 0;
var currentTimeLeft = 0;
var musicTimeInterval;

var socket = io.connect("http://" + window.location.hostname + ":8080", { transports: ["websocket"] });

socket.on("connect", function () {
	try {
		$("#warningsContainer").css("display", "none");

		socket.emit("SpotifyControl", { data: controlSpotify });
		console.log("SpotifyControl: " + controlSpotify);
		console.log("Client connected!");

		if (controlSpotify == true) {
			$("#spotifyPlaybackStatus").text("ON");
		} else {
			$("#spotifyPlaybackStatus").text("OFF");
		}

		$("#gameStatus").removeClass("go-red").addClass("go-blue");
		$("#gameStatus").text("Waiting");

		$("#webAppOnlineStatus").text("ONLINE");

		try {
			var messageDiv = document.getElementById("messages");

			messageDiv.innerHTML += '<p class="text-success">Connected @ ' + Date.now() + "</p>";
		} catch (err) {}
	} catch (err) {}
});

socket.on("start", function (msg) {
	try {
		gamePlayingStatus = "playing";

		// console.log(msg);

		for (let i = 1; i <= 21; i++) {
			$("#gun-" + i + "-score").text("0");
			$("#gun-" + i + "-accuracy").text("0%");
		}

		var gameStatus = document.getElementById("gameStatus");

		$("#gameStatus").removeClass("go-red go-blue go-green").addClass("go-green");
		$("#gameStatus").text("Game in Progress...");

		try {
			var messageDiv = document.getElementById("messages");

			messageDiv.innerHTML += '<p class="text-success">' + msg.message + "</p>";
		} catch (err) {}

		$(document).trigger("gameStarted", [msg]);
	} catch (err) {}
});

socket.on("zonePacket", function(msg){
	$(document).trigger("zonePacketRecieved", [msg.data]);
})

socket.on("obsStatus", function (msg) {
	try {
		// console.log(msg.message);

		$("#OBSConnectionStatus").text(msg.message);
	} catch (err) {}
});

socket.on("dmxStatus", function (msg) {
	try {
		// console.log(msg.message);

		$("#DMXConnectionStatus").text(msg.message);
	} catch (err) {}
});

socket.on("end", function (msg) {
	try {
		gamePlayingStatus = "stopped";

		// console.log(msg);

		for (let i = 1; i <= 21; i++) {
			$("#gun-" + i + "-score").text("0");
			$("#gun-" + i + "-accuracy").text("0%");
		}

		var gameStatus = document.getElementById("gameStatus");

		$("#timeRemaining").text("00:00:00");

		$("#gameStatus").removeClass("go-red go-blue go-green").addClass("go-mars");
		$("#gameStatus").text("Game ended at " + new Date().toLocaleTimeString());
	} catch (err) {}
});

socket.on("server", function (msg) {
	try {
		// console.log(msg);

		try {
			var messageDiv = document.getElementById("messages");

			messageDiv.innerHTML += '<p class="text-danger">' + msg.message + "</p>";
		} catch (err) {}
	} catch (err) {}
});

socket.on("gameMode", function (msg) {
	try {
		// console.log("Game Mode: ", msg.message);

		try {
			var messageDiv = document.getElementById("messages");

			messageDiv.innerHTML += '<p class="text-danger">' + msg.message + "</p>";
		} catch (err) {}
	} catch (err) {}
});

socket.on("gunScores", function (msg) {
	try {
		if (gamePlayingStatus == "stopped") {
			return;
		}

		// console.log("gunScore: "+msg);

		var gunScores = msg.message.split(",");

		var gunId = gunScores[0];
		var finalScore = gunScores[1];
		var Accuracy = gunScores[2];

		// console.log("Gun ID: " + gunId + " Score: " + finalScore + " Accuracy: " + Accuracy);

		$("#gun-" + gunId + "-score").text(finalScore);
		$("#gun-" + gunId + "-accuracy").text(Accuracy + "%");
	} catch (err) {}
});

socket.on("disconnect", function () {
	var messageDiv = document.getElementById("messages");

	$("#webAppOnlineStatus").text("UNKNOWN");

	try {
		messageDiv.innerHTML += '<p class="text-danger">Disconnected @ ' + Date.now() + "</p>";
	} catch (err) {}
});

socket.on("timeRemaining", function (msg) {
	try {
		if (gamePlayingStatus == "stopped") {
			return;
		}

		const newTime = parseInt(msg.message);

		// If the current time is different from the new time, update the countdown
		if (currentTimeLeft !== newTime) {
			currentTimeLeft = newTime;

			// If there's an existing interval, clear it
			try {
				if (countdownInterval) {
					clearInterval(countdownInterval);
				}
			} catch {}

			countdownInterval = setInterval(function () {
				if (currentTimeLeft <= 0) {
					clearInterval(countdownInterval);
					return;
				}

				currentTimeLeft--;

				const formattedTime = formatTime(currentTimeLeft);
				$("#timeRemaining").text(formattedTime);
			}, 1000);
		}
	} catch (err) {}
});

async function getAlbumCover(albumName) {
	const apiKey = "ce4aeea69e2f5a8fb184700d5892aa82";
	const response = await fetch(`http://ws.audioscrobbler.com/2.0/?method=album.search&album=${encodeURIComponent(albumName)}&api_key=${apiKey}&format=json`);
	const data = await response.json();
	if (data.results.albummatches.album.length > 0) {
		return data.results.albummatches.album[0].image[3]["#text"];
	} else {
		return null;
	}
}

var previousAlbumName = "";

socket.on("songAlbum", async function (albumName) {
	try {
		if (albumName.message != previousAlbumName) {
			previousAlbumName = albumName.message;

			const imageUrl = await getAlbumCover(albumName.message);

			if (imageUrl) {
				document.getElementById("album-cover").style.backgroundImage = "url(" + imageUrl + ")";
			}
		}
	} catch (err) {}
});

socket.on("songName", function (msg) {
	try {
		// console.log(msg.message);

		if (msg.message == "No media playing") {
		} else {
			$("#currentPlayingSongForTrigger").val(msg.message.split(" - ")[1] + " - " + msg.message.split(" - ")[0]);
			$("#musicPlaying").text(msg.message);
			$("#setThisSongAsBindButton").show();
		}
	} catch (err) {}
});

socket.on("createWarning", function (msg) {
	console.log(msg.message);

	createWarning(msg.message);
});

// socket.on('musicStatus', function (msg) {
//     try{
//         console.log(msg.message);

//         if (msg.message == "playing"){
//             gamePlayingStatus = "playing";
//             $("#pauseplayButton").removeClass("fa-circle-play").addClass("fa-circle-pause");
//         } else {
//         gamePlayingStatus = "stopped";
//             $("#pauseplayButton").removeClass("fa-circle-pause").addClass("fa-circle-play");
//         }
//     }
//     catch(err){}
// });

socket.on("musicStatusV2", function (msg) {
	try {
		msg = msg.message;

		if (msg.playbackStatus == true) {
			gamePlayingStatus = "playing";
			$(".pausePlayMusicButton").removeClass("fa-circle-play").addClass("fa-circle-pause");
		} else {
			gamePlayingStatus = "stopped";
			$(".pausePlayMusicButton").removeClass("fa-circle-pause").addClass("fa-circle-play");
		}

		const durationDiff = Math.abs(msg.musicPosition - (currentTime ?? 0));
		if (durationDiff > 10 || currentTime == 0) {
			if (msg.musicPosition !== undefined) {
				currentTime = msg.musicPosition;
			}

			totalDuration = msg.duration;

			updateProgressBar(currentTime, totalDuration);
		}
	} catch (err) {
		// handle error if you want, or leave silent
	}
});
let lastMusicQueueHtml = "";
socket.on("musicQueue", function (queue) {
	var containers = $(".musicQueueList");

	if (containers.length == 0) { return; }

	containers.each(async function (_, container) {
		var isContainerLargeEnough = $(container).width() > 300;

		const newSongIds = queue.queue.map(song => song.id);

		const currentSongIds = [];
		$(container).find("li.list-group-item[data-song-id]").each(function () {
			const id = $(this).attr("data-song-id");
			currentSongIds.push(parseInt(id, 10));
		});

		const idsAreSame = currentSongIds.length === newSongIds.length &&
			currentSongIds.every((id, idx) => id === newSongIds[idx]);
		if (idsAreSame) return;

		var contentArr = await Promise.all(queue.queue.map(async song => {
			var songName = song.name;
			var songAlbum = song.album;
			var songArtist = song.artist;
			var songDuration = song.duration;

			let formattedDuration = "";
			if (songDuration != "" && songDuration != null && !isNaN(songDuration)) {
				const minutes = Math.floor(songDuration / 60);
				const seconds = Math.floor(songDuration % 60);
				formattedDuration = `${minutes}:${seconds < 10 ? "0" : ""}${seconds}`;
			}

			let albumCoverUrl = "";

			try {
				if (isContainerLargeEnough) {
					albumCoverUrl = await getAlbumCover(songAlbum);
				}
			}
			catch (err) {
				albumCoverUrl = "";
			}

			return `
				<li class="list-group-item d-flex flex-row justify-content-between align-items-start" data-song-id="${song.id}">
					${isContainerLargeEnough ? `<div class="border-end pe-2">
						${(isContainerLargeEnough && albumCoverUrl ? `<img src="${albumCoverUrl}" class="rounded mb-1" style="max-width: 50px; max-height: 50px;">` : "")}
					</div>` : ""}
					<div class="d-flex flex-column align-items-start flex-grow-1 overflow-hidden text-muted ${isContainerLargeEnough ? "ps-2" : ""}">
						<p class="mb-1 text-truncate w-100">
							<u><strong>${songName}</strong></u>
						</p>	
						<p class="mb-1 text-truncate w-100 fs-7">
							${(songArtist != "" && songArtist != null ? songArtist + " - " + songAlbum : songAlbum)}
						</p>
						${(formattedDuration ? `<p class="mb-1 fs-7">(${formattedDuration})</p>` : "")}
					</div>
					<button class="btn btn-close btn-close-white ms-2" onclick="removeSongFromQueue('${song.id}')"></button>
				</li>
			`;
		}));

		let newHtml;
		if (isContainerLargeEnough == true) {
			newHtml = `<div id='musicQueueHeader' class="musicQueueHeader list-group-item d-flex flex-row justify-content-between align-items-center">
				<span class="fs-6"><b>Up Next...</b></span>
				<button class="btn btn-outline-secondary d-none" onclick="clearMusicQueue();">Clear Queue</button>
			</div>` + contentArr.join("");
		} else {
			newHtml = contentArr.join("");
		}

		$(container).html(newHtml);
	});
});

function updateProgressBar(currentTime, totalDuration) {
	const progressBars = $(".musicProgressBar");
	const timeLeftDisplays = $(".timeLeft");

	if (musicTimeInterval) {
		clearInterval(musicTimeInterval);
	}

	let internalCurrentTime = currentTime;
	let startTime = Date.now();

	function updateDisplay() {
		if (gamePlayingStatus === "stopped") return;

		const elapsedSeconds = (Date.now() - startTime) / 1000;
		const progressPercent = (Math.min(internalCurrentTime + elapsedSeconds, totalDuration) / totalDuration) * 100;

		progressBars.css("width", progressPercent + "%");

		const timeLeft = totalDuration - (internalCurrentTime + elapsedSeconds);
		if (timeLeft >= 0) {
			const minutesLeft = Math.floor(timeLeft / 60);
			const secondsLeft = Math.floor(timeLeft % 60);
			const timeString = `-${minutesLeft}:${secondsLeft < 10 ? "0" : ""}${secondsLeft}`;
			timeLeftDisplays.text(timeString);
		}

		if (elapsedSeconds >= 1) {
			internalCurrentTime += Math.floor(elapsedSeconds);
			startTime += Math.floor(elapsedSeconds) * 1000;
		}

		if (internalCurrentTime >= totalDuration) {
			clearInterval(musicTimeInterval);
		}
	}

	updateDisplay();
	musicTimeInterval = setInterval(updateDisplay, 100);
}

socket.on("songBPM", function (msg) {
	try {
		// console.log(msg.message);

		if (lastBPM == msg.message) {
			return;
		}

		$("#musicBPM").text(msg.message);

		lastBPM = msg.message;

		if (msg.message == "0") {
			clearInterval(window.flashInterval);
			clearInterval(window.flashInterval2);

			return;
		}

		const flashSpeed = 60000 / parseInt(msg.message); // Calculate flash speed in milliseconds

		clearInterval(window.flashInterval);
		clearInterval(window.flashInterval2);

		window.flashInterval = setInterval(function () {
			$("#flashingDot").css("opacity", function (_, currentOpacity) {
				return currentOpacity == 1 ? 0 : 1;
			});
		}, flashSpeed);

		window.flashInterval2 = setInterval(function () {
			$("#flashingDot2").css("opacity", function (_, currentOpacity) {
				return currentOpacity == 1 ? 0 : 1;
			});
		}, flashSpeed * 2);
	} catch (err) {}
});

// socket.on('musicDuration', function(duration) {
//     try{
//         totalDuration = duration.message;
//         updateProgressBar(currentTime, totalDuration);
//     }
//     catch(err){}
// });

// socket.on('musicPosition', function(position) {
//     try{
//         currentTime = position.message;
//         updateProgressBar(currentTime, totalDuration);
//     }
//     catch(err){}
// });

socket.on("UpdateDMXValue", function (data) {
	// console.log("Updating DMX Value: ", data)

	var channel = data.message.channel;
	var value = data.message.value;
	var fixture = data.message.fixture;

	var valueLabel = document.getElementById(`valueLabel_${fixture}_${channel}`);
	var slider = document.getElementById(`slider_${fixture}_${channel}`);

	if (valueLabel) valueLabel.textContent = value;
	if (slider) slider.value = value;
});

socket.on("refreshPage", function () {
	location.reload(true);
});

socket.on("logMessage", function (data) {
	// console.log(`Received log message: ${JSON.stringify(data)}`);
	// console.log(`Received log message with content: ${data.message.message}`);
	// console.log(`Received log message with type: ${data.message.logType}`);

	const now = Date.now();

	let logMessages = JSON.parse(localStorage.getItem("logMessages")) || [];

	// Remove messages older than 8 hours
	logMessages = logMessages.filter((msg) => now - msg.receivedDate < 28800000);

	data.receivedDate = now;

	logMessages.push(data);

	localStorage.setItem("logMessages", JSON.stringify(logMessages));
});

function getCurrentSong() {
	try {
		socket.emit("getCurrentSong");
	} catch (err) {
		console.error("Error getting current song:", err);
	}
}

function setMusicVolume(elem) {
	socket.emit("setVolume", { volume: $(elem).val() });
	$(elem).closest('.musicVolumeSlider').find('.volumeValue').text($(elem).val() + "%");
}

socket.on("musicVolume", function (msg) {
	$(".volumeControlSlider").each(function(){
		$(this).val(msg.message);
		$(this).closest('.musicVolumeSlider').find('.volumeValue').text(msg.message + "%");
	})
});