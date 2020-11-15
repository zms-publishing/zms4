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
            .replace(/%3D/gi,'=')
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
      + '<nav aria-label="Page navigation">'
      + '<ul class="pagination">';
    html += ''
      + '<li class="page-item '+(pageIndex==0?"disabled":"")+'">'
      + '<a class="page-link" href="'+(pageIndex==0?'javascript:;':fn(pageIndex-1))+'">'+$ZMI.icon('fa fa-chevron-left icon-chevron-left')+'</span></a>'
      + '</li>';
    for (var page = 0; page < pageCount; page++) {
      if (pageCount>=10 && page==pageCount-1 && pageIndex<pageCount-(3+1)-1) {
        html += '<li class="page-item disabled"><span>...</span></li>';
      }
      if (pageCount<10 || (page==0) || (page>=pageIndex-3 && page<=pageIndex+3) || (page==pageCount-1)) {
        html += ''
          + '<li class="page-item ' + (pageIndex==page?"active":"") + '">'
          + '<a class="page-link" href="'+(pageIndex==page?'javascript:;':fn(page))+'">'+(page+1)+'</a>'
          + '</li>';
      }
      if (pageCount>=10 && page==0 && pageIndex>(3+1)) {
        html += '<li class="page-item disabled"><span>...</span></li>';
      } 
    }
    html += ''
      + '<li class="page-item last' + (pageIndex==pageCount-1?" disabled":"") + '">'
      + '<a  class="page-link" href="'+(pageIndex==pageCount-1?'javascript:;':fn(pageIndex+1))+'">'+$ZMI.icon('fa fa-chevron-right icon-chevron-right')+'</a>'
      + '</li>'
      + '</ul>'
      + '</nav><!-- .pagination -->';
  }
  $(".pagination").replaceWith(html);
}

function zmiBodyContentSearch(q,pageSize,pageIndex) {
		if (q.length==0) {
			return;
		}
		var zmi = document.location.toString().indexOf('/manage') > 0;
		$("#search_results").show();
		$("input[name=search]").val(q).change();
		$(".line.row:first").html('');
		$(".line.row:gt(0)").remove();
		var p = {};
		p['q'] = q;
		p['hl.fragsize'] = 200;
		p['hl.simple.pre'] = '<span class="highlight">';
		p['hl.simple.post'] = '</span>';
		p['page_size'] = pageSize;
		p['page_index'] = pageIndex;
		var fq = [];
		if (zmi) {
			var home_id = $ZMI.getPhysicalPath();
			home_id = home_id.substr(0,home_id.indexOf('/content'));
			home_id = home_id.substr(home_id.lastIndexOf('/')+1);
			fq.push('home_id_s:'+home_id);
		}
		p['fq'] = fq;
		var baseurl = $('meta[name=physical_path]').attr('content');
		if (typeof baseurl == "undefined") {
			try {
				baseurl = zmiParams['base_url'];
			} catch(e) {
				console.log(e);
				baseurl = window.location['pathname'];
			}
		}
		if (baseurl.indexOf("/content")>0) {
			baseurl = baseurl.substr(0,baseurl.indexOf("/content")+"/content".length);
		}
		var adapter = $ZMI.getConfProperty('zms.search.adapter.id','zcatalog_adapter');
		var connector = $ZMI.getConfProperty('zms.search.connector.id','zcatalog_connector');
		var url = baseurl+'/'+adapter+'/'+connector+'/search_xml';
    $.ajax({
      url:url,
      data:p,
      timeout:5000,
      error: function (xhr, ajaxOptions, thrownError) {
          $("#search_results .small-head").html(''
            + getZMILangStr('CAPTION_ERROR')+'<hr/> '
            + '<code>' + xhr.status + ': ' + thrownError + '</code>');
      },
      success:function(xmlDoc) {
        var $xml = $(xmlDoc);
        var $response = $("result[name=response]",$xml);
        var total = 0;
        var status = parseInt($("lst[name=responseHeader] > int[name=status]",$xml).text());
        var message = "Status: "+status;
        var html = "";
        if (status != 0) {
          $("#search_results .small-head").html(getZMILangStr('SEARCH_YOURQUERY').replace('%s','<span id="q"></span>')+' '+message);
          $("#search_results .small-head #q").text(q);
        }
        else {
          total = parseInt($response.attr("numFound"));
          if (total == 0) {
            $("#search_results .small-head").html(getZMILangStr('SEARCH_YOURQUERY').replace('%s','<span id="q"></span>')+' '+getZMILangStr('SEARCH_NORESULTS'));
            $("#search_results .small-head #q").text(q);
          }
          else {
            $("#search_results .small-head").html(getZMILangStr('SEARCH_YOURQUERY').replace('%s','<span id="q"></span>')+' '+getZMILangStr('SEARCH_RETURNEDRESULTS')+':');
            $("#search_results .small-head #q").text(q);
            var $docs = $("doc",$response);
            var $highlighting = $("lst[name=highlighting]",$xml);
            for (var c = 0; c < $docs.length; c++) {
              var $doc = $($docs[c]);
              function getattr(name) {
                return $("str[name="+name+"]",$doc).text()+$("arr[name="+name+"]>str",$doc).text();
              }
              var did = getattr("id");
              var meta_id = getattr("meta_id");
              var href = '';
              if (zmi) {
                if (href=='') href = getattr("loc");
                if (href=='') href = getattr("absolute_url");
                href += '/manage';
              } else {
                href = getattr("index_html");
              }
              var title = getattr("title");
              var snippet = getattr("standard_html");
              var custom = getattr("custom");
              if (snippet.length > p['hl.fragsize']) {
                snippet = snippet.substr(0,p['hl.fragsize']);
                while (!snippet.lastIndexOf(" ")==snippet.length-1) {
                  snippet = snippet.substr(0,snippet.length-2);
                }
              }
              var $hl = $("lst[name="+did+"]",$highlighting);
              var str = getattr("title");
              if (typeof str != "undefined" && str.length > 0) {
                title = str.replace(/&lt;/gi,'<').replace(/&gt;/gi,'>');
              }
              var str = getattr("body");
              if (typeof str != "undefined" && str.length > 0) {
                snippet = str.replace(/&lt;/gi,'<').replace(/&gt;/gi,'>');
              }
              var breadcrumb = '';
              if (typeof custom != "undefined" && custom.length > 0) {
                var $custom = $("<xml>"+custom+"<xml>");
                $("custom>breadcrumbs>breadcrumb",$custom).each(function() {
                  var title = $(">title",this).text();
                  var loc;
                  if (zmi) {
                    loc = $(">loc",this).text()+"/manage";
                  } else {
                    loc = $(">index_html",this).text();
                  }
                  breadcrumb += '<li class="breadcrumb-item"><a href="'+loc+'">'+title+'</a></li>';
                });
              }
              html += ''
                + '<div class="line row'+(c%2==0?" gray":"")+'">'
                + '<div class="col-sm-12">'
                + '<h2 class="'+meta_id+'"><a href="'+href+'">'+title+'</a></h2>'
                + (breadcrumb.length==0?'':'<nav aria-label="breadcrumb"><ol class="breadcrumb">'+breadcrumb+'</ol></nav><!-- .breadcrumb -->')
                + '<p>'+snippet+'</p>'
                + '</div>'
                + '</div><!-- .line.row -->';
            }
            
            // Pagination
            var fn = function(pageIndex) {
              var url = window.location.href;
              return AssembleUrlParameter(url,{"pageIndex:int":pageIndex});
            }
            GetPagination(fn,total,pageSize,pageIndex);
          }
        }
        $(".line.row:first").replaceWith(html);
        // Callback: Done
        if (typeof zmiBodyContentSearchDone == 'function') {
          zmiBodyContentSearchDone();
        }
      }});
    return false;
}

$(function() {
    var q = GetURLParameter("search","").trim();
    var pageSize = 10;
    var pageIndex = parseInt(GetURLParameter('pageIndex:int','0'));
    return zmiBodyContentSearch(q,pageSize,pageIndex);
  });
