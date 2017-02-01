
var progressTimer;

// Check if a date section was clicked in sidebar
window.onhashchange = function (e) {
    var hash = e.newURL.substring(e.newURL.indexOf("#")), section;
    if (hash.length < 9) return;
    section = $(hash);
    if (section.length == 0) {
	// Section was not found, load from server given date from hash
	saveDatesSidebar();
	loadPhotosFromDate(hash.substring(1));
    }
};

function saveDatesSidebar() {
    // Collect all open years and months and store them in browser db
    var expanded = {};
    var sidebar = $("#main .sidebar");
    sidebar.find(".dates > ul > li.expanded > a").each(function () {
	var year = this.innerText;
	expanded[year] = {};
	$(this.nextElementSibling).find("> li.expanded > a").each(function () {
	    var month = this.innerText;
	    expanded[year][month] = true;
	});
    });
    localStorage.setItem("expanded", JSON.stringify(expanded));
}

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
$("#main img.thumbnail, #view img.thumbnail").click(showThumbnail);

function showThumbnail(event) {
    // Remember hash on main location for 30 minutes, for use when pressing close from view page
    if ($("body#main").length) {
	document.cookie = "mainLocation=" + document.location.hash + "; max-age=60*30;";
    }
    openThumbnail(event.target.src);
}

function getThumbnailUrl(direction) {
    var thumbnails = $("img.thumbnail"), uuid = getPhotoId(), thumbnail;
    for (var i = 0; i < thumbnails.length; i++) {
	if ($(thumbnails[i]).attr("id") === uuid) {
	    if ($(thumbnails[i + direction])) {
		return $(thumbnails[i + direction]).attr("src");
	    }
	}
    }
    return "";
}

function openThumbnail(url) {
    if (!url) return;
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
    showPhoto();
});

function showPhoto(uuid, source) {
    var args = {uuid: uuid || getPhotoId()};
    if (source) args["source"] = source;
    $.getJSON("/_show_photo", args, function (data) {
	window.location.href = "/" + data.src;
    });
}

// Show prev photo when clicking < on photo
$(".photo .prev").click(function (e) {
    openThumbnail(getThumbnailUrl(-1));
});

// Show next photo when clicking > on photo
$(".photo .next").click(function (e) {
    openThumbnail(getThumbnailUrl(1));
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
    return $("div.photo").attr("id");
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

$("#view .edit-description, #view .description").click(function (e) {
    if (e.target.nodeName !== "INPUT") {
	var text = $("#view .description").text();
	var input = $("<input>").attr("title", "Press Enter to save. Press Escape to abort.").keyup(saveDescription);
	if (text) input.val(text);
	$("#view .description").empty().append(input);
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
	$("#view .metainfo").empty().append($(html)).show();
	$(".metainfo tr.more").toggle();
	$(".metainfo input.more").click(function () {
	    $(".metainfo tr.more").toggle();
	    this.value = this.value === "More" ? "Less" : "More";
	});
	$(".metainfo input.close").click(function () {
	    $(".sidebar.metainfo").empty().hide();
	});
    }

    $.get("/_get_metainfo", {uuid: getPhotoId()}, showMetaInfo, "html");
});

$("#view .tags-icon").click(showTagsSidebar);

function showTagsSidebar() {
    function showTags(html) {
	$("#view .tags").empty().append($(html)).show();
	$("#view #addTag").click(function (e) {
	    addTag(getPhotoId(), $("#view #tagName").val());
	    showTagsSidebar();
	});
	$("#view .tags input[type=checkbox]").click(function (e) {
	    if (this.checked) addTag(getPhotoId(), this.value);
	    else removeTag(getPhotoId(), this.value);
	    showTagsSidebar();
	});
	$("#view .tags input.close").click(function () {
	    $(".sidebar.tags").empty().hide();
	});
    }

    $.get("/_get_tags", {uuid: getPhotoId()}, showTags, "html");
}

function addTag(uuid, tag) {
    $.getJSON("/_add_tag", {
	uuid: uuid,
	tag: tag
    }, function (data) {
	console.debug(data);
    });
}

function removeTag(uuid, tag) {
    $.getJSON("/_remove_tag", {
	uuid: uuid,
	tag: tag
    }, function (data) {
	console.debug(data);
    });
}

$("#view .star").click(function (e) {
    var icon = e.currentTarget.firstElementChild;
    $.getJSON("/_toggle_star", {
	uuid: getPhotoId()
    }, function (data) {
	if (data.starred) {
	    $(icon).addClass("fa-star").removeClass("fa-star-o");
	} else {
	    $(icon).addClass("fa-star-o").removeClass("fa-star");
	}
    });
});

$("#view .remove").click(function (e) {
    $.getJSON("/_remove_photo", {
	uuid: getPhotoId()
    }, function (data) {
	// Open next or prev thumbnail, if not exists then return to main
	var thumbnails = $("img.thumbnail");
	if (thumbnails.length > 1) {
	    openThumbnail(getThumbnailUrl(1));
	} else {
	    console.debug("Go to main page");
	}
    });
});

// Clicking recover on removed photo adds photo back into gallery
function recoverPhoto(e) {
    var table = $(e.currentTarget).closest("table");
    $.getJSON("/_recover_photo", {
	uuid: table.attr("id")
    }, function (data) {
	if (data.success) {
	    table.remove();
	} else {
	    console.warn(data.message || "Could not recover photo");
	}
    });
}

// Clicking on removed thumbnail shows original directly
function viewRemovedPhoto(e) {
    var table = $(e.currentTarget).closest("table");
    showPhoto(table.attr("id"), "removed");
}

// Clicking import or settings toggles form
$("#settings nav .import, #settings nav .prefs").click(function (e) {
    $("#settings nav li").removeClass("selected");
    var li = $(e.currentTarget);
    li.addClass("selected");
    emptySettingsPage();
    if (li.hasClass("import")) {
	$("#settings .container .import").show();
    } else if (li.hasClass("prefs")) {
	$("#settings .container .prefs").show();
    }
});

function emptySettingsPage() {
    $("#settings .container > form").hide();
    $("#settings .container > div").remove();
}

// Clicking removed photos on settings page
$("#settings nav .removed").click(function () {
    function showRemoved(html) {
	$("#settings .container").append($(html));
	$("#removed .recover").click(recoverPhoto);
	$("#removed img.thumbnail").click(viewRemovedPhoto);
    }

    $("#settings nav li").removeClass("selected");
    $("#settings nav li.removed").addClass("selected");
    emptySettingsPage();
    $.get("/_get_removed", {}, showRemoved, "html");
});

// Clicking add and remove on locations in settings page
$("#settings input.add").click(function (e) {
    var location = $("<div>").attr("class", "location");
    location.append($("<input>").attr("type", "text").attr("placeholder", "Path").attr("title", "Absolute path on disk").css("margin-right", "3px"));
    location.append($("<input>").attr("type", "text").attr("placeholder", "User").attr("title", "Username. Use 'public' for shared photos.").css("margin-right", "3px"));
    location.append($("<input>").attr("type", "button").attr("class", "remove").val("Remove").click(removeLocation));
    $(".locations").append(location);
    updateLocationRows();
});

$("#settings input.remove").click(removeLocation);

function removeLocation(e) {
    $(e.target.parentElement).remove();
    updateLocationRows();
}

function updateLocationRows() {
    $("#settings .location").each(function (index, row) {
	$(row).find("input").eq(0).attr("name", "location" + Number(index + 1));
	$(row).find("input").eq(1).attr("name", "user" + Number(index + 1));
    });
}

// Clicking tags on settings page
$("#settings nav .tags").click(showTagEdit);

function showTagEdit() {
    function showAllTags(html) {
	$("#settings .container").append($(html));
	$("#settings ul.tag-list .count").click(showAllPhotosWithTag);
	$("#settings ul.tag-list .rename").click(renameAllTagsByName);
	$("#settings ul.tag-list .remove").click(removeAllTagsByName);
    }

    $("#settings nav li").removeClass("selected");
    $("#settings nav li.tags").addClass("selected");
    emptySettingsPage();
    $.get("/_get_all_tags", {}, showAllTags, "html");
}

function showAllPhotosWithTag(e) {
    var name = $(e.target).closest("li").attr("name");
    var href = document.location.origin + "?tags=" + encodeURIComponent(name);
    window.location.href = href;
}

function renameAllTagsByName(e) {
    var oldName = $(e.target).closest("li").attr("name");
    var newName = $(e.target).closest("li").find("input.name").val();
    if (oldName.trim() === newName.trim()) return;
    $.getJSON("/_rename_all_tags", {oldName: oldName, newName: newName}, function (result) {
	if (result.success) {
	    showTagEdit();
	} else {
	    console.warn(result);
	}
    });
}

function removeAllTagsByName(e) {
    var name = $(e.target).closest("li").attr("name");
    console.debug("remove all", name);
}

// Clicking back goes to previous page
$("input.back").click(function (e) {
    if (window.history.length > 1) {
	window.history.back();
    } else {
	window.location.href = window.location.origin;
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

function updateDatesSidebar(expanded) {
    if (!expanded) return;
    var sidebar = $("#main .sidebar");
    sidebar.find(".dates > ul > li > a").each(function () {
	var year = this.innerText;
	if (expanded.hasOwnProperty(year)) {
	    $(this.parentElement).addClass("expanded").removeClass("collapsed");
	    $(this.nextElementSibling).find("> li > a").each(function () {
		var month = this.innerText;
		if (expanded[year].hasOwnProperty(month)) {
		    $(this.parentElement).addClass("expanded").removeClass("collapsed");
		}
	    });
	} else {
	    $(this.parentElement).removeClass("expanded").addClass("collapsed");
	}
    });
}

// Code to run after page has been loaded
$(function (e) {
    // If showing main page put focus in scrollable page content and update dates sidebar
    if ($("#main").length) {
	updateDatesSidebar(JSON.parse(localStorage.getItem("expanded")));
	$(".page-content").focus();
    }

    // Create date tooltip from thumbnail path, but just on view page
    $("#view img.thumbnail").each(function () {
	parts = $(this).attr("src").split("/");
	var i = parts.length - 2;
	var title = [parts[i - 2], parts[i - 1], parts[i]].join("-");
	$(this).attr("title", title);
    });

    $(document).keypress(function (e) {
	if ($("body#view").length > 0) {
	    if (e.originalEvent.key === "ArrowLeft") {
		openThumbnail(getThumbnailUrl(-1));
	    } else if (e.originalEvent.key === "ArrowRight") {
		openThumbnail(getThumbnailUrl(1));
	    }
	}
    });
});
