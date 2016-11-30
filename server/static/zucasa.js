
var progressTimer;

// Open/close branches in sidebar on click
$(".sidebar li a").click(function (e) {
    $(e.target.parentElement).toggleClass("collapsed").toggleClass("expanded");
});

// Open photo when clicking thumbnail
$("img.thumbnail").click(function (e) {
    // Remember main location for 30 minutes, for use when pressing close from view page
    document.cookie = "mainLocation=" + document.location.href + "; max-age=60*30;";
    openThumbnail(e.target.src);
});

function getThumbnailUrl(index) {
    return $("img.thumbnail").eq(index).attr("src");
}

function openThumbnail(url) {
    // Remove extension, but it can be more than 3 chars
    var href = url.substring(0, url.length - 4);
    window.location.href = href.replace("/static/import/photos", "");
}

// Clicking filter in sidebar
$(".users > div, .cameras > div, .tags > div").click(function (e) {
    $(e.target).toggleClass("selected");
});

// Show original when clicking zoom on photo
$(".photo .zoom").click(function (e) {
    var src = $(e.target.parentElement).css("background-image");
    src = src.replace('url("', '').replace('")', '');
    window.location.href = src;
});

// Show prev photo when clicking < on photo
$(".photo .prev").click(function (e) {
    openThumbnail(getThumbnailUrl(2));
});

// Show next photo when clicking > on photo
$(".photo .next").click(function (e) {
    openThumbnail(getThumbnailUrl(4));
});

// Clicking close on view page goes back previous main location
$("#view .close").click(function (e) {
    // https://developer.mozilla.org/en-US/docs/Web/API/Document/cookie
    var mainLocation = document.cookie.replace(/(?:(?:^|.*;\s*)mainLocation\s*\=\s*([^;]*).*$)|^.*$/, "$1");
    window.location.href = mainLocation;
});

// Clicking cancel on config page goes to previous page
$("#config .cancel").click(function (e) {
    if (window.history.length) {
	window.history.back();
    }
});

// Get progress from server and show in overlay
// Stop progressTimer when server returns "Idle"
function getProgress() {
    $.getJSON("/_get_progress", {}, function (progress) {
	if (progress.status === "Idle") {
	    stopProgressTimer();
	    console.debug("Change page")
	    return;
	}
	$ul = $("#progress ul");
	if ($ul.length) {
	    $li = $ul.find(":last-child");
	    if ($li.length) {
		if ($li.text() !== progress.status) {
		    $ul.append("<li>" + progress.status + "</li>");
		}
	    } else {
		$ul.append("<li>" + progress.status + "</li>");
	    }
	} else {
	    console.debug("Look for something else that holds progress");
	}
    });
}

function startProgressTimer() {
    console.debug("Starting timer");
    progressTimer = window.setInterval(getProgress, 1000);
}

function stopProgressTimer() {
    console.debug("Stopping timer");
    window.clearInterval(progressTimer);
}
