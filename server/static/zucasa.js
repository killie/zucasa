
var progressTimer;

// Check if a date section was clicked in sidebar
window.onhashchange = function (e) {
    var hash = e.newURL.substring(e.newURL.indexOf("#")), section;
    if (hash.length < 9) return;
    section = $(hash);
    if (section.length == 0) {
	// Section was not found, load from server given date from hash
	loadPhotosFromDate(hash.substring(1));
    }
};

function loadPhotosFromDate(date) {
    var url = window.location.href;
    var i = url.indexOf("#");
    if (i !== -1) url = url.substring(0, i);
    i = url.indexOf("date=");
    if (i === -1) {
	// Adding date as new GET argument
	url += (url.indexOf("?") === -1 ? "?" : "&") + "date=" + date;
    } else {
	// Replacing current date value
	url = url.substring(0, i) + "date=" + date + url.substring(i + 13);
    }
    window.location = url;
}

// Open/close branches in sidebar on click
$(".sidebar li a").click(function (e) {
    $(e.target.parentElement).toggleClass("collapsed").toggleClass("expanded");
});

// Open photo when clicking thumbnail
$("img.thumbnail").click(showThumbnail);

function showThumbnail(event) {
    // Remember hash on main location for 30 minutes, for use when pressing close from view page
    if ($("body#main").length) {
	document.cookie = "mainLocation=" + document.location.hash + "; max-age=60*30;";
    }
    openThumbnail(event.target.src);
}

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
    var uuid, direction;
    if (e.target.innerText === "Show newer") {
	uuid = getIdFromThumbnail($("img.thumbnail").eq(0));
	direction = "newer";
    } else if (e.target.innerText === "Show older") {
	uuid = getIdFromThumbnail($("img.thumbnail").eq(-1));
	direction = "older";
    } else {
	console.warn("Unknown .show-more text");
	return;
    }
    $.getJSON("/_show_more", {
	uuid: uuid,
	direction: direction,
	filter: window.location.search
    }, function (payload) {
	loadPhotosFromDate(payload["date"]);
    });
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

// Scroll thumbnails while looking at a photo
$("#view .forward3, #view .back3").click(function (e) {
    var direction = e.target.parentElement.className;
    var filmstrip = $("#view .filmstrip");
    $.getJSON("/_scroll_thumbnails", {
	uuid: getPhotoId(),
	filter: window.location.search,
	count: direction === "forward3" ? 3 : -3
    }, function (thumbnails) {
	if ((thumbnails || []).length) {
	    // Replace current thumbnails and append new, with click handler
	    filmstrip.find("img.thumbnail").remove();
	    thumbnails.forEach(function (src) {
		var img = $("<img>").attr("class", "thumbnail").attr("src", "/" + src);
		img.click(showThumbnail);
		filmstrip.append(img);
	    });
	    // Move > and x to end of filmstrip
	    var forward3 = filmstrip.find(".forward3").detach();
	    filmstrip.append(forward3);
	    var close = filmstrip.find(".close").detach();
	    filmstrip.append(close);
	}
    });
});

function getPhotoId() {
    var filmstrip = $("#view .filmstrip");
    var thumbnail = filmstrip.find("img.thumbnail").eq(3);
    return getIdFromThumbnail(thumbnail);
}

function getIdFromThumbnail(thumbnail) {
    var uuid = thumbnail.attr("src").split("/").pop();
    return uuid.substring(0, uuid.indexOf("."));
}

// Clicking close on view page goes back previous main location
$("#view .close").click(function (e) {
    // https://developer.mozilla.org/en-US/docs/Web/API/Document/cookie
    var hash = document.cookie.replace(/(?:(?:^|.*;\s*)mainLocation\s*\=\s*([^;]*).*$)|^.*$/, "$1");
    var url = window.location.origin + "/" + window.location.search;
    if (hash) url += hash;
    window.location.href = url;
});

$("#view .description").click(function (e) {
    if (e.target.nodeName !== "INPUT") {
	var text = e.target.innerText;
	var input = $("<input>").attr("title", "Press Enter to save. Press Escape to abort.").keyup(saveDescription);
	if (text) input.val(text);
	$(e.target.parentElement).empty().append(input);
	input.focus();
    }
});

function saveDescription(e) {
    if (e.key === "Enter") {
	// Save description on photo
	$.getJSON("/_save_description", {
	    uuid: getPhotoId(),
	    description: e.target.value
	}, function (result) {
	    var node = $("<span>").text(result["description"]);
	    $(e.target.parentElement).empty().append(node);
	});
    } else if (e.key === "Escape") {
	// Reload page
	window.location.reload();
    }
}

$("#view .date").click(function () {
    function showMetaInfo(html) {
	$("#view").append($(html));
	$(".metainfo tr.more").toggle();
	$(".metainfo input.more").click(function () {
	    $(".metainfo tr.more").toggle();
	    this.value = this.value === "More" ? "Less" : "More";
	});
	$(".metainfo input.close").click(function () {
	    $(".metainfo").remove();
	});
    }

    $.get("/_get_metainfo", {uuid: getPhotoId()}, showMetaInfo, "html");
});

// Clicking add and remove on locations in config page
$("#config input.add").on("click", function (e) {
    var location = $("<div>").attr("class", "location");
    location.append($("<input>").attr("type", "text").attr("title", "Absolute path on disk").css("margin-right", "3px"));
    location.append($("<input>").attr("type", "text").attr("title", "Username. Use 'public' for shared photos.").css("margin-right", "3px"));
    location.append($("<input>").attr("type", "button").attr("class", "remove").val("Remove").click(removeLocation));
    $(".locations").append(location);
    updateLocationRows();
});

$("#config input.remove").click(removeLocation);

function removeLocation(e) {
    $(e.target.parentElement).remove();
    updateLocationRows();
}

function updateLocationRows() {
    $("#config .location").each(function (index, row) {
	$(row).find("input").eq(0).attr("name", "location" + Number(index + 1));
	$(row).find("input").eq(1).attr("name", "user" + Number(index + 1));
    });
}

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
    progressTimer = window.setInterval(getProgress, 1000);
}

function stopProgressTimer() {
    window.clearInterval(progressTimer);
}

// Code to run after page has been loaded
$(function (e) {
    // If showing main page put focus in scrollable page content
    if ($("#main").length) {
	$(".page-content").focus();
    }

    // Create date tooltip from thumbnail path, but just on view page
    $("#view img.thumbnail").each(function () {
	parts = $(this).attr("src").split("/");
	var i = parts.length - 2;
	var title = [parts[i - 2], parts[i - 1], parts[i]].join("-");
	$(this).attr("title", title);
    });
});
