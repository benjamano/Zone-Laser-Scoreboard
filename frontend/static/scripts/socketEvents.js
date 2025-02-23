var controlSpotify = true;
var gamePlayingStatus = "stopped"

var lastBPM = 0;
var totalDuration = 0;
var currentTime = 0;
var currentTimeLeft = 0;
var musicTimeInterval;

var socket = io.connect('http://' + window.location.hostname + ':8080', {transports: ['websocket']});

socket.on('connect', function() {
    try{
        $("#warningsContainer").css("display", "none");
        
        socket.emit('SpotifyControl', {data: controlSpotify});
        console.log("SpotifyControl: " + controlSpotify);
        console.log("Client connected!");

        if (controlSpotify == true){
            $("#spotifyPlaybackStatus").text("ON")
        } else {
            $("#spotifyPlaybackStatus").text("OFF")
        }

        $("#gameStatus").removeClass("go-red").addClass("go-blue");
        $("#gameStatus").text("Waiting");

        $("#webAppOnlineStatus").text("ONLINE");

        try{

        var messageDiv = document.getElementById('messages');

        messageDiv.innerHTML += '<p class="text-success">Connected @ '+Date.now()+'</p>';
        }
        catch(err){}
    }
    catch(err){}
});

socket.on('start', function(msg) {
    try{
        gamePlayingStatus = "playing";

        console.log(msg);

        for (let i = 1; i <= 21; i++) {
            $("#gun-" + i + "-score").text("0");
            $("#gun-" + i + "-accuracy").text("0%");
        }

        var gameStatus = document.getElementById('gameStatus');

        $("#gameStatus").removeClass("go-red go-blue go-green").addClass("go-green");
        $("#gameStatus").text("Game in Progress...");

        try{

            var messageDiv = document.getElementById('messages');

            messageDiv.innerHTML += '<p class="text-success">' + msg.message + '</p>';
        }
        catch(err){}
    }
    catch(err){}
});

socket.on('obsStatus', function(msg) {
    try{
        console.log(msg.message);

        $("#OBSConnectionStatus").text(msg.message)
    }
    catch(err){}
});

socket.on('dmxStatus', function(msg) {
    try{
        console.log(msg.message);

        $("#DMXConnectionStatus").text(msg.message)
    }
    catch(err){}
});

socket.on('end', function(msg) {
    try{
        gamePlayingStatus = "stopped";

        console.log(msg);

        for (let i = 1; i <= 21; i++) {
            $("#gun-" + i + "-score").text("0");
            $("#gun-" + i + "-accuracy").text("0%");
        }

        var gameStatus = document.getElementById('gameStatus');

        $("#timeRemaining").text("00:00");

        $("#gameStatus").removeClass("go-red go-blue go-green").addClass("go-mars");
        $("#gameStatus").text('Game ended at ' + new Date().toLocaleTimeString());
    }
    catch(err){}
});

socket.on('server', function(msg) {
    try{
        console.log(msg);

        try{
            var messageDiv = document.getElementById('messages');

            messageDiv.innerHTML += '<p class="text-danger">' + msg.message + '</p>';
        }
        catch(err){}
    }
    catch(err){}
});

socket.on('gameMode', function(msg) {
    try{
        console.log("Game Mode: ", msg.message);

        try{
        var messageDiv = document.getElementById('messages');

            messageDiv.innerHTML += '<p class="text-danger">' + msg.message + '</p>';
        }
        catch(err){}
        }
    catch(err){}
});

socket.on('gunScores', function(msg) {
    try{
        if (gamePlayingStatus == "stopped"){
            return;
        }

    console.log("gunScore: "+msg);

    var gunScores = msg.message.split(',');

    var gunId = gunScores[0];
    var finalScore = gunScores[1];
    var Accuracy = gunScores[2];

    console.log("Gun ID: " + gunId + " Score: " + finalScore + " Accuracy: " + Accuracy);

        $("#gun-"+gunId+"-score").text(finalScore);
        $("#gun-"+gunId+"-accuracy").text(Accuracy+"%")
    }
    catch(err){}
});

socket.on('disconnect', function() {
    var messageDiv = document.getElementById('messages');

    $("#webAppOnlineStatus").text("UNKNOWN");
    
    try{
    messageDiv.innerHTML += '<p class="text-danger">Disconnected @ '+Date.now()+'</p>';
    }

    catch(err){}
});

socket.on('timeRemaining', function (msg) {
    try{
        if (gamePlayingStatus == "stopped"){
            return;
        }

        const newTime = parseInt(msg.message);

        // If the current time is different from the new time, update the countdown
        if (currentTimeLeft !== newTime) {
            currentTimeLeft = newTime;

            // If there's an existing interval, clear it
            try{
                if (countdownInterval) {
                    clearInterval(countdownInterval);
                }
            }
            catch{}

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
    }
    catch(err){}
});

async function getAlbumCover(albumName) {
    const apiKey = 'ce4aeea69e2f5a8fb184700d5892aa82';
    const response = await fetch(`http://ws.audioscrobbler.com/2.0/?method=album.search&album=${encodeURIComponent(albumName)}&api_key=${apiKey}&format=json`);
    const data = await response.json();
    if (data.results.albummatches.album.length > 0) {
        return data.results.albummatches.album[0].image[3]['#text'];
    } else {
        return null;
    }
}

socket.on('songAlbum', async function(albumName) {
    try{
        console.log(albumName);

    if (albumName == "None"){
        return;
    }

    console.log(albumName.message);
    const imageUrl = await getAlbumCover(albumName.message);
    if (imageUrl) {
        document.getElementById('album-cover').style.backgroundImage = 'url(' + imageUrl + ')';
    } else {
            console.log('Album cover not found.');
        }
    }
    catch(err){}
});

socket.on('songName', function (msg) {
    try{
        console.log(msg.message);

        $("#currentPlayingSongForTrigger").val((msg.message).split(" - ")[1] + " - " + (msg.message).split(" - ")[0]);

        $("#musicPlaying").text(msg.message);
    }
    catch(err){}
});

socket.on('createWarning', function (msg) {
    console.log(msg.message);

    if (msg.message == "Restart"){
        $("#warningsText").text(msg.message);

        try{
            if (countdownInterval) {
                clearInterval(countdownInterval);
            }
        }
        catch{}

        TimeUntilRestart = 60;

        RestartCountdownInterval = setInterval(function () {
            if (TimeUntilRestart <= 0) {
                clearInterval(RestartCountdownInterval);
                return;
            }

            TimeUntilRestart--;

            const formattedTime = formatTime(TimeUntilRestart);
            $("#warningsText").text("warning: WebApp restarting in "+formattedTime + " | MUSIC WILL NOT BE AVAILABLE DURING THIS PERIOD");
        }, 1000);
    }
    else{
        $("#warningsText").text(msg.message);
    }

    $("#warningsContainer").css("display", "unset");

});

socket.on('musicStatus', function (msg) {
    try{
        console.log(msg.message);

        if (msg.message == "playing"){
            gamePlayingStatus = "playing";
            $("#pauseplayButton").removeClass("fa-circle-play").addClass("fa-circle-pause");
        } else {
        gamePlayingStatus = "stopped";
            $("#pauseplayButton").removeClass("fa-circle-pause").addClass("fa-circle-play");
        }
    }
    catch(err){}
});

socket.on('songBPM', function (msg) {
    try{
        console.log(msg.message);

        if (lastBPM == msg.message){
            return;
        }

        $("#musicBPM").text(msg.message);

        lastBPM = msg.message;

        if (msg.message == "0"){
            clearInterval(window.flashInterval);
            clearInterval(window.flashInterval2);

            return;
        }

        const flashSpeed = 60000 / parseInt(msg.message); // Calculate flash speed in milliseconds

        clearInterval(window.flashInterval);
        clearInterval(window.flashInterval2);

        window.flashInterval = setInterval(function () {
            $("#flashingDot").css("opacity", function(_, currentOpacity) {
                return currentOpacity == 1 ? 0 : 1;
            });
        }, flashSpeed);

        window.flashInterval2 = setInterval(function () {
            $("#flashingDot2").css("opacity", function(_, currentOpacity) {
                return currentOpacity == 1 ? 0 : 1;
                });
            }, flashSpeed*2);
        }
    catch(err){}
});

socket.on('musicDuration', function(duration) {
    try{
        totalDuration = duration.message;
        updateProgressBar(currentTime, totalDuration); 
    }
    catch(err){}
});

socket.on('musicPosition', function(position) {
    try{
        currentTime = position.message;
        updateProgressBar(currentTime, totalDuration);
    }
    catch(err){}
});

socket.on('UpdateDMXValue', function(data) {
    console.log("Updating DMX Value: ", data)

    var channel = data.message.channel;
    var value = data.message.value;
    var fixture = data.message.fixture;

    var valueLabel = document.getElementById(`valueLabel_${fixture}_${channel}`);
    var slider = document.getElementById(`slider_${fixture}_${channel}`);

    if (valueLabel) valueLabel.textContent = value;
    if (slider) slider.value = value;
});

socket.on("refreshPage", function() {
    location.reload();
});