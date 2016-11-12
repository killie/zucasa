
// Open/close branches in sidebar on click
$(".sidebar li a").click(function (e) {
    $(e.target.parentElement).toggleClass("collapsed").toggleClass("expanded");
});

// Open photo when clicking thumbnail
$("img.thumbnail").click(function (e) {
    var src = e.target.src;
    var url = src.substring(0, src.length - 4);
    window.location.href = url.replace("/static/import/photos", "");
});

// Show original when clicking zoom on photo
$("div.zoom").click(function (e) {
    var src = $(e.target.parentElement).css("background-image");
    src = src.replace('url("', '').replace('")', '');
    window.location.href = src;
});

// Clicking close on view page goes back to /<user>
$("#view .close").click(function (e) {
    var url = window.location.href;
    window.location.href = url.substring(0, url.length - 16);
});
