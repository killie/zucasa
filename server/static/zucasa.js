
var progressTimer;

// Check if a date section was clicked in sidebar
window.onhashchange = function (e) {
    var hash = e.newURL.substring(e.newURL.indexOf("#")), section, url, i, s;
    if (hash.length < 9) return;
    section = $(hash);
    if (section.length == 0) {
	// Section was not found, load from server given date from hash
	url = window.location.href;
	i = url.indexOf("#");
	if (i !== -1) url = url.substring(0, i);
	i = url.indexOf("date=");
	if (i === -1) {
	    // Adding date as new GET argument
	    url += (url.indexOf("?") === -1 ? "?" : "&") + "date=" + hash.substring(1);
	} else {
	    // Replacing current date value
	    url = url.substring(0, i) + "date=" + hash.substring(1) + url.substring(i + 13);
	}
	window.location = url;
    }
};

// Open/close branches in sidebar on click
$(".sidebar li a").click(function (e) {
    $(e.target.parentElement).toggleClass("collapsed").toggleClass("expanded");
});

// Open photo when clicking thumbnail
$("img.thumbnail").click(function (e) {
    // Remember main location for 30 minutes, for use when pressing close from view page
    if ($("body#main").length) {
	document.cookie = "mainLocation=" + document.location.href + "; max-age=60*30;";
    }
    openThumbnail(e.target.src);
});

function getThumbnailUrl(index) {
    return $("img.thumbnail").eq(index).attr("src");
}

function openThumbnail(url) {
    // Remove extension, but it can be more than 3 chars
    var href = url.substring(0, url.length - 4);
    var s = href.replace("/static/import/photos", "") + window.location.search;
    window.location.href = s;
}

// Clicking filter in sidebar
$(".users > div, .cameras > div, .tags > div").click(function (e) {
    var users = [], cameras = [], tags = [], url, first = true;

    function addFilters(key, values) {
	if (values.length) {
	    url += (first ? "?" : "&") + key + "=" + values.join(",");
	    first = false;
	}
    }

    // Toggle clicked filter
    $(e.target).toggleClass("selected");

    // Collect current filters
    $(".sidebar .selected").each(function () {
	var filter = encodeURIComponent(this.innerText);
	var header = this.parentElement.className;
	if (header === "users") users.push(filter);
	if (header === "cameras") cameras.push(filter);
	if (header === "tags") tags.push(filter);
    });

    // Create new URL with current filters
    url = "http://" + window.location.host + "/";
    addFilters("users", users);
    addFilters("cameras", cameras);
    addFilters("tags", tags);

    // Maintain selected date if possible
    url += window.location.hash;
    window.location.href = url;
});

// Clicking 'Show newer' or 'Show older' buttons
$(".show-more").click(function (e) {
    var s;
    if (e.target.innerText === "Show newer") {
	s = $("section").eq(0).attr("id");
	console.debug("Show newer than", s);
    } else if (e.target.innerText === "Show older") {
	s = $("section").eq(-1).attr("id");
	console.debug("Show older than", s);
    } else {
	console.warn("Unknown .show-more text");
    }
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

// If showing main page put focus in scrollable page content
$(function (e) {
    if ($("#main").length) {
	$(".page-content").focus();
    }
});
