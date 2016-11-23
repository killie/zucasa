
// Open/close branches in sidebar on click
$(".sidebar li a").click(function (e) {
    $(e.target.parentElement).toggleClass("collapsed").toggleClass("expanded");
});

// Open photo when clicking thumbnail
$("img.thumbnail").click(function (e) {
    openThumbnail(e.target.src);
});

// Show original when clicking zoom on photo
$(".photo .zoom").click(function (e) {
    var src = $(e.target.parentElement).css("background-image");
    src = src.replace('url("', '').replace('")', '');
    window.location.href = src;
});

$(".photo .prev").click(function (e) {
    openThumbnail(getThumbnailUrl(2));
});

$(".photo .next").click(function (e) {
    openThumbnail(getThumbnailUrl(4));
});

// Clicking close on view page goes back to /<user>
$("#view .close").click(function (e) {
    var url = window.location.href;
    window.location.href = url.substring(0, url.length - 16);
});

function getThumbnailUrl(index) {
    return $("img.thumbnail").eq(index).attr("src");
}

function openThumbnail(url) {
    // Remove extension, but it can be more than 3 chars
    var href = url.substring(0, url.length - 4);
    window.location.href = href.replace("/static/import/photos", "");
}

// Clicking cancel on config page goes to previous page
$("#config .cancel").click(function (e) {
    if (window.history.length) {
	window.history.back();
    }
});
