
// Open/close branches in sidebar on click
$(".sidebar li a").click(function (e) {
    $(e.target.parentElement).toggleClass("collapsed").toggleClass("expanded");
});

// Open details page when clicking thumbnail
$(".page-content img").click(function (e) {
    console.debug(e.target.src);
});
