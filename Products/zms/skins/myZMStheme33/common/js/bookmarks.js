/**
 *  Individual Bookmarks based on HTML5 local-storage.
 *
 * @see http://fortuito.us/diveintohtml5/storage.html
 * @author Dirk Nordmann
 *
 * 22.01.2015 [1.0] Initial revision.
 */

function getBookmarks() {
	var l =  [];
	while (true) {
		var title = localStorage["site.bookmark." + l.length + ".title"];
		var href = localStorage["site.bookmark." + l.length + ".href"];
		if (typeof title == "undefined" || typeof href == "undefined") {
			break;
		}
		l.push({title:title,href:href});
	}
	return l;
}

function setBookmarks(l) {
	var i = 0;
	while (true) {
		var title = localStorage["site.bookmark." + i + ".title"];
		var href = localStorage["site.bookmark." + i + ".href"];
		if (typeof title == "undefined" && typeof href == "undefined") {
			break;
		}
		delete localStorage["site.bookmark." + i + ".title"];
		delete localStorage["site.bookmark." + i + ".href"];
		i++;
	}
	for (var i = 0; i < l.length; i++) {
		localStorage["site.bookmark." + i + ".title"] = l[i].title;
		localStorage["site.bookmark." + i + ".href"] = l[i].href;
	}
}

function initBookmarks() {
	var l = getBookmarks();
	for (var i = 0; i < l.length; i++) {
		$("#add-bookmark").after(''
				+ '<li>'
				+ '<a href="javascript:;" onclick="self.location.href=\''+l[i].href+'\'"'
				+ ' onmouseover="$(\'.fa-times\',this).removeClass(\'text-muted\').addClass(\'text-danger\')"'
				+ ' onmouseout="$(\'.fa-times\',this).removeClass(\'text-danger\').addClass(\'text-muted\')"'
				+ '><span class="fas fa-star text-primary"></span> '
				+ l[i].title + ' '
				+ '<span class="fas fa-times text-muted" title="Remove Favorite"'
				+ ' onclick="var event=arguments[0]||window.event;event.stopPropagation();if(confirm(\'Wollen Sie Favorit \\\''+l[i].title+'\\\' wirklich entfernen?\')){removeBookmark(\''+l[i].href+'\')};"'
				+ '></span>'
				+ '</a>'
				+ '</li>');
	}
}

function addBookmark() {
	var l = getBookmarks();
	var title = $("title").text();
	var href = window.location.href;
	l.push({title:title,href:href});
	setBookmarks(l);
	window.location.reload();
}

function removeBookmark(href) {
	var l = getBookmarks();
	for (var i = 0; i < l.length; i++) {
		if (l[i].href==href) {
			l.splice(i, 1);
			break;
		}
	}
	setBookmarks(l);
	window.location.reload();
}

$(function() {
	initBookmarks();
});