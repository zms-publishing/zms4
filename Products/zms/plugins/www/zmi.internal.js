// /////////////////////////////////////////////////////////////////////////////
//  Auth
// /////////////////////////////////////////////////////////////////////////////

/**
 * Force change password.
 */
ZMI.prototype.forceChangePassword = function() {
	$("a#manage_userForm").click();
	$(".modal-header .close").hide();
}

// /////////////////////////////////////////////////////////////////////////////
//  Dimensions
// /////////////////////////////////////////////////////////////////////////////

/**
 * Returns coordinates of given element
 */
ZMI.prototype.getCoords = function(theElement, thePosition) {
	var coords = {x: 0, y: 0};
	var element = theElement;
	while (element) {
		if (thePosition=="relative" && $(element).css("position")=="absolute") {
			break;
		}
		coords.x += element.offsetLeft;
		coords.y += element.offsetTop;
		element = element.offsetParent;
	}
	return coords;
}

// /////////////////////////////////////////////////////////////////////////////
//  Languages
// /////////////////////////////////////////////////////////////////////////////

/**
 * Get descendant languages.
 */
ZMI.prototype.getDescendantLanguages = function() {
	var base = self.location.href;
	if (base.indexOf('?') > 0) {
		base = base.substr(0,base.indexOf('?'));
	}
	base = base.substr(0,base.lastIndexOf('/'));
	var response = $.ajax({
		url: base+'/getDescendantLanguages',
		data:{id:getZMILang()},
		datatype:'text',
		async: false
		}).responseText;
	var langs = eval('('+response+')');
	if (langs.length > 1) {
		var labels = '';
		for ( var i = 0; i < langs.length; i++) {
			if (labels.length>0) {
				labels += ', ';
			}
			labels += $.ajax({
				url: 'getLanguageLabel',
				data:{id:langs[i]},
				datatype:'text',
				async: false
				}).responseText;
		}
		return ' '+getZMILangStr('MSG_CONFIRM_DESCENDANT_LANGS').replace("%s",langs);
	}
	return '';
}


// /////////////////////////////////////////////////////////////////////////////
//  RTE: Relative URLs.
// /////////////////////////////////////////////////////////////////////////////

/**
 * Relativate url.
 */
ZMI.prototype.getServerUrl = function(url) {
	if (url.startsWith("/") || url.startsWith(".")) {
		return "";
	}
	var protocol = url;
	protocol = protocol.substr(0,protocol.indexOf(":")+3);
	var server_url = url;
	server_url = server_url.substr(protocol.length);
	server_url = protocol + server_url.substr(0,server_url.indexOf("/"));
	return server_url;
}

/**
 * Relativate url.
 */
ZMI.prototype.relativateUrl = function(url,anchor,page_abs_url) {
	if (typeof page_abs_url == "undefined") {
		page_abs_url = $('meta[name="version_container_abs_url"]').attr('content');
	}
	var server_url = $ZMI.getServerUrl(url);
	var page_server_url = $ZMI.getServerUrl(page_abs_url);
	if (server_url.length > 0 && page_server_url.length > 0 && server_url != page_server_url) {
		return url;
	}
	var currntPath = page_abs_url.substr(page_server_url.length);
	var targetPath = url.substr(server_url.length);
	while ( currntPath.length > 0 && targetPath.length > 0) {
		var i = currntPath.indexOf( '/');
		var j = targetPath.indexOf( '/');
		if ( i < 0) {
			currntElmnt = currntPath;
		}
		else {
			currntElmnt = currntPath.substring( 0, i);
		}
		if ( j < 0) {
			targetElmnt = targetPath;
		}
		else {
			targetElmnt = targetPath.substring( 0, j);
		}
		if ( currntElmnt != targetElmnt) {
			break;
		}
		if ( i < 0) {
			currntPath = '';
		}
		else {
			currntPath = currntPath.substring( i + 1);
		}
		if ( j < 0) {
			targetPath = '';
		}
		else {
			targetPath = targetPath.substring( j + 1);
		}
	}
	while ( currntPath.length > 0) {
		var i = currntPath.indexOf( '/');
		if ( i < 0) {
			currntElmnt = currntPath;
			currntPath = '';
		}
		else {
			currntElmnt = currntPath.substring( 0, i);
			currntPath = currntPath.substring( i + 1);
		}
		targetPath = '../' + targetPath;
	}
	if (!targetPath.startsWith('/')) {
		url = './' + targetPath;
	}
	if (typeof anchor != 'undefined') {
		url += anchor;
	}
	return url;
}

/**
 * Relativate urls.
 */
ZMI.prototype.relativateUrls = function(html,page_abs_url) {
	if (typeof page_abs_url == "undefined") {
		page_abs_url = $('meta[name="version_container_abs_url"]').attr('content');
	}
	var splitTags = ['href="','src="'];
	for ( var h = 0; h < splitTags.length; h++) {
		var splitTag = splitTags[h];
		var vSplit = html.split(splitTag);
		var v = vSplit[0];
		for ( var i = 1; i < vSplit.length; i++) {
			var j = vSplit[i].indexOf('"');
			var url = vSplit[i].substring(0,j);
			if (url.indexOf("://")<0 && !url.startsWith("./")) {
				url = this.relativateUrl(url,'',page_abs_url);
			}
			v += splitTag + url + vSplit[i].substring(j);
		}
		html = v;
	}
	return html;
};