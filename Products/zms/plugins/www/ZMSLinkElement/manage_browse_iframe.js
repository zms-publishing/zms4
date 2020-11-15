/**
 * Select internal url.
 */
function zmiSelectObject(sender) {
	var parent = self.window.parent;
	var uid = $(sender).attr('data-uid');
	var selectedLang = zmiParams['selectedLang'];
	uid = uid.substr(0,uid.lastIndexOf('}'))+(typeof selectedLang=='undefined' || selectedLang==''?'':';lang='+selectedLang)+"}";
	var href = $(sender).attr('href');
	var titlealt = $(sender).attr('data-page-titlealt');
	console.log('zmiSelectObject: uid='+uid+'\nhref='+href+'\ntitlealt='+titlealt);
	var fm;
	var fmName = zmiParams['fmName']; 
	var elName = zmiParams['elName']; 
	if (typeof fmName != 'undefined' && fmName != '' && typeof elName != 'undefined' && elName != '') {
		fm = parent.document.forms[fmName];
	}
	if (fm) {
		parent.zmiBrowseObjsApplyUrlValue(fmName,elName,uid,titlealt);
	}
	else {
		parent.selectObject(href,titlealt,uid);
	}
	self.window.parent.zmiModal("hide");
}

/**
 * Select external url.
 */
function selectUrl(href) {
	var titlealt = '';
	console.log('selectUrl: href='+href+'\ntitlealt='+titlealt);
	var fm;
	var fmName = zmiParams['fmName']; 
	var elName = zmiParams['elName']; 
	if (typeof fmName != 'undefined' && fmName != '' && typeof elName != 'undefined' && elName != '') {
		fm = parent.document.forms[fmName];
	}
	if (fm) {
		parent.zmiBrowseObjsApplyUrlValue(fmName,elName,href);
	}
	else {
		self.window.parent.selectObject(href,titlealt);
	}
	self.window.parent.zmiModal("hide");
}

$(function(){
	$("button[name=btn]").click(function() {
			var type = $("select[name=type]").val();
			var url = $("input[name=url]").val();
			if (!url.indexOf(type)==0) {
				url = type + url;
			}
			selectUrl(url);
		});
	var physical_path = $('span[name=physical_path]').text();
	var href = physical_path;
	if (typeof href == "undefined" || href == "") {
		href = $ZMI.getPhysicalPath();
	}
	// filter
	var t = null;
	var search_results = $("#search_results").html();
	var applyListFilter = function() {
			var filter = $('input.filter').val().trim();
			var v = filter;
			if (v.length == 0) {
				$("#search_results").html(search_results).hide();
				$(".zmi-sitemap").show();
			}
			else {
				$("#search_results").html(search_results).show();
				$(".zmi-sitemap").hide();
				var pageSize = 10;
				var pageIndex = parseInt(GetURLParameter('pageIndex:int','0'));
				zmiBodyContentSearch(v,pageSize,pageIndex);
			}
		};
	$('input.filter').keyup(function(e) {
		var that = this;
		if (t != null) {
			clearTimeout(t);
		}
		t = setTimeout(applyListFilter, 500);
	});
	// sitemap
	$ZMI.objectTree.init(".zmi-sitemap",href,{});
});

var URLParser = (function (document) {
	var PROPS = 'protocol hostname host pathname port search hash href'.split(' ');
	var self = function (url) {
		this.aEl = document.createElement('a');
		this.parse(url);
	};
	self.prototype.parse = function (url) {
		this.aEl.href = url;
		if (this.aEl.host == "") {
			this.aEl.href = this.aEl.href;
		}
		PROPS.forEach(function (prop) {
			switch (prop) {
				case 'hash':
					this[prop] = this.aEl[prop].substr(1);
					break;
				default:
					this[prop] = this.aEl[prop];
			}
		}, this);
		if (this.pathname.indexOf('/') !== 0) {
			this.pathname = '/' + this.pathname;
		}
		this.requestUri = this.pathname + this.search;
	};
	self.prototype.toObj = function () {
		var obj = {};
		PROPS.forEach(function (prop) {
			obj[prop] = this[prop];
		}, this);
		obj.requestUri = this.requestUri;
		return obj;
	};
	self.prototype.toString = function () {
		return this.href;
	};
	return self;
})(document);

function zmiBodyContentSearchDone() {
	$("#search_results h4:first").hide();
	$(".zmi-filter .badge.badge-pill.badge-info").text($(".line.row").length);
	$(".line.row").each(function() {
			var $h2 = $("h2",this);
			var meta_id = $("h2").attr("class");
			var display_icon = $ZMI.display_icon(meta_id);
			var $a = $("a",$h2);
			$a.html(display_icon+' '+$a.html());
			var href = $a.attr("href");
			if (href.lastIndexOf(".html")>href.lastIndexOf("/")) {
				href = href.substr(0,href.lastIndexOf("/"));
			}
			var parser = new URLParser();
			parser.parse(href);
			var url = parser.toObj();
			var titlealt = $a.text();
			$a.attr({
					'href':url['href'],
					'data-page-titlealt':titlealt
					})
				.click(function() {
						var phys_path = $(this).attr('href');
						var result = $.ajax({
									url: phys_path.replace('/manage','/ajaxGetNode'),
									data: {'get_attrs:int':0},
									contentType:'text/xml;charset=UTF-8',
									async: false
									}).responseText;
						var $resultXML = $.parseXML(result);
						var uid = $('page',$resultXML).attr('uid');
						$(this).attr('data-uid',uid);
						return zmiSelectObject(this);
					});
		});
}