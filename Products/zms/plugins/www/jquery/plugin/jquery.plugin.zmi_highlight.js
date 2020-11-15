// ############################################################################
// ### Highlight
// ############################################################################

/**
 * Scroll to given element.
 * 
 * @see http://radio.javaranch.com/pascarello/2005/01/09/1105293729000.html
 */
function zmiScrollToElement(theElement) {
	var selectedPosX = 0;
	var selectedPosY = 0;
	while(theElement != null){
		selectedPosX += theElement.offsetLeft;
		selectedPosY += theElement.offsetTop;
		theElement = theElement.offsetParent;
	}
	window.scrollTo(selectedPosX,selectedPosY);
}

// escape by Colin Snover
// Note: if you don't care for (), you can remove it..
RegExp.escape = function(text) {
	return text.replace(/[-[\]{}()*+?.,\\^$|#\s]/g, "\\$&");
}

/**
 * Highlight all occurences of given text.
 * 
 * @see http://stackoverflow.com/questions/3241169/highlight-search-terms-select-only-leaf-nodes
 */
function htmlReplace($context, exp, newvalue, newoptions, parentsfilter) {
	newoptions = (typeof newoptions == "undefined" || newoptions == "") ? "gi" : newoptions;
	parentsfilter = (typeof parentsfilter == "undefined" || parentsfilter == "") ? "" : "," + parentsfilter;
	newvalue = newvalue.replace(/class="(.*?)"/i, 'class="$1 nohighlight"');
	console.log(exp + "," + newoptions + "==>" + newvalue);
	var regexp = new RegExp(exp, newoptions);
	$('*', $context).addBack().contents().filter(function() {
		// nodyType=3 (Text) Represents textual content in an element or attribute
		return this.nodeType === 3;
	}).filter(function() {
		// Only match when contains 'simple string' anywhere in the text
		return this.nodeValue.match(regexp);
	}).each(
			function(i, el) {
				// Do something with this.nodeValue
				if ($(el).parents(".nohighlight,input,option,select,textarea" + parentsfilter).length == 0) {
					var data = el.data;
					if (data = data.replace(regexp, newvalue)) {
						var wrapper = $("<span>").html(data);
						$(el).before(wrapper.contents()).remove();
					}
				}
			});
}

/**
 * Init highlight.
 */
function zmiInitHighlight(s) {
	var $context = $("body");
	var newvalue = '<span class=\"highlight\">$1</span>';
	var raw = s.split(" ");
	var text1st = null;
	for (var i = 0; i < raw.length; i++) {
		var text = raw[i].basicTrim();
		if (text.length > 0) {
			if (text1st == null) {
				text1st = text;
			}
			htmlReplace( $context, "("+text+")", newvalue);
		}
	}
	if (text1st!=null) {
		var spans_highlight = $('span.highlight');
		if ( spans_highlight.length>0) {
			zmiScrollToElement(spans_highlight[0]);
		}
	}
}


$(function() {
	try {
		zmiInitHighlight(zmiParams[zmiParams['ZMS_HIGHLIGHT']]);
	}
	catch (e) {
		// do nothing
	}
});

// ############################################################################
