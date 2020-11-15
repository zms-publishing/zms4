// Search API

function GetSearchBaseUrl() {
  var baseurl = self.location.href;
  baseurl = baseurl.substr(0,baseurl.indexOf('/content/'))+'/content/';
  return baseurl;
}

/**
 * Highlight all occurences of given text.
 */
function htmlReplace($context, exp, newvalue) {
	var regexp = new RegExp(exp, "gi");
	$('*',$context)
		.addBack()
		.contents()
		.filter(function(){
			return this.nodeType === 3;
		})
		.filter(function(){
			// Only match when contains 'simple string' anywhere in the text
			return this.nodeValue.match(regexp);
		})
		.each(function(){
			// Do something with this.nodeValue
			try {
				var raw = $(this).parent().html().split("<");
				var html = raw[0].replace( regexp, newvalue);
				for (var i = 1; i < raw.length; i++) {
					var j = raw[i].indexOf(">");
					html += "<";
					if (j<0) {
						html = html
							+ raw[i].replace( regexp, newvalue);
					}
					else {
						html = html
							+ raw[i].substr(0,j+1)
							+ raw[i].substr(j+1).replace( regexp, newvalue);
					}
				}
				$(this).parent().html(html);
			} catch (e) {}
		});
}

/**
 * Get url-parameter.
 *
 * @sParam the name of the parameter
 * @sDefault the default-value
 */
function GetURLParameter(sParam, sDefault) {
  var sPageURL = window.location.search.substring(1);
  var sURLVariables = sPageURL.split('&');
  for (var i = 0; i < sURLVariables.length; i++) {
    var sParameterName = sURLVariables[i].split('=');
    if (sParameterName[0] == sParam) {
      var parameterValue = sParameterName[1]
            .replace(/\+/gi,' ')
            .replace(/%23/gi,'#')
            .replace(/%24/gi,'$')
            .replace(/%26/gi,'&')
            .replace(/%2B/gi,'+')
            .replace(/%2C/gi,',')
            .replace(/%2F/gi,'/')
            .replace(/%3A/gi,':')
            .replace(/%3B/gi,';')
            .replace(/%3F/gi,'?');
      try {
        return decodeURI(parameterValue);
      }
      catch (e) {
        return parameterValue;
      }
    }
  }
  return sDefault;
}

/**
 * Assemble url-parameters:
 *
 * add parameters from dict to url (overwrite existing values).
 * @param url the url
 * @param d the dictionary of parameters to be added to the url.
 */
function AssembleUrlParameter(url,d) {
  if (url.indexOf("?") > 0) {
    var sPageURL = url.substr(url.indexOf("?")+1);
    var sURLVariables = sPageURL.split('&');
    for (var i = 0; i < sURLVariables.length; i++) {
      var sURLVariable = sURLVariables[i].split('=');
      var sParameterName = sURLVariable[0];
      var sParameterValue = sURLVariable[1];
      if (typeof d[sParameterName]=="undefined") {
        d[sParameterName] = sParameterValue;
      }
    }
    url = url.substr(0,url.indexOf("?"));
  }
  var dl = "?";
  for (var sParameterName in d) {
    url += dl + sParameterName + "=" + d[sParameterName];
    dl = "&";
  } 
  return url;
}

/**
 * Get pagination.
 *
 * @param fn the function to assemble url for page-index.
 * @param size the total number of records.
 * @param pageSize the number of records on each page.
 * @param pageIndex the index of the current-page.
 */
function GetPagination(fn, size, pageSize, pageIndex) {
  var html = '';
  if (size > pageSize) {
    var pageCount = Math.floor(((size-1)/pageSize)+1);
    html += ''
      + '<ul class="pagination">';
    html += ''
      + '<li class="'+(pageIndex==0?"disabled":"")+'">'
      + '<a href="'+(pageIndex==0?'javascript:;':fn(pageIndex-1))+'"><span class="glyphicon glyphicon-chevron-left"></span></a>'
      + '</li>';
    for (var page = 0; page < pageCount; page++) {
      if (pageCount>=10 && page==pageCount-1 && pageIndex<pageCount-(3+1)-1) {
        html += '<li class="disabled"><span>...</span></li>';
      }
      if (pageCount<10 || (page==0) || (page>=pageIndex-3 && page<=pageIndex+3) || (page==pageCount-1)) {
        html += ''
          + '<li class="' + (pageIndex==page?"active":"") + '">'
          + '<a href="'+(pageIndex==page?'javascript:;':fn(page))+'">'+(page+1)+'</a>'
          + '</li>';
      }
      if (pageCount>=10 && page==0 && pageIndex>(3+1)) {
        html += '<li class="disabled"><span>...</span></li>';
      } 
    }
    html += ''
      + '<li class="last' + (pageIndex==pageCount-1?" disabled":"") + '">'
      + '<a href="'+(pageIndex==pageCount-1?'javascript:;':fn(pageIndex+1))+'"><span class="glyphicon glyphicon-chevron-right"></span></a>'
      + '</li>'
      + '</ul><!-- .pagination -->';
  }
  $(".pagination").replaceWith(html);
}

$(function() {

// ********** ZOOM img for ZMSGraphic **********
var src = zmiParams.base_url;
src = src.substr(0,src.lastIndexOf("/"));
src = src + "/common/js/images/zoomImg.png";
$('div.graphic>a.fancybox>img.img').after('<div class="zoomImg"><img src="'+src+'" /></div>');

// ********** ZMSTable for Bootstrap **********
$('.ZMSTable').addClass('table table-striped');

// ********** ZMS plugins **********
if (typeof zmiParams['ZMS_HIGHLIGHT'] != 'undefined' && typeof zmiParams[zmiParams['ZMS_HIGHLIGHT']] != 'undefined') {
	$.plugin('zmi_highlight',{
		files: ['/++resource++zms_/jquery/plugin/jquery.plugin.zmi_highlight.js']
		});
	$.plugin('zmi_highlight').get('body',function(){});
}

});// ~~~eo document.ready function~~~
