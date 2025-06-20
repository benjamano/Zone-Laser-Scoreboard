function renderDate(value) {
    return (
        "<span class='text-start'>" +
        new Date(value).toLocaleString() +
        "</span>"
    );
}

function renderValue(value) {
    return "<span class='text-start'>" + value + "</span>";
}

function renderPlaylistActions(data) {
    return "<span></span>";
}
