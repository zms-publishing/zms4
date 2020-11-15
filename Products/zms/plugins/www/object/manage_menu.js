/**
 * Select object.
 */
function zmiSelectObject(sender) {
	$(".zmi-sitemap .active").removeClass("active");
	$(sender).parents("li").addClass("active");
	window.parent.manage_main.location.href=$(sender).attr("href")+"/manage_main?lang="+getZMILang();
	return false;
}
function zmiRefresh() {
	var href = $ZMI.getPhysicalPath();
	try {
		href = window.parent.manage_main.$ZMI.getPhysicalPath();
	}
	catch(e) {
		console.log('zmiRefresh: cannot get physical-path from parent - ' + e);
	}
	$ZMI.objectTree.init(".zmi-sitemap",href,{params:{meta_types:$ZMI.getConfProperty('zms.plugins.www.object.manage_menu.meta_types','0,1,ZMSTrashcan')}});
}

// Leading Zeros
// https://gist.github.com/aemkei/1180489
function pad(a,b){
	return(1e15+a+"").slice(-b)
}

function zmiBookmarksChanged() {
	var data_root = $("body").attr('data-root');
	var key = "ZMS."+data_root+".bookmarks";
	var bookmarks = $ZMILocalStorageAPI.get(key,[]);
	var url = "ajaxGetNodes";
	var lang = getZMILang();
	var data = {lang:lang};
	for (var i = 0; i < bookmarks.length; i++) {
		data['ref'+i] = bookmarks[i];
	}
	$.ajax({
			url:url,data:data
		})
		.done(function(response) {
				var html = '';
				var i = 0;
				$("page",response).each(function() {
						var not_found = $(this).attr("not_found");
						if (typeof not_found=="undefined" || not_found!="1") {
							var titlealt = $(this).attr("titlealt");
							var absolute_url = $(this).attr("absolute_url");
							var icon = $(this).attr("display_icon");
							if (icon.indexOf('<')!=0) {
								icon = $ZMI.icon(icon);
							}
							if (i==0) {
								html += '<a href="javascript:;" class="dropdown-toggle" data-toggle="dropdown" title="Favoriten">';
								html += $ZMI.icon('far fa-bookmark')+' ';
								html += '<b class="caret"></b>';
								html += '</a>';
								html += '<div class="dropdown-menu" role="menu" aria-labelledby="dropdownMenu1">';
								html += '<div class="dropdown-header">'+$ZMI.icon('far fa-bookmark')+' Favoriten</div>';
							}
							html += ''
									+ '<a class="dropdown-item" href="'+absolute_url+'/manage_main?lang='+lang+'" target="manage_main"'
											+ ' onmouseover="$(\'.fa-clock.text-muted\').removeClass(\'text-muted\').addClass(\'text-danger\')"'
											+ ' onmouseout="$(\'.fa-clock.text-danger\').removeClass(\'text-danger\').addClass(\'text-muted\')"'
										+ '>'+icon+' '+titlealt+'</span> '
										+ '<span title="Favorit entfernen" data-path="'+bookmarks[i]+'"'
											+ '>'+$ZMI.icon('far fa-clock text-muted')+'</span>'
									+ '</a>';
							i++;
						}
					});
				if (i>0) {
					html += '</div><!-- .dropdown-menu --> ';
				}
				$("#zmi-bookmarks").html(html);
				$("#zmi-bookmarks .fa-clock.text-muted").click(function(event) {
						event.preventDefault();
						event.stopPropagation();
						var data_path = $(this).parent().attr('data-path');
						if(confirm(getZMILangStr('MSG_CONFIRM_DELOBJ'))){
							var index = bookmarks.indexOf(data_path);
							bookmarks.splice(index,1);
							$ZMILocalStorageAPI.replace(key,bookmarks);
							zmiBookmarksChanged();
						}
					});
			});
}

function zmiHistoryChanged() {
	var data_root = $("body").attr('data-root');
	var key = "ZMS."+data_root+".history";
	var history = $ZMILocalStorageAPI.get(key,[]);
	var url = "ajaxGetNodes";
	var lang = getZMILang();
	var data = {lang:lang};
	for (var i = 0; i < Math.min(history.length,10); i++) {
		data['ref'+i] = history[i];
	}
	$.ajax({
			url:url,data:data
		})
		.done(function(response) {
				var html = '';
				var i = 0;
				$("page",response).each(function() {
						var not_found = $(this).attr("not_found");
						if (typeof not_found=="undefined" || not_found!="1") {
							var titlealt = $(this).attr("titlealt");
							var absolute_url = $(this).attr("absolute_url");
							var icon = $(this).attr("zmi_icon");
							if (icon && icon.indexOf('<')!=0) {
								icon = $ZMI.icon(icon);
							}
							if (i==0) {
								html += '<a href="javascript:;" class="dropdown-toggle" data-toggle="dropdown" title="Verlauf">';
								html += $ZMI.icon('far fa-clock')+' ';
								html += '<b class="caret"></b>';
								html += '</a>';
								html += '<div class="dropdown-menu" role="menu" aria-labelledby="dropdownMenu1">';
								html += '<div class="dropdown-header">'+$ZMI.icon('far-fa-clock')+' Verlauf</div>';
							}
							html += '<a class="dropdown-item" href="'+absolute_url+'/manage_main?lang='+lang+'" target="manage_main">'+pad((i+1),2)+'. '+icon+' '+titlealt+'</a>';
							i++;
						}
					});
				if (i>0) {
					html += '</div><!-- .dropdown-menu --> ';
				}
				$("#zmi-history").html(html);
			});
}

function zmiResize(init) {
	var key = "ZMS.manage_menu.width";
	$(window).resize(function() {
			$ZMILocalStorageAPI.set(key,window.innerWidth);
		});
	var frmwidth = $ZMILocalStorageAPI.get(key,224);
	var frmset = parent.document.getElementsByTagName('frameset');
	var colval = frmwidth + ",*";
	try {
		frmset[0].cols=colval;
	} catch(err) {
		console.log(err)
	}
}

$(function(){
	zmiResize();
	zmiRefresh();
	zmiBookmarksChanged();
	zmiHistoryChanged();
});

