
// Open/close branches in sidebar on click
$(".sidebar li a").click(function (e) {
    $(e.target.parentElement).toggleClass("collapsed").toggleClass("expanded");
});

// Open photo when clicking thumbnail
$("img.thumbnail").click(function (e) {
    var src = e.target.src;
    var url = src.substring(0, src.length - 4);
    url = url.replace("/static/import", "");
    window.location.href = url;
});
