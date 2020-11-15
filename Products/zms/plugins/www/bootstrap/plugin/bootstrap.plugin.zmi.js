$ZMI.registerReady(function(){

	$ZMI.setCursorWait("BO bootstrap.plugin.zmi");

	var manage_menu = typeof window.parent.frames!="undefined"&&typeof window.parent.frames.manage_menu!="undefined";

	$("body").each(function() {
			var data_root = $(this).attr('data-root');
			var data_path = $(this).attr('data-path');
			if (typeof data_root != "undefined" && typeof data_path != "undefined") {
				// Bookmark
				if (manage_menu) {
					$("#zmi-tab .breadcrumb .active").each(function() {
							$(this).append(' <a href="javascript:;" title="Bookmark"><i class="fas fa-bookmark-empty text-muted"></a>');
							var key = "ZMS."+data_root+".bookmarks";
							var bookmarks = $ZMILocalStorageAPI.get(key,[]);
							$("a:last",this).click(function() {
									var index = bookmarks.indexOf(data_path);
									if (index >= 0) {
										bookmarks.splice(index,1);
										$('.fa-bookmark',this).removeClass("fa-bookmark text-primary").addClass("fa-bookmark-empty text-muted");
									}
									else {
										bookmarks.push(data_path);
										$('.fa-bookmark-empty',this).removeClass("fa-bookmark-empty text-muted").addClass("fa-bookmark text-primary");
									}
									$ZMILocalStorageAPI.replace(key,bookmarks);
									var frames = window.parent.frames;
									try {
									for (var i = 0; i < frames.length; i++) {
										if (frames[i] != window && typeof frames[i].zmiBookmarksChanged == "function") {
											frames[i].zmiBookmarksChanged();
										}
									}
									}
									catch (e) {
									}
								});
							var index = bookmarks.indexOf(data_path);
							if (index >= 0) {
								$('.fa-bookmark-empty',this).removeClass("fa-bookmark-empty text-muted").addClass("fa-bookmark text-primary");
							}
							else {
								$('.fa-bookmark',this).removeClass("fa-bookmark text-primary").addClass("fa-bookmark-empty text-muted");
							}
						});
				}
				// History
				var key = "ZMS."+data_root+".history";
				var history = $ZMILocalStorageAPI.get(key,[]);
				var index = history.indexOf(data_path);
				if (index >= 0) {
					history.splice(index,1);
				}
				history.splice(0,0,data_path);
				while (history.length > 10) {
					history.splice(history.length-1,1);
				}
				$ZMILocalStorageAPI.replace(key,history);
				var frames = window.parent.frames;
				try {
				for (var i = 0; i < frames.length; i++) {
					if (frames[i] != window && typeof frames[i].zmiHistoryChanged == "function") {
						frames[i].zmiHistoryChanged();
					}
				}
				}
				catch (e) {
				}
			}
		});

  var $change_dt = $(".zmi-change-dt,.zmi-created-dt");
  if ($change_dt.length > 0) {
    var fn = function() {
        $change_dt.each(function() {
          var $el = $(this);
          var mydate = $el.attr("title");
          if (typeof mydate=="undefined") {
            mydate = $el.text();
          }
          var myformat = getZMILangStr('DATETIME_FMT');
          var dtsplit=mydate.split(/[\/ .:]/);
          var dfsplit=myformat.split(/[\/ .:]/);
          // creates assoc array for date
          df = new Array();
          for(dc=0;dc<dtsplit.length;dc++) {
            df[dfsplit[dc]]=dtsplit[dc];
            df[dfsplit[dc].substr(1)]=parseInt(dtsplit[dc]);
          }
          var dstring = df['%Y']+'-'+df['%m']+'-'+df['%d']+' '+df['%H']+':'+df['%M']+':'+df['%S'];
          var date = new Date(df['Y'],df['m']-1,df['d']);
          var now = new Date();
          now.setHours(0,0,0);
          var daysBetween = (now.valueOf()-date.valueOf())/(24*60*60*1000);
          if (daysBetween<1) {
            date = new Date(df['Y'],df['m']-1,df['d'],df['H'],df['M'],df['S']);
            now = new Date();
            var secondsBetween = (now.valueOf()-date.valueOf())/(1000);
            var minutesBetween = secondsBetween/(60);
            $(this).text(getZMILangStr('TODAY')+" "+(minutesBetween<60?Math.floor(minutesBetween)+" min. ":df['%H']+':'+df['%M']));
          }
          else if (daysBetween<2) {
            $(this).text(getZMILangStr('YESTERDAY')+" "+df['%H']+':'+df['%M']);
          }
          else {
            $(this).text(getZMILangStr('DATE_FMT').replace('%Y',df['%Y']).replace('%m',df['%m']).replace('%d',df['%d']));
          }
        $(this).attr("title",mydate);
      });
      setTimeout(fn,10000);
    };
    fn();
  }

	// Toggle: Classical Sitemap Icon
	$('a#navbar-sitemap').each(function() {
		var $a = $(this);
		if (self.window.parent.frames.length > 1 && typeof self.window.parent != "undefined" && (self.window.parent.location+"").indexOf('dtpref_sitemap=1') > 0) {
			$a.attr('target','_top');
		}
		else {
			$a.attr('href',$a.attr('href')+'&dtpref_sitemap=1');
		}
	});

	// Toggle: Lang
	if (manage_menu) {
		$('.zmi header a.toggle-lang').each(function() {
				var $a = $(this);
				$a.attr('target','_top');
				$a.attr('href','manage?lang='+$a.attr('data-language') + '&dtpref_sitemap=1' + '&came_from='+$a.attr('href'));
			});
	}

	// Context-Sensitive Help On Labels
	$(".help").each(function() {
			$(this).hide();
			var data_for = $(this).attr("data-for");
			$("label[for="+data_for+"], label[for="+data_for+"_"+getZMILang()+"]").each(function() {
					$(this).append('<i class="fas fa-info-circle text-info ml-1" title="'+getZMILangStr('TAB_HELP')+'..." onclick="var evt=arguments[0]||window.event;evt.stopPropagation();zmiModal(\'div.help[data-for='+data_for+']\',{title:\''+getZMILangStr('TAB_HELP')+': '+$(this).text().trim()+'\'})"></i>');
				});
		});

	// Tooltip
	$('[data-toggle="tooltip"]').tooltip();

	// Main Menu Toggle
	$('.zmi .main-nav li.active a').click(function(event) {
		if ( $(window).width() < 767) {
			event.preventDefault();
			$('.zmi .main-nav li:not(.active)').toggle();
			return false;
		}
	});

  // Filters
  $(".collapse.filters").each(function() {
      var $body = $(this);
      var f = function() {
          // Ensure at least one empty filter (cloned from hidden prototype).
          var $hidden = $(".form-group.d-none",$body);
          var $other = $hidden.prevAll(".form-group");
          var $selects = $("select[name^='filterattr']",$other);
          var i = 0;
          var c = 0;
          $selects.each(function() {
              i++;
              if ($(this).val()=='') {
                if (i<$selects.length) {
                  $(this).parents(".form-group").remove();
                }
                c++;
              }
            });
          if (c==0) {
            var $cloned = $hidden.clone(true);
            $cloned.insertBefore($hidden).removeClass("d-none");
          }
          // Rename filters (ordered by DOM).
          var qfilters = 0;
          var d = {}
          $("*[name^='filter']",$body).each(function() {
              var nodeName = this.nodeName.toLowerCase();
              if (nodeName=='input' || nodeName=='select') {
                var name = $(this).attr("name").replace(/\d/gi,'');
                if (typeof d[name]=="undefined") {
                  d[name] = 0;
                }
                $(this).attr("name",name+d[name]);
                qfilters = d[name];
                d[name]++;
              }
            });
          $("input#qfilters").val(qfilters);
        };
      $("select[name^=filterattr]",$body).each(function() {
          var that = this;
          $(that).click(f).keyup(f);
        });
      f();
    });

  // Filters (ii)
  // @see zpt/ZMSRecordSet/main_grid.zpt
  var filter_timeout = null;
  $('table.table.table-striped.table-bordered.table-hover.zmi-sortable.zmi-selectable input.form-control:text').keyup(function(e) {
    var that = this;
    if ($(that).hasClass("form-disabled")) {
      return false;
    }
    var f = function() {
        $(that).addClass("form-disabled");
        var form = that.form;
        form.action = self.location.href;
        form.submit();
      }
    clearTimeout(filter_timeout);
    switch (e.keyCode) {
      case 13:
        f();
        return false;
      default:
        filter_timeout = setTimeout(f, 500);
        return true;
    }
  });

	// Textarea:
	// single-line
	$('div.single-line').each(function() {
			var $single_line = $(this);
			var $textarea = $('textarea',this);
			$textarea.prop({rows:1,wrap:'off'});
			
			if ($single_line.hasClass("zmi-code")) {
				$('textarea',$single_line).on('focus', function() {
					if ( !$(this).hasClass('open-zmi-code') ) {
						$(this)
							.addClass('open-zmi-code')
							.removeClass('alert-warning')
							.css('height','auto')
							.animate({height: $(this).prop('scrollHeight') + 'px'},600);
						if ( $(this).attr('data-dblclickhandler') ) {
							$(this).dblclick(function(e) {
								$('.zmi-code-close',$single_line).remove();
								$('textarea',$single_line)
									.animate({height: '30px'},0)
									.css('height','auto')
									.removeClass('open-zmi-code')
									.addClass('alert-warning')
									.blur();
								eval($(this).attr('data-dblclickhandler'));
							})
						}
						// Add closing button
						var close_btn = '<i title="Close Editing" class="zmi-code-close fas fa-chevron-up text-primary text-center" style="cursor:pointer;margin: 0 0 0 calc(50%);"></i>';
						$single_line.append(close_btn);
						$('.zmi-code-close',$single_line).click(
							function() {
								$('textarea',$single_line)
									.animate({height: '30px'},600)
									.css('height','auto')
									.removeClass('open-zmi-code');
								$(this).remove();
							}
						);
					}
				});
				return;
			}
			
			if ($single_line.hasClass("zmi-nodes")) {
				$textarea.prop({title:getZMILangStr('ATTR_NODE')});
			}
			if ($("span.input-group-append",this).length==0) {
				$(this).addClass("input-group");
				if ($textarea.prev('i').length==1) {
					$textarea.prev('i').wrap('<div class="input-group-prepend"><span class="btn btn-secondary"></span></div>')
				}
				if ($textarea.attr('data-style')) {
					$(this).append('<div class="input-group-append"><a href="javascript:;" class="btn btn-secondary" title="Click for Code Popup or Dbl-Click for Native Editor!" style="' + $textarea.attr('data-style') + '"></a></div>');
				} else {
					$(this).append('<div class="input-group-append"><a href="javascript:;" class="btn btn-secondary">...</a></div>');
				};
				var clicks, timer, delay;
				clicks=0;delay=500;timer=null;
				$('.input-group-append',this).on('click', function(){
					clicks++;
					timer = setTimeout(function() {
						switch(clicks){
							case 1:
								var html = '';
								html = html
									+ '<div id="zmi-single-line-edit" class="inner">'
										+ '<form class="form-horizontal" name="zmi-single-line-form">';
								if ($single_line.hasClass("zmi-nodes")) {
									html = html
											+ '<div class="col-lg-10">'
												+ '<div class="input-group">'
													+ '<input class="form-control url-input" type="text" name="zmi-nodespicker-url-input">'
													+ '<div class="input-group-append">'
														+ '<a class="btn btn-secondary" href="javascript:;" onclick="zmiBrowseObjs(\'zmi-single-line-form\',\'zmi-nodespicker-url-input\',getZMILang())">'
															+ '...'
														+ '</a>'
													+ '</div>'
												+ '</div><!-- .input-group -->'
											+ '</div><!-- .col-lg-10 -->';
								}
								html = html
											+ '<textarea class="form-control" rows="10" wrap="off" style="overflow:scroll">' + $textarea.val() + '</textarea>'
										+ '</form>'
									+ '</div><!-- #zmi-single-line-edit -->';
								zmiModal(null,{
									body:html,
									resizable:true,
									title:getZMILangStr('BTN_EDIT')+': '+$textarea.attr('title'),
									resize: function( event, ui ) {
										var $container = $('#zmi-single-line-edit');
										var $ta = $('textarea',$container);
										var taCoords = $ZMI.getCoords($ta[0],"relative");
										$ta.css({height:Math.max(20,$container.innerHeight()-taCoords.y-20)+'px'});
									},
									close: function( event, ui ) {
										$textarea.val($('#zmi-single-line-edit textarea').val());
									}});
							break;
							case 2:
								eval($textarea.attr('data-dblclickhandler'));
							break;
						}
					clicks=0;
					}, delay);
				});
			}
		});

	// Double-Clickable
	$('table.table-hover tbody tr')
		.dblclick( function(evt) {
			var href = null;
			if ((href==null || typeof href=="undefined") && $("a .fa-pencil-alt",this).length > 0) {
				return $("a .fa-pencil-alt",this).parents("a")[0].click();
			}
			else if ((href==null || typeof href=="undefined")) {
				href = $('a[target=]',this).attr('href');
			}
			if (!(href==null || typeof href=="undefined")) {
				self.location.href = href;
			} 
		})
		.attr( "title", "Double-click to edit!");

	// >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
	// Selectable
	$("table.zmi-selectable input:checkbox,table.zmi-selectable input:radio").change(function() {
			var $table = $(this).parents("table");
			$("tr",$table).each(function() {
					if ($("td:first input:checked",this).length == 0) {
						$(this).removeClass("zmi-selected");
					}
					else {
						$(this).addClass("zmi-selected");
					}
				});
		});

	// >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
	// Sortable
	var dragSrcEl = null;

	function handleDragStart(e) {
		// Target (this) element is the source node.
		dragSrcEl = this;
		e.dataTransfer.effectAllowed = 'move';
		e.dataTransfer.setData('text/html', this.outerHTML);
		this.classList.add('zmi-selected');
	}

	function handleDragOver(e) {
		if ( dragSrcEl ) {
			if (e.preventDefault) {
				e.preventDefault(); // Necessary. Allows us to drop.
			}
			if ((this.classList.contains("page") && dragSrcEl.classList.contains("page"))
					|| (this.classList.contains("pageelement") && dragSrcEl.classList.contains("pageelement"))) {
				this.classList.add('zmi-data-transfer-drag');
				e.dataTransfer.dropEffect = 'move';  // See the section on the DataTransfer object.
			}
			return false;
		}
	}

	function handleDragEnter(e) {
		// this / e.target is the current hover target.
	}

	function handleDragLeave(e) {
		this.classList.remove('zmi-data-transfer-drag');  // this / e.target is previous target element.
	}

	function handleDrop(e) {
		// this/e.target is current target element.
		if (e.stopPropagation) {
			e.stopPropagation(); // Stops some browsers from redirecting.
		}
		// Don't do anything if dropping the same column we're dragging.
		if (dragSrcEl != this) {
			// Set the source column's HTML to the HTML of the column we dropped on.
			this.parentNode.removeChild(dragSrcEl);
			var dropHTML = e.dataTransfer.getData('text/html');
			this.insertAdjacentHTML('beforebegin',dropHTML);
			var dropElem = this.previousSibling;
			addDnDHandlers(dropElem);
			var that = this;
			var c = 0;
			$('.zmi-sortable > li').each(function() {
				if ($(this).attr("id") == that.id) {
					// var pos = $(this).position();
					var pos = $(this.previousSibling).position();
					var id = $ZMI.actionList.getContextId(dragSrcEl);
					var href = id+'/manage_moveObjToPos?lang='+getZMILang()+'&pos:int='+c+'&fmt=json';
					$.get(href,function(result){
							var message = eval('('+result+')');
							$ZMI.showMessage(pos, message, 'alert-success zmi-dragged-info');
							$('.alert-success button').remove();
						});
				}
				c++;
			});
		}
		this.classList.remove('zmi-data-transfer-drag');
		return false;
	}

	function handleDragEnd(e) {
		this.classList.remove('zmi-selected');
	}

	function addDnDHandlers(elem) {
		elem.draggable = true;
		elem.addEventListener('dragstart', handleDragStart, false);
		elem.addEventListener('dragenter', handleDragEnter, false);
		elem.addEventListener('dragover', handleDragOver, false);
		elem.addEventListener('dragleave', handleDragLeave, false);
		elem.addEventListener('drop', handleDrop, false);
		elem.addEventListener('dragend', handleDragEnd, false);
	}

	var sortables = document.querySelectorAll('ul.zmi-container.zmi-sortable .zmi-selectable');
	[].forEach.call(sortables, addDnDHandlers);

	// >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
	// Checkboxes
	$("input[name='ids:list']").attr('title',getZMILangStr('ACTION_SELECT').replace('%s',getZMILangStr('ATTR_OBJECT')));
	$(".zmi-container .zmi-item:first .right input[name='active']:checkbox")
		.change(function() {
				zmiToggleSelectionButtonClick(this,$(this).prop("checked"));
			});
	$(".zmi-container .right input[name='ids:list']")
		.change(zmiActionButtonsRefresh)
		;
	// Constraints
	$(".split-left i.constraint").each(function() {
			var $container = $(this).parents(".right");
			$(".split-right",$container).popover({html:true,title:$("div.constraint",$container)[0].outerHTML});
		});
	// Action-Lists
	$('button.btn.split-right.dropdown-toggle').attr('title',getZMILangStr('ACTION_SELECT').replace('%s',getZMILangStr('ATTR_ACTION')));
	$(".btn-group")
		.mouseover( function(evt) {
				$(this).parents(".collapse").css({overflow:"visible"});
			})
		.mouseout( function(evt) {
				$(this).parents(".collapse").css({overflow:"hidden"});
			});
	$(".zmi-container .zmi-item .zmi-action")
		.focus( function(evt) {
				$ZMI.actionList.over(this,evt);
			})
		.hover( function(evt) {
				$ZMI.actionList.over(this,evt);
			},
			function(evt) {
				$ZMI.actionList.out(this);
			})
		;
	// Additional Add Button
	// var c = 0;
	// $(".zmi-container .zmi-item.pageelement .zmi-action:last,.zmi-container .zmi-item.page .zmi-action:first").each(function() {
	// 		if (c > 0) {
	// 			return;
	// 		}
	// 		c++;
	// 		var $that = $(this);
	// 		$that.parents(".zmi-container").append('<div id="zmi-action-default"><i class="fas fa-plus"></i></div>');
	// 		$("#zmi-action-default")
	// 			.hover( function(evt) {
	// 					var $zmiActionDefault = $(this);
	// 					var cb = function() {
	// 						if ($("#zmi-action-default-dropdown").length==0) {
	// 							var html = '<div id="zmi-action-default-dropdown" class="dropdown-menu">';
	// 							html += $(".insert-action",$that).nextAll().clone().wrapAll("<div/>").parent().html();
	// 							html += '</div>'
	// 							$("body").append(html);
	// 							var $zmiActionDropdown = $("#zmi-action-default-dropdown");
	// 							$zmiActionDropdown
	// 								.css({
	// 									position:"absolute",
	// 									top:($zmiActionDefault.offset().top+$zmiActionDefault.outerHeight()/2-$zmiActionDropdown.outerHeight())+"px",
	// 									left:($zmiActionDefault.offset().left+$zmiActionDefault.outerWidth()/2)+"px"
	// 								})
	// 								.hover( function(evt) {
	// 									},function(evt) {
	// 										$(this).hide();
	// 								});
								
	// 						}
	// 						$("#zmi-action-default-dropdown").show();
	// 					}
	// 					$ZMI.actionList.over($that,evt,cb);
	// 				},
	// 				function(evt) {
	// 				})
	// 			;
	// 	});

	// Inputs
	$ZMI.initInputFields($("body"));

	// Select tab.
	$("#subTab ul.nav.nav-tabs").each(function() {
			var anchor = $("a:first",this).attr("href");
			if (self.location.href.indexOf("#")>0) {
				anchor = self.location.href.substr(self.location.href.indexOf("#")+1);
				if (anchor.indexOf('_')==0) {
					anchor = anchor.substr(1);
				}
				anchor = '#'+anchor;
			}
			$("a[href='"+anchor+"']",this).click();
		});

	// Ajax Lazy Load
	$(".ajax-lazy-load").each(function() {
			var $that = $(this);
			$that.html('<i class="fas fa-spinner fa-spin"></i>&nbsp;'+getZMILangStr('MSG_LOADING'));
			var ajax_url = $that.attr("data-ajax-url");
			var params = {};
			$.get( ajax_url, params, function( data) {
					$that.html(data);
				});
		});

	$ZMI.setCursorAuto("EO bootstrap.plugin.zmi");

});

/**
 * Unlock form
 */
function zmiUnlockForm(form_id) {
	var $form = $('input[name="form_id"][value="'+form_id+'"]').parents("form");
	if ($('input[name="form_unlock"]',$form).length==0) {
		$form.append('<input type="hidden" name="form_unlock" value="1">');
	}
	$form.submit();
}

/**
 * Init input_fields
 */
ZMI.prototype.afterInitInputFields = function(h) {
	if (typeof this.afterInitInputFieldsHandler == "undefined") {
		this.afterInitInputFieldsHandler = [];
	}
	this.afterInitInputFieldsHandler.push(h);
}
ZMI.prototype.initInputFields = function(container) {
	$ZMI.setCursorWait("BO zmiInitInputFields["+$('form:not(.form-initialized)',container).length+"]");
	$(container).each(function() {
		var context = this;
			// Accordion:
			// highlight default collapse item
			var data_root = $("body").attr('data-root');
			$(".collapse",context).each(function() {
					var id = $(this).attr('id');
					if (typeof id != "undefined") {
						var $toggle = $('a.card-toggle[href=\'#'+id+'\']');
						if ($toggle.length > 0) {
							var key = "ZMS."+data_root+".collapse-"+id;
							var value = $ZMILocalStorageAPI.get(key,'1');
							if (value != null) {
								if ($(this).hasClass('show')) {
									if (value == '0') {
										$(this).removeClass('show');
									}
								}
								else {
									if (value == '1') {
										$(this).addClass('show');
									}
								}
							}
						}
					}
				});
			$("i:first",$(".collapse",context).prev('.card-header')).removeClass("fa-caret-down").addClass("fa-caret-right");
			$("i:first",$(".collapse.show",context).prev('.card-header')).removeClass("fa-caret-right").addClass("fa-caret-down");
			$("a.card-toggle",this).click(function(){
					$(this).blur();
					var id = $(this).attr('href').substr(1);
					var key = "ZMS."+data_root+".collapse-"+id;
					var $icon = $("i:first",this);
					var showing = $icon.hasClass("fa-caret-down")?1:0;
					if (showing) {
						$icon.removeClass("fa-caret-down").addClass("fa-caret-right");
						$ZMILocalStorageAPI.set(key,'0');
					}
					else {
						$icon.removeClass("fa-caret-right").addClass("fa-caret-down");
						$ZMILocalStorageAPI.set(key,'1');
					}
				});
				// Password
				$("input[type=password]",this).focus(function() {
						if ($(this).val()=='******') {
							$(this).val('');
						}
					})
				.blur(function() {
						if ($(this).val()=='') {
							$(this).val('******');
						}
					});
			});
	$('form:not(.form-initialized)',container)
		.submit(function() {
				var b = true;
				var context = this;
				// Button
				if( typeof self.btnClicked=="undefined" ||
						self.btnClicked=="BTN_BACK" ||
						self.btnClicked=="BTN_CANCEL" ||
						self.btnClicked=="BTN_DELETE" ) {
					return b;
				}
				// Richedit
				if ($(".form-richtext",this).length > 0) {
					zmiRichtextOnSubmitEventHandler(this);
				}
				// Multiple-Selects
				$('select[multiple="multiple"]',this).each(function() {
						var name = $(this).attr("name");
						var form = $(this).parents("form");
						if ($(this).hasClass('form-on-submit-selected')||($('select[name="zms_mms_src_'+name+'"]',form).length>0)) {
							$("option",this).prop("selected","selected");
						}
					});
				// Mandatory
				$(".has-error",this).removeClass("has-error");
				$(".form-group label.control-label.mandatory",this).filter(":visible").each(function() {
						var $label = $(this);
						var forName = $(this).attr("for");
						var labelText = $label.text().basicTrim();
						var $controlGroup = $label.parents(".form-group");
						var $controls = $("div:first",$controlGroup);
						var $control = $('input[name='+forName+'],select:not([name^="zms_mms_src_"])',$controls);
						$label.attr("title","");
						$control.attr("title","");
						if ($control.length==1) {
							var isBlank = false;
							var nodeName = $control.prop("nodeName").toLowerCase();
							var nodeType = $control.prop("type").toLowerCase();
							if (nodeName=="input") {
								if ($control.val().basicTrim().length==0 && typeof $control.attr("data-value-attr")!="undefined") {
									$control.val($control.attr($control.attr("data-value-attr")));
								}
								isBlank = $control.val().basicTrim().length==0;
								if (isBlank && nodeType=="file") {
									var name = $control.attr("name");
									var exists = $('input[name="exists_'+forName+'"]:hidden',$controlGroup).val();
									isBlank = !(exists=='True');
									var generate_preview = $('input[name="generate_preview_'+forName.replace(/_/,'hires_')+':int"]:checked',context).val();
									isBlank &= !(generate_preview=='1');
								}
							}
							else if (nodeName=="select") {
								isBlank = ($("option:selected",$control).length==0) 
									|| ($("option:selected",$control).length==1 && $("option:selected",$control).attr("value")=="");
							}
							if (isBlank) {
								$controlGroup.addClass("has-error");
								$label.attr("title",getZMILangStr("MSG_REQUIRED").replace(/%s/,labelText));
								$control.attr("title",getZMILangStr("MSG_REQUIRED").replace(/%s/,labelText)).tooltip({placement:'top'});
								if (b) {
									$control.focus();
								}
								b = false;
							}
							else {
								var dataExclude = $(this).attr("data-exclude");
								if (typeof dataExclude != "undefined") {
									var excludeList = dataExclude.split(",");
									var v = $control.val();
									if ($.inArray(v,excludeList)) {
										$controlGroup.addClass("has-error");
									}
								}
							}
						}
					});
				// Password
				var $password = $("input[type=password]",this).filter(":visible");
				if (($password.length==2)
					&& ($($password[0]).prop("name").toLowerCase().indexOf("confirm")<0)
					&& ($($password[1]).prop("name").toLowerCase().indexOf("confirm")>=0)
					&& ($($password[0]).val().length == 0
						|| $($password[0]).val() != $($password[1]).val())) {
					var $controlGroup = $password.parents(".form-group");
					var $label = $("label.control-label",$controlGroup);
					$controlGroup.addClass("has-error");
					b = false;
				}
				// Check for intermediate modification by other user
				if (b && $('input#last_change_dt:hidden',this).length && $('input[name="form_unlock"]',this).length==0) {
					var result = $.ajax({
						url: 'manage_get_node_json',
						data:{lang:getZMILang(),preview:'preview'},
						datatype:'text',
						async: false
						});
					var node = eval("("+result.responseText+")");
					var change_dt = node["change_dt"];
					var change_uid = node["change_uid"];
					var last_change_dt = $('input#last_change_dt:hidden',this).val();
					var last_change_uid = $('input#last_change_uid:hidden',this).val();
					// Intermediate modification?
 					if (change_dt != last_change_dt) {
						var body = '<div class="alert alert-error">'
									+ '<h4>'+$ZMI.icon("icon-warning-sign")+' '+getZMILangStr('ATTR_LAST_MODIFIED')+'</h4>'
									+ '<div>'+change_dt+' '+getZMILangStr('BY')+' '+change_uid+'</div>'
								+ '</div>'
								+ '<table class="table table-bordered table-striped">'
								+ '<thead>'
								+ '<tr class="form-group">'
									+ '<th><label class="control-label">' + '</label></th>'
									+ '<th><em>Diff</em></th>'
									+ '<th><em>Mine</em></span></th>'
									+ '<th><em>Theirs</em> ('+change_uid+' <span class="zmi-change-dt">'+(new Date(change_dt)).toLocaleFormat(getZMILangStr('DATETIME_FMT'))+'</span>)</th>'
								+ '</thead>'
								+ '</tr>';
						for (var key in node) {
							var $input = $("[name='"+key+"'],[name='"+key+"_"+getZMILang()+"']",this).filter("[data-initial-value]");
							if ($input.length > 0) {
								var $controlGroup = $input.parents(".form-group");
								var $label = $("label.control-label:first",$controlGroup);
								var remoteVal = (""+node[key]).replace(/\r\n/gi,"\n").trim();
								var currentVal = (""+$input.val()).replace(/\r\n/gi,"\n").trim();
								var initialVal = (""+$input.attr("data-initial-value")).replace(/\r\n/gi,"\n").trim();
								if ("file"==$input.attr("type")) {
									if (currentVal=="") {
										currentVal = initialVal;
									}
								}
								if (currentVal != initialVal) {
									$input.addClass("form-modified");
								}
								if (currentVal != remoteVal) {
									$input.removeClass("form-modified").addClass("form-conflicted").attr("data-remote-value",remoteVal);
									body += '<tr class="form-group">'
											+ '<td><label class="control-label"><span>' + $label.text() + '</span></label></td>'
											+ '<td><div style="overflow-y:scroll;max-height:20em" class="diff" id="'+$input.attr("name")+'_diff"></div></td>'
											+ '<td><div style="overflow-y:scroll;max-height:20em" class="mine" id="'+$input.attr("name")+'_mine">'+currentVal+'</div></td>'
											+ '<td><div style="overflow-y:scroll;max-height:20em" class="theirs" id="'+$input.attr("name")+'_theirs">'+remoteVal+'</div></td>'
										+ '</tr>';
								}
							}
						}
						var conflicts = $(".form-conflicted",this).length;
						if (conflicts > 0) {
							b = false;
							// confirm
							var form_id = $('input[name=form_id]').val();
							body += '</table>'
								+ '<div class="form-group">'
									+ '<button class="btn btn-primary" value="'+getZMILangStr('BTN_SAVE')+'" onclick="zmiUnlockForm(\''+form_id+'\')">'+getZMILangStr('BTN_SAVE')+'</button> '
									+ '<button class="btn btn-default" value="'+getZMILangStr('BTN_CANCEL')+'" onclick="window.open(self.location.href);">'+getZMILangStr('BTN_CANCEL')+'</button> '
								+ '</div>';
							zmiModal(null,{
									body:body,
									title: getZMILangStr('CAPTION_WARNING')
								});
							// show diffs
							$.plugin('diff',{
									files: [
										'/++resource++zms_/jquery/diff/diff_match_patch.js',
										'/++resource++zms_/jquery/diff/jquery.pretty-text-diff.min.js'
								]});
							$.plugin('diff').set({context:this});
							$.plugin('diff').get(".form-conflicted",function() {
									$(".form-conflicted",context).each(function(){
											var id = $(this).attr("name")+"_diff";
											var $diffContainer = $("#"+id);
											$(this).prettyTextDiff({
													cleanup:true,
													originalContent:$(this).attr("data-initial-value").replace(/</gi,'&lt;'),
													changedContent:$(this).val().replace(/</gi,'&lt;'),
													diffContainer:$diffContainer
												});
											var lines = $diffContainer.html().replace(/<span>/gi,'').replace(/<\/span>/gi,'').split("<br>");
											var show = [];
											var changed = false;
											for (var i = 0; i < lines.length; i++) {
												var line = lines[i];
												changed |= line.indexOf("<del>")>=0 || line.indexOf("<ins>")>=0;
												if (changed) {
													show.push(i);
												}
												changed &= !(line.indexOf("</del>")>=0 || line.indexOf("</ins>")>=0);
											}
											var html = [];
											changed = false;
											for (var i = 0; i < lines.length; i++) {
												var line = lines[i];
												changed |= line.indexOf("<del>")>=0 || line.indexOf("<ins>")>=0;
												line = '<span class="line-number'+(changed?' line-changed':'')+'">'+(i+1)+'</span> '+lines[i];
												if (!(show.contains(i-1) || show.contains(i) || show.contains(i+1))) {
													line = '<span class="diff-unchanged hidden">'+line+'</span>';
												}
												else {
													line = line+'<'+'br/>';
												}
												html.push(line);
												changed &= !(line.indexOf("</del>")>=0 || line.indexOf("</ins>")>=0);
											}
											$diffContainer.html(html.join(""));
										});
								});
						}
					}
				}
				return b;
			})
		.each(function() {
			var context = this;
			if ($(this).parents(".d-none").length>0) {
				return;
			}
			$(this).addClass('form-initialized');
			// Multi-Autocomplete
			$('select.form-multiautocomplete[multiple]:not(.d-none)',context).each(function() {
					var $select = $(this);
					var id = $select.attr('id');
					var ajax_url = $select.attr('data-ajax-url');
					var obj_id = $select.attr('data-obj-id');
					var attr_id = $select.attr('data-attr-id');
					$select.removeClass("form-control").addClass("zmi-select").attr({"data-autocomplete-add":false});
					$select.before(''
						+ '<div class="input-group form-multiautocomplete">'
							+ '<input type="text" id="_'+id+'" class="form-control form-autocomplete" data-ajax-url="'+ajax_url+'" data-obj-id="'+obj_id+'" data-attr-id="'+attr_id+'"/>'
							+ '<div class="input-group-append">'
								+ '<a href="javascript:;" class="btn btn-secondary"><i class="fas fa-plus text-primary"></i></a>'
							+ '</div>'
						+ '</div><!-- .input-group -->');
					var $inputgroup = $select.prev();
					$("input",$inputgroup).keydown(function(e) {
							if (e.which==13) {
								e.preventDefault();
								e.stopPropagation();
								$(".input-group-append",$inputgroup).trigger("click");
								return false;
							}
						});
					$(".input-group-append .btn",$inputgroup).click(function() {
							// get value
							var $input = $("input",$inputgroup);
							var v = $input.val();
							if (v.length>0) {
								$input.val("");
								if ($select.children("option[value='"+v+"']").length==0) {
									$select.append('<option selected="selected" value="'+v+'" data-value="'+v+'">'+v+'</option>').removeClass("d-none");
									// rebuild multiselect
									$ZMI.multiselect(context);
								}
							}
						});
				});
			// Autocomplete
			$('.form-autocomplete:not(.d-none)',context).each(function() {
					$(this).addClass("ui-autocomplete-input");
					var id = $(this).attr('id');
					var ajax_url = $(this).attr('data-ajax-url');
					var obj_id = $(this).attr('data-obj-id');
					var attr_id = $(this).attr('data-attr-id');
					zmiAutocomplete('#'+id,{
							serviceUrl:ajax_url,
							paramName:'q',
							params:{obj_id:obj_id,attr_id:attr_id},
							transformResult: function(response, originalQuery) {
									var m = {
										query: originalQuery,
										suggestions: $.map(response.split("\n"), function(x) {
											return { value: x, data: x };
										})
									};
									return m;
								}
					});
				});
			// Multiselect
			$.plugin('multiselect',{
				files: [
					$ZMI.getConfProperty('plugin.bootstrap.multiselect.js','/++resource++zms_/bootstrap/plugin/bootstrap.plugin.zmi.multiselect.js')
				]});
			$.plugin('multiselect').set({context:context});
			$.plugin('multiselect').get("select.zmi-select[multiple]:not(.d-none)",function(){
					$ZMI.multiselect(context);
				});
			// Activity-Toggle
			if ($("#zmi-toggle-activity").length==0) {
				$("#attrActivity",context).each(function() {
						var $input = $(".activity input:checkbox",this);
						if ($input.length>0) {
							$(this).prev(".attr_last_modified").each(function() {
									$("#zmi-toggle-activity-btn",this).append('<span id="zmi-toggle-activity" style="vertical-align:inherit" title="'+getZMILangStr('ATTR_ACTIVE')+'">'+$ZMI.icon(($input.prop('checked')?'fas fa-check-square':'far fa-square')+' ui-helper-clickable')+'</span>&nbsp;');
									$("#zmi-toggle-activity").click(function(event) {
											$input.click();
											$("i",this).attr("class",($input.prop('checked')?'fas fa-check-square':'far fa-square')+' ui-helper-clickable');
											event.stopPropagation();
										});
								});
						}
					});
				}
			// Button-Clicked
			$('input[type="submit"],button[type="submit"]',context)
				.click(function() {
						self.btnClicked = $(this).attr("value");
					});
			// Button-Radiogroup
			$('.btn-radiogroup',context).each(function() {
					var key = $(this).attr('data-value');
					var $input = $('input#'+key);
					var val = $input.val();
					$(this).children('span')
						.addClass("btn")
						.click(function() {
								var item = $(this).attr('data-value');
								$input.val(item);
								$(this).siblings('.btn-info').removeClass('btn-info').addClass('btn-secondary');
								$(this).removeClass('btn-secondary').addClass('btn-info');
							})
						.each(function() {
								var item = $(this).attr('data-value');
								if (val == "") {
									val = item;
									$input.val(val);
								}
								if (item==val) {
									$(this).addClass("btn-info");
								}
								else {
									$(this).addClass("btn-secondary");
								}
							});
				});
			// Mandatory
			if ($(this).hasClass('form-insert')) {
				$(".form-group label.col-lg-2 control-label.mandatory",this).each(function() {
						var $label = $(this);
						$label.prepend('<i class="fas fa-exclamation"></i>');
					});
			}
			// Check for intermediate modification by other user
			$("input,select,textarea",this).each(function() {
					var $this = $(this);
					$this.attr("data-initial-value",$this.val());
					$this.change(function() {
							if ($this.val()==$this.attr("data-initial-value")) {
								$this.removeClass("form-modified");
							}
							else {
								$this.addClass("form-modified");
							}
						});
				});
			// Icon-Class
			$('input.zmi-input-icon-clazz',this).each(function() {
				$(this).wrap( '<div class="input-group"></div>' );
				$(this).before('<span class="input-group-text"><i class="fas fa-invisible"></i></span>');
				$(this).parent().children('span.input-group-text').wrap( '<div class="input-group-prepend"></div>');
				var fn = function() {
					var $input = $(this);
					var $formGroup = $input.parents(".form-group");
					var $i = $("i",$formGroup);
					$i.attr("class",$input.val());
				};
				$(this).change(fn).keyup(fn).change();
			});
			// Url-Picker
			var fn_url_input_each = function() {
					var $input = $(this);
					var fmName = $input.parents("form").attr("name");
					var elName = $input.attr("name");
					$input.wrap('<div class="input-group"></div>');
					var $inputgroup = $input.parent();
					if ($input.prop("disabled")) {
						$inputgroup.append(''
								+ '<div class="input-group-append">'
									+ '<span class="input-group-text"><i class="fas fa-ban-circle"></i></span>'
								+ '</div>'
							);
					}
					else {
						$inputgroup.append(''
									+ '<div class="input-group-append">'
										+ '<a class="btn btn-secondary" href="javascript:;" onclick="return zmiBrowseObjs(\'' + fmName + '\',\'' + elName + '\',getZMILang())">'
											+ '<i class="fas fa-link"></i>'
										+ '</a>'
									+ '</div>'
							);
					}
					var fn = function() {
							$inputgroup.next(".breadcrumb, [aria-label=breadcrumb]").remove();
							$.ajax({
									url: 'zmi_breadcrumbs_obj_path',
									data:{lang:getZMILang(),zmi_breadcrumbs_ref_obj_path:$input.val()},
									datatype:'text',
									success:function(response) {
											$inputgroup.next(".breadcrumb, [aria-label=breadcrumb]").remove();
											$inputgroup.after(response.replace(/<!--(.*?)-->/gi,'').trim());
										}
								});
						};
					$input.change(fn).change();
				}
			$("input.url-input",this).each(fn_url_input_each);
			$("textarea.url-input",this).each(function() {
					var $input = $(this);
					var fmName = $input.parents("form").attr("name");
					var elName = $input.attr("name");
					var $container = $input.parent();
					$input.hide();
					$container.append(''
						+ '<div class="url-input-container"></div>'
						+'<input type="hidden" name="new_'+elName+'"/>'
						+'<a href="javascript:;" onclick="return zmiBrowseObjs(\'' + fmName + '\',\'new_' + elName + '\',getZMILang())" class="btn btn-secondary">'
						+'<i class="fas fa-plus"></i>'
						+'</a>');
					$("input[name='new_"+elName+"']",$container).change(function() {
							var v = $(this).val();
							var l = $input.val().length==0?[]:$input.val().split("\n");
							if (!l.contains()) {
								l.push(v);
								$input.val(l.join("\n")).change();
							}
							$(this).val("");
						});
					$input.change(function() {
							var v = $(this).val();
							var l = $input.val().length==0?[]:$input.val().split("\n");
							var $inputContainer = $(".url-input-container",$container);
							$inputContainer.html('');
							for (var i = 0; i < l.length; i++) {
								$inputContainer.append('<input class="form-control url-input" type="text" value="'+l[i]+'" disabled="disabled"> ');
							}
							$("input.url-input",$inputContainer).each(fn_url_input_each);
							$(".input-group-append",$inputContainer).replaceWith('<a class="btn btn-secondary" href="javascript:;"><i class="fas fa-times"></i></a>');
							$("input.url-input",$inputContainer).next().click(function() {
									$(this).parents(".input-group").next(".breadcrumb").remove();
									$(this).parents(".input-group").remove();
									var l = [];
									$("input",$inputContainer).each(function() {
											var v = $(this).val();
											if (v.length > 0) {
												l.push(v);
											}
										});
									$input.val(l.join("\n")).change();
								});
						}).change();
				});
				// Richedit
				var $richedits = $('div[id^="zmiStandardEditor"]',this);
				if ($richedits.length > 0) {
					$richedits.each(function() {
							var elName = $(this).attr("id").substr("zmiStandardEditor".length);
							zmiRichtextInit(elName);
							var v = $("#"+elName).val();
							function matchAll(source, regexp) {
								var matches = [];
								source.replace(regexp, function() {
										var arr = ([]).slice.call(arguments, 0);
										var extras = arr.splice(-2);
										arr.index = extras[0];
										arr.input = extras[1];
										matches.push(arr);
								});
								return matches.length ? matches : [];
							}
							var l = matchAll(v,/<a data-id="(.*?)"(.*?)>(.*?)<\/a>/gi);
							if (l.length > 0) {
								var labels = [];
								for (var i = 0; i < l.length; i++) {
									labels.push(' <span class="label">'+l[i][0]+'</span>');
								}
								$(this).siblings(":last").after('<div class="inlinelinks">Inline-Links: '+labels.join(', ')+'</div>')
							}
						});
				}
			// Date-Picker
			$("input.datepicker,input.datetimepicker",this).each(function() {
				$(this).closest("div")
					.addClass("input-group")
					.removeClass("col-sm-9")
					.removeClass("col-sm-10")
					.removeClass("col-md-10")
					.wrap('<div class="col-sm-4 col-md-3 col-lg-3"></div>');
				$(this).before('<div class="input-group-prepend"><span class="input-group-text"><i class="far fa-calendar"></i></span></div>');
			})
		});
	if (typeof this.afterInitInputFieldsHandler != "undefined") {
		for (var i in this.afterInitInputFieldsHandler) {
			this.afterInitInputFieldsHandler[i]();
		}
	}
	$ZMI.setCursorAuto("EO zmiInitInputFields");
}

/**
 * Show message
 */
ZMI.prototype.showMessage = function(pos, message, context) {
	$(".alert").remove();
	var html = ''
		+ '<div class="alert'+(typeof context=='undefined'?'':' '+context)+'" style="position:absolute;left:'+pos.left+'px;top:'+pos.top+'px;">'
			+ '<button type="button" class="close" data-dismiss="alert">&times;</button>'
			+ '<span class="message">' + message + '</span>'
		+ '</div>';
	$('body').append(html);
	window.setTimeout('$(".alert").hide("slow")',2000);
}

/**
 * Open modal
 */
var zmiModalStack = [];
function zmiModal(s, opt) {
	$ZMI.setCursorWait("zmiModal");
	if (typeof opt == "undefined") {
		var id = zmiModalStack[zmiModalStack.length-1];
		$('#'+id).modal(s);
	}
	else if (typeof opt == "object") {
		var id = typeof opt['id']=="undefined"?"zmiModal"+(s==null || typeof $(s).attr('id')=="undefined"?zmiModalStack.length:$(s).attr('id')):opt['id'];
		var body = s==null?opt['body']:$(s).html();
		if (s!=null && opt['remove']==true) {
			$(s).remove();
		}
		if (typeof id!="undefined" && typeof body!="undefined") {
			zmiModalStack.push(id);
			var html = ''
				+'<div class="modal" id="'+id+'" tabindex="-1" role="dialog">'
					+'<div class="modal-dialog" role="document">'
						+'<div class="modal-content">'
							+'<div class="modal-header">'
								+'<h5 class="modal-title">'+opt['title']+'</h5>'
								+'<button type="button" class="close" data-dismiss="modal" aria-label="'+getZMILangStr('BTN_CLOSE')+'">'
									+'<span aria-hidden="true">&times;</span>'
								+'</button>'
								+'</div>'
							+'<div class="modal-body">'+body+'</div>'
							+'<div class="modal-footer">'
							+'</div>'
						+'</div><!-- /.modal-content -->'
					+'</div><!-- /.modal-dialog -->'
				+'</div><!-- /.modal -->';
			$('#'+id).remove();
			$("body").append(html);
			var buttons = opt['buttons'];
			if (typeof buttons == 'object') {
				for (var i = 0; i < buttons.length; i++) {
					var button = buttons[i];
					$('#'+id+' .modal-footer').append('<button type="submit">'+button['text']+'</button> ');
					var $button = $('#'+id+' .modal-footer button:last');
					for (var k in button) {
						var v = button[k];
						if (typeof v == "function") {
							$button.on(k,eval("("+v+")"));
						}
						else {
							$button.attr(k,v);
						}
					}
				}
			}
			$('#'+id)
				.on('show.bs.modal',function(){
						if (typeof opt['beforeOpen'] == 'function') {
							opt['beforeOpen'](this);
						}
					})
				.on('shown.bs.modal',function(){
						if (typeof opt["width"] != "undefined") {
							$("#"+id+" .modal-dialog").css({width:opt["width"]});
						}
						if (typeof opt['open'] == 'function') {
							opt['open'](this);
						}
						$ZMI.initInputFields($("#"+id));
					})
				.on('hide.bs.modal',function(){
						if (typeof opt['beforeClose'] == 'function') {
							opt['beforeClose'](this);
						}
					})
				.on('hidden.bs.modal',function(){
						if (typeof opt['close'] == 'function') {
							opt['close'](this);
						}
						zmiModalStack.pop();
					})
				.modal(opt['modal']);
			if (typeof opt['minWidth'] != 'undefined') {
				$('#'+id+' .modal-content').css('minWidth',opt['minWidth']);
				$('#'+id+' .modal-dialog').css('minWidth',opt['minWidth']);
			}
			$('#'+id+' .modal-dialog').css('transform','translate('+((zmiModalStack.length-1)*2)+'em,'+((zmiModalStack.length-1)*2)+'em)');
		}
	}
	$ZMI.setCursorAuto("zmiModal");
	return false;
}

/**
 * Open link in iframe (jQuery UI Dialog).
 */
ZMI.prototype.iframe = function(href, data, opt) {
	$ZMI.setCursorWait("$ZMI.iframe");
	data = typeof data == "undefined" ? {} : data;
	opt = typeof opt == "undefined" ? {} : opt;
	var url = href + "?";
	for (var k in data) {
		url += k + "=" + data[k] + "&";
	}
	// Iframe
	if (typeof opt['iframe'] != 'undefined') {
		var width = '100%';
		var height = typeof opt['height'] == 'undefined' ? '100%' : opt['height'];
		opt['body'] = '<iframe src="' + url + '" width="' + width + '" height="' + height + '" frameBorder="0"></iframe>';
		zmiModal(null,opt);
		$ZMI.setCursorAuto("zmiIframe");
	}
	else {
		$.get( href, data, function(result) {
				var $result = $(result);
				if ($("div#system_msg",$result).length>0) {
					var manage_tabs_message = $("div#system_msg",$result).text();
					manage_tabs_message = manage_tabs_message.substr(0,manage_tabs_message.lastIndexOf("("));
					var href = self.location.href;
					href = href.substr(0,href.indexOf("?"))+"?lang="+getZMILang()+"&manage_tabs_message="+manage_tabs_message;
					self.location.href = href;
				}
				else {
					opt['body'] = result;
					if (typeof opt['title'] == "undefined") {
						var title = $("div.zmi",result).attr("title");
						if (typeof title != "undefined" && title) {
							opt['title'] = title;
						}
					}
					zmiModal(null,opt);
					$ZMI.setCursorAuto("$ZMI.iframe");
				}
			});
	}
	return false;
}

// #############################################################################
// ### ZMI ObjectTree
// #############################################################################

ZMIObjectTree = function() {};
$ZMI.objectTree = new ZMIObjectTree();

ZMIObjectTree.prototype.init = function(s,href,p) {
	var that = this;
	that.p = p;
	// Init preselected active.
	that.active = [];
	href = href+"/"+(typeof p['init.href'] != "undefined"?p['init.href']:"ajaxGetParentNodes");
	$(s).html('<i class="fas fa-spinner fa-spin"></i>&nbsp;'+getZMILangStr('MSG_LOADING'));
	var params = {lang:getZMILang(),preview:'preview'};
	if (typeof that.p["params"] == "object") {
		for (var i in that.p["params"]) {
			params[i] = that.p["params"][i];
		}
	}
	$.get(href,params,function(result) {
			$(s).html("");
			var context = s;
			var pages = $("page",result);
			for (var i = 0; i < pages.length; i++) {
				var $page = $(pages[i]);
				var page_home_id = $page.attr("home_id");
				var page_id = $page.attr("id").substr(page_home_id.length+1);
				var html = that.addPages([pages[i]]);
				$(context).append(html);
				context = "ul[data-home-id="+page_home_id+"][data-id="+page_id+"] li";
				// Remember preselected active.
				that.active.push({id:page_id,home_id:page_home_id});
			}
			$("li",s).addClass("active");
			var callback = that.p['init.callback'];
			if (typeof callback != "undefined") {
				callback();
			}
		});
}

ZMIObjectTree.prototype.addPages = function(pages) {
	var that = this;
	var html = "";
	for (var i=0; i<pages.length;i++) {
		var $page = $(pages[i]);
		var titlealt = "";
		var page_uid = $page.attr("uid");
		var page_home_id = $page.attr("home_id");
		var page_id = $page.attr("id").substr(page_home_id.length+1);
		var page_absolute_url = $page.attr("absolute_url");
		var page_physical_path = $page.attr("physical_path");
		var link_url = $page.attr("index_html");
		var page_is_active = $page.attr("active")=='1' || $page.attr("active")=='True';
		var page_is_restricted = $page.attr("restricted")=='1' || $page.attr("restricted")=='True';
		var page_is_page = $page.attr("is_page")=='1' || $page.attr("is_page")=='True';
		var page_is_pageelement = $page.attr("is_pageelement")=='1' || $page.attr("is_pageelement")=='True';
		var page_meta_type = $page.attr("meta_id");
		var page_type = $page.attr("attr_dc_type");
		var page_titlealt = $page.attr("titlealt");
		var page_icon = $page.attr("zmi_icon");
		var anchor = "";
		if ( page_is_pageelement) {
			var file_filename = $("file>filename",$page);
			if (file_filename.length) {
				anchor = "/" + file_filename.text();
			}
		}
		if (page_meta_type=='ZMSGraphic') {
			var $img = $("img",$page);
			if ($img.length==1) {
				link_url = '<img data-id=&quot;'+page_uid+'&quot; src=&quot;'+$("href",$img).text()+'&quot;>';
				try { page_titlealt = filename; } catch(err) { };
			}
		}
		else if (page_meta_type=='ZMSFile') {
			var $file = $("file",$page);
			if ($file.length==1) {
				var $fname = $("filename",$file).text();
				var $ext = $fname.substring($fname.lastIndexOf('.')+1,$fname.length);
				link_url = '<a data-id=&quot;'+page_uid+'&quot; href=&quot;'+$("href",$file).text()+'&quot; target=&quot;_blank&quot;>'+$page.attr("titlealt").replace(/"/g,'')+'&#32;('+$ext.toUpperCase()+',&#32;'+$("size",$file).text()+')</a>'; 
				try { page_titlealt = filename; } catch(err) { };
			}
		}
		var callback = that.p['toggleClick.callback'];
		var css = [];
		if (!page_is_active) {
			css.push("inactive");
		};
		if (page_is_restricted) {
			css.push("restricted");
		};
		if (typeof(page_type) != 'undefined') { 
			if ( page_type.length > 0 ) {
				css.push('type-'+page_type)
			}
		};
		html += '<ul data-id="'+page_id+'" data-home-id="'+page_home_id+'" class="zmi-page '+page_meta_type+'">';
		html += '<li class="'+css.join(' ')+'">';
		html += $ZMI.icon("fas fa-caret-right toggle",'title="+" onclick="$ZMI.objectTree.toggleClick(this'+(typeof callback=="undefined"?'':','+callback)+')"')+' ';
		if (page_is_pageelement) {
			html += '<span style="cursor:help" onclick="$ZMI.objectTree.previewClick(this)" title="'+$ZMI.getLangStr('TAB_PREVIEW')+'"><i class="'+page_icon+'"></i></span> ';
		}
		html += '<a href="'+page_absolute_url+'"'
				+ ' data-link-url="'+link_url+'"'
				+ ' data-uid="'+page_uid+'"'
				+ ' data-page-physical-path="'+page_physical_path+'"'
				+ ' data-anchor="'+anchor+'"'
				+ ' data-page-is-page="'+page_is_page+'"'
				+ ' data-page-titlealt="'+page_titlealt.replace(/"/g,'&quot;').replace(/'/g,'&apos;')+'"'
				+ ' onclick="return zmiSelectObject(this)">';
		if (!page_is_pageelement) {
			html += '<i class="'+page_icon+'"></i> ';
		}
		html += page_titlealt;
		html += '</a>';
		html += '</li>';
		html += '</ul><!-- .zmi-page -->';
	}
	return html;
}

/**
 * Click toggle.
 */
ZMIObjectTree.prototype.toggleClick = function(toggle, callback) {
	var that = this;
	var $container = $(toggle).parents("li:first");
	$container.children("ul").remove();
	if ($(toggle).hasClass("fa-caret-right")) {
		$(toggle).removeClass("fa-caret-right").addClass("fa-caret-down").attr({title:'-'});
		var href = '';
		var homeId = null;
		$(toggle).parents(".zmi-page").each(function(){
				var dataId = $(this).attr("data-id");
				var dataHomeId = $(this).attr("data-home-id");
				if (homeId == null) {
					homeId = dataHomeId;
				}
				if (homeId != dataHomeId) {
					href = '/'+dataHomeId+'/'+homeId+href;
					homeId = dataHomeId;
				}
				else {
					href = '/'+dataId+href;
				}
			});
		if (!href.indexOf('/'+homeId)==0) {
			href = '/'+homeId+href;
		}
		var base = $ZMI.getPhysicalPath();
		base = base.substr(0,base.indexOf('/'+homeId));
		// Set wait-cursor.
		$container.append('<div id="loading" class="zmi-page"><i class="fas fa-spinner fa-spin"></i>&nbsp;&nbsp;'+getZMILangStr('MSG_LOADING')+'</div>');
		// JQuery.AJAX.get
		var params = {lang:getZMILang(),preview:'preview',physical_path:$('meta[name=physical_path]').attr('content')}
		if (typeof that.p["params"] == "object") {
			for (var i in that.p["params"]) {
				params[i] = that.p["params"][i];
			}
		}
		$.get(base+href+'/manage_ajaxGetChildNodes',params,function(result){
				// Reset wait-cursor.
				$("#loading").remove();
				// Get and iterate pages.
				var pages = $('page',result);
				if ( pages.length == 0) {
					$(toggle).removeClass("fa-caret-down").attr({title:''});
				}
				else {
					var html = that.addPages(pages);
					$container.append(html);
					// Set preselected active.
					for (var i = 0; i < that.active.length; i++) {
						var d = that.active[i];
						$('ul[data-id='+d.id+'][data-home-id='+d.home_id+'] > li').addClass('active');
					}
				}
				if (typeof callback == 'function') {
					callback();
				}
			});
	}
	else {
		if ($(toggle).hasClass("fa-caret-down")) {
			$(toggle).removeClass("fa-caret-down").addClass("fa-caret-right").attr({title:'+'});
		}
		if (typeof callback == 'function') {
			callback();
		}
	}
}

/**
 * Click preview.
 */
ZMIObjectTree.prototype.previewClick = function(sender) {
	var that = this;
	var data_id = $(sender).closest('.zmi-page').attr('data-id');
	if($('#zmi_preview_'+data_id).length > 0) {
		$('#zmi_preview_'+data_id).remove();
	}
	else {
		var coords = $ZMI.getCoords(sender);
		var abs_url = $(sender).parent('li').children('[data-page-physical-path]').attr('data-page-physical-path');
		$.get(abs_url+'/ajaxGetBodyContent',{lang:getZMILang(),preview:'preview'},function(data){
				$('div.zmi-browse-iframe-preview').remove();
				$('body').append(''
						+'<div id="zmi_preview_'+data_id+'">'
							+'<div class="zmi-browse-iframe-preview">'
								+'<div class="btn btn-default" title="' + getZMILangStr('BTN_CLOSE') + '" style="position:absolute;border-radius:0;" onclick="$(\'#zmi_preview_'+data_id+'\').remove()"><i class="icon-remove fas fa-times"></i></div>'
								+data
							+'</div><!-- .zmi-browse-iframe-preview -->'
						+'</div><!-- #zmi-preview -->'
					);
				$('div.zmi-browse-iframe-preview').css({top:coords.y+$(sender).height(),left:coords.x+$(sender).width()});
			});
	}
}

// #############################################################################
// ### ZMI Action-Lists
// #############################################################################

ZMIActionList = function() {};
$ZMI.actionList = new ZMIActionList();

ZMIActionList.prototype.getContextId = function(el) {
	var context = $(el).hasClass("zmi-item")?$(el):$(el).parents("li.zmi-item");
	var context_id = $(context).attr("id");
	return typeof context_id == "undefined" || context_id == ""?"":context_id.replace(/zmi_item_/gi,"");
}

/**
 * Populate and show action-list.
 *
 * @param el
 */
ZMIActionList.prototype.over = function(el, e, cb) {
	var that = this;
	if (typeof cb == "undefined") {
		$("button.split-left",el).css({visibility:"visible"});
	}
	var $button = $('button.btn.split-right.dropdown-toggle',el);
	// Expandable headers.
	$button.click(function() {
			var $right = $(this).parents(".right");
			var selected = $("input:checkbox",$right).length?$("input:checkbox",$right).prop("checked"):false;
			$(".dropdown-header",$right).each(function(index) {
					var actualCollapsed = $("i",this).hasClass("fa-caret-right");
					var expectedCollapsed = (index == 0 && !selected) || (index > 0 && selected);
					if (actualCollapsed != expectedCollapsed) {
						$(this).click();
					}
				});
		});
	$('*',$button).hide();
	// Exit.
	if ($(el).hasClass("loaded") || $(el).hasClass("loading")) {
		// Callback.
		if (typeof cb == "function") {
			cb();
		}
		return;
	}
	// Set wait-cursor.
	$(el).addClass("loading");
	$(document.body).css( "cursor", "wait");
	// Initialize.
	var lang = getZMILang();
	var context_id = this.getContextId(el);
	// Edit action
	$("button.split-left",el).click(function() {
			if (!$(el).hasClass("loading")) {
				if ($(".fa-plus-sign",this).length==0) {
					var action = self.location.href;
					action = action.substr(0,action.lastIndexOf("/")+1);
					if (context_id=="") {
						action += "manage_properties";
					}
					else {
						if ($ul.html().indexOf(context_id+"/manage_main")<0) {
							return false;
						}
						action += context_id+"/manage_main";
					}
					action += "?lang=" + lang;
					self.location.href = action;
				}
				else {
					$('button.btn.split-right.dropdown-toggle',el).click();
				}
			}
			return false;
		});
	// Build action and params.
	var action = zmiParams['base_url'];
	action = action.substr(0,action.lastIndexOf("/"));
	action += "/manage_ajaxZMIActions";
	var params = {};
	params['lang'] = lang;
	params['context_id'] = context_id;
	// JQuery.AJAX.get
	$.get( action, params, function(data) {
		// Get object-id.
		var value = eval('('+data+')');
		var id = value['id'].replace(/\./,"_");
		var actions = value['actions'];
		$(el).append('<div class="dropdown-menu"></div>');
		$ul = $(".dropdown-menu",el);
		var startsWithSubmenu = actions.length > 1 && actions[1][0].indexOf("-----") == 0 && actions[1][0].lastIndexOf("-----") > 0;
		console.log("[ZMIActionList.over]: startsWithSubmenu="+startsWithSubmenu);
		var o = 0;
		if (startsWithSubmenu) {
			o = 2;
			var html = '';
			var action = actions[1];
			var optlabel = action[0];
			var opticon = '<i class="fas fa-plus-sign"></i>';
			optlabel = optlabel.substr("-----".length);
			optlabel = optlabel.substr(0,optlabel.lastIndexOf("-----"));
			optlabel = optlabel.basicTrim();
			$("button.split-left",el).html(opticon+' '+optlabel);
		}
		for (var i = o; i < actions.length; i++) {
			if (o==0 && i==1) {
				$ul.append('<a class="dropdown-item" href="javascript:zmiToggleSelectionButtonClick($(\'li.zmi-item' + (id==''?':first':'#zmi_item_'+id) + '\'))"><i class="fas fa-check-square"></i> '+getZMILangStr('BTN_SLCTALL')+'/'+getZMILangStr('BTN_SLCTNONE')+'</a>');
			}
			var action = actions[i];
			var optlabel = action[0];
			var optvalue = action[1];
			var opticon = action.length>2?action[2]:'';
			var opttitle = action.length>3?action[3]:'';
			if (optlabel.indexOf("-----") == 0 && optlabel.lastIndexOf("-----") > 0) {
				opticon = '<i class="fas fa-caret-down"></i>';
				optlabel = optlabel.substr("-----".length);
				optlabel = optlabel.substr(0,optlabel.lastIndexOf("-----"));
				optlabel = optlabel.basicTrim();
				$ul.append('<div class="dropdown-header '+optvalue+'">'+opticon+' '+optlabel+'</div>');
			}
			else {
				if (opticon.indexOf('<')!=0) {
					opticon = $ZMI.icon(opticon);
				}
				var html = '';
				html += '<a class="dropdown-item" title="'+opttitle+'" href="javascript:$ZMI.actionList.exec($(\'li.zmi-item' + (id==''?':first':'#zmi_item_'+id) + '\'),\'' + optlabel + '\',\'' + optvalue + '\')">';
				html += opticon+' '+optlabel;
				html += '</a>';
				$ul.append(html);
			}
		}
		// Dropup
		if(typeof e!="undefined"&&$ul.innerHeight()<$(document).innerHeight()&&e.pageY>$ul.innerHeight()){
			$(el).addClass("dropup");
		}
		// Expandable headers
		$(".dropdown-header",$ul)
			.click(function (event) {
				var duration = (event.pageX && event.pageY) ? 400 : 0; // User-event show animation
				$("i",this).toggleClass("fa-caret-down").toggleClass("fa-caret-right");
				$(this).nextUntil(".dropdown-header").slideToggle(duration);
				event.stopImmediatePropagation();
				event.stopPropagation();
			});
		// Reset wait-cursor.
		$(el).removeClass("loading").addClass("loaded");
		$(document.body).css( "cursor", "auto");
		// Callback.
		if (typeof cb == "function") {
			cb();
		}
	});
}

/**
 * Hide action-list.
 *
 * @param el
 */
ZMIActionList.prototype.out = function(el) {
	$("button.split-left",el).css({visibility:"hidden"});
	var $button = $('button.btn.split-right.dropdown-toggle',el);
	$('*',$button).show();
}

/**
 *  Execute action.
 */
ZMIActionList.prototype.exec = function(sender, label, target) {
	var id_prefix = this.getContextId(sender);
	if (typeof id_prefix != 'undefined' && id_prefix != '') {
		id_prefix = id_prefix.replace(/(\d*?)$/gi,'');
	}
	else {
		id_prefix = 'e';
	}
	var $el = $(".zmi-action",sender);
	var $fm = $el.parents("form");
	var sort_id = $(".zmi-sort-id",$el).text();
	$("input[name='custom']").val(label);
	if (typeof sort_id!="undefined"&&sort_id.length>0&&!isNaN(sort_id)) {
		$("input[name='_sort_id:int']").val(sort_id);
	}
	if (target.toLowerCase().indexOf('manage_addproduct/')==0 && target.toLowerCase().indexOf('form')>0) {
		// Parameters
		var inputs = $("input:hidden",$fm);
		var data = {};
		for ( var i = 0; i < inputs.length; i++) {
			var $input = $(inputs[i]);
			var id = $input.attr("id");
			if (jQuery.inArray(id,['form_id','id_prefix','_sort_id','custom','lang','preview'])>=0) {
				data[$input.attr('name')] = $input.val();
			}
		}
		data['id_prefix'] = id_prefix;
		var title = '<i class="fas fa-plus-sign"></i> '+getZMILangStr('BTN_INSERT')+': '+label;
		$('<li id="manage_addProduct" class="zmi-item zmi-highlighted"><div class="center">'+title+'</div></li>').insertAfter($el.parents(".zmi-item"));
		// Show add-dialog.
		$ZMI.iframe(target,data,{
				id:'zmiIframeAddDialog',
				title:title,
				width:800,
				open:function(event,ui) {
					$ZMI.runReady();
					$('#addInsertBtn').click(function() {
								self.btnClicked = $(this).text();
								var $fm = $(".modal form.form-horizontal");
								$("input[name=btn]:hidden",$fm).remove();
								$fm.append('<input type="hidden" name="btn" value="BTN_INSERT">');
								$fm.submit();
							});
					$('#addCancelBtn').click(function() {
								zmiModal("hide");
							});
					if($('#zmiIframeAddDialog .form-control').length==0) {
						$('#addInsertBtn').click();
					}
				},
				close:function(event,ui) {
					$('#manage_addProduct').remove();
				},
				buttons:[
						{id:'addInsertBtn', text:getZMILangStr('BTN_INSERT'), name:'btn', 'class':'btn btn-primary'},
						{id:'addCancelBtn', text:getZMILangStr('BTN_CANCEL'), name:'btn', 'class':'btn'}
				]
			});
	}
	else {
		var $div = $el.parents("div.right");
		var $input = $("input[name='ids:list']",$div);
		$input.prop("checked",true);
		zmiActionButtonsRefresh(sender);
		var params = $ZMI.parseURLParams(target);
		var target = target.indexOf("?")>0?target.substr(0,target.indexOf("?")):target;
		if (this.confirm($fm,target,params)) {
			var c = 0;
			for (var k in params) {
				var id = 'hidden_'+k+'_'+c;
				$fm.append('<input type="hidden" id="'+id+'" name="'+k+'">');
				$('input#'+id,$fm).val(params[k]);
				c++;
			}
			$("input[name='id_prefix']",$fm).val(id_prefix);
			$fm.attr("action",target);
			$fm.attr("method","POST");
			$fm.submit();
		}
		else {
			$("input[name='ids:list']",$div).prop("checked",false);
			zmiActionButtonsRefresh(sender);
		}
	}
}

/**
 * Confirm execution of action from select.
 *
 * @param fm
 * @param target
 * @param data
 */
ZMIActionList.prototype.confirm = function(fm, target, data) {
	var b = true;
	var i = $("input[name='ids:list']:checkbox:checked").length;
	if (target.indexOf("../") == 0) {
		i = 1;
	}
	if (target.indexOf("manage_rollbackObjChanges") >= 0) {
		var msg = getZMILangStr('MSG_ROLLBACKVERSIONCHANGES');
		msg = msg.replace("%i",""+i);
		b = confirm(msg);
	}
	else if (target.indexOf("manage_cutObjects") >= 0) {
		var msg = getZMILangStr('MSG_CONFIRM_CUTOBJS') + $ZMI.getDescendantLanguages();
		msg = msg.replace("%i",""+i);
		b = i > 0 && confirm(msg);
	}
	else if (target.indexOf("manage_eraseObjs") >= 0) {
		var msg = getZMILangStr('MSG_CONFIRM_DELOBJS');
		msg = msg.replace("%i",""+i);
		b = i > 0 && confirm(msg);
	}
	else if (target.indexOf("manage_deleteObjs") >= 0) {
		var msg = getZMILangStr('MSG_CONFIRM_TRASHOBJS');
		msg = msg.replace("%i",""+i);
		msg += $ZMI.getDescendantLanguages();
		b = i > 0 && confirm(msg);
	}
	else if (target.indexOf("manage_undoObjs") >= 0) {
		var msg = getZMILangStr('MSG_CONFIRM_DISCARD_CHANGES');
		msg = msg.replace("%i",""+i);
		b = i > 0 && confirm(msg);
	}
	else if (target.indexOf("manage_executeMetacmd") >=0 ) {
		var msg = $.ajax({
			url: 'getMetaCmdDescription',
			data:data,
			datatype:'text',
			traditional: true,
			async: false
			}).responseText;
		if (typeof msg != 'undefined' && msg.length > 0) {
			msg = msg.replace("%i",""+i);
			b = confirm(msg);
		}
	}
	else if (target == "") {
		b = false;
	}
	return b;
}

/**
 * @param sender
 * @param evt
 */
function zmiActionButtonsRefresh(sender,evt) {
	$(".zmi-selectable").each(function() {
			if ($(".right input:checked",this).length > 0) {
				$(this).addClass("zmi-selected");
			}
			else {
				$(this).removeClass("zmi-selected");
			}
		});
}

/**
 * This method (un-)checks all id-checkboxes on page and refreshs the buttons.
 *
 * @param sender
 * @param v Boolean value for new (un-)checked state.
 */
function zmiToggleSelectionButtonClick(sender,v) {
	var $fm = $(sender).parents('form');
	var $inputs = $('input:checkbox:not([id~="active"]):not([id~="attr_dc_coverage"])',$fm);
	if (typeof v == "undefined") {
		v = !$inputs.prop('checked');
	}
	$inputs.prop('checked',v).change();
	zmiActionButtonsRefresh(sender);
}

/**
 * zmiBrowseObjs
 */
function zmiBrowseObjs(fmName, elName, lang) {
	var elValue = '';
	if (fmName.length>0 && elName.length>0) {
		elValue = $('form[name='+fmName+'] input[name='+elName+']').val();
	}
	var title = getZMILangStr('CAPTION_CHOOSEOBJ');
	var href = "manage_browse_iframe";
	href += '?lang='+lang;
	href += '&defaultLang='+lang;
	href += '&fmName='+fmName;
	href += '&elName='+elName;
	href += '&elValue='+escape(elValue);
	if ( typeof selectedText == "string") {
		href += '&selectedText=' + escape( selectedText);
	}
	zmiModal(null,{
			body: '<iframe src="'+href+'" style="width:100%; min-width:'+$ZMI.getConfProperty('zmiBrowseObjs.minWidth','200px')+'; height:100%; min-height: '+$ZMI.getConfProperty('zmiBrowseObjs.minHeight','62vh')+'; border:0;"></iframe>',
			title: title
		});
	return false;
}

function zmiBrowseObjsApplyUrlValue(fmName, elName, elValue, elTitle) {
	$('form[name='+fmName+'] input[name='+elName+']').val(elValue).change();
	if (typeof elTitle != "undefined") {
		$('form[name='+fmName+'] input[name^=title]:text').each(function() {
				if ($(this).val()=='') {
					$(this).val(elTitle).change();
				} 
			});
	}
}

function zmiDialogClose() {
	zmiModal("hide");
}

// ############################################################################
// ### WYSIWYG-Textareas
// ############################################################################

/**
 * @see http://stackoverflow.com/questions/1981088/set-textarea-selection-in-internet-explorer
 */
function setInputSelection(e, selection){
	e.focus();
	if(e.setSelectionRange) {
		e.setSelectionRange(selection.start, selection.end);
	} else if(e.createTextRange) {
		e = e.createTextRange();
		e.collapse(true);
		e.moveEnd('character', selection.end);
		e.moveStart('character', selection.start);
		e.select();
	}
}

/**
 * @see http://stackoverflow.com/questions/7186586/how-to-get-the-selected-text-in-textarea-using-jquery-in-internet-explorer-7
 */
function getInputSelection(el) {
	var start = 0, end = 0, normalizedValue, range,
	textInputRange, len, endRange;
	if (typeof el.selectionStart == "number" && typeof el.selectionEnd == "number") {
		start = el.selectionStart;
		end = el.selectionEnd;
	} else {
		range = document.selection.createRange();
		if (range && range.parentElement() == el) {
			len = el.value.length;
			normalizedValue = el.value.replace(/\r\n/g, "\n");
			// Create a working TextRange that lives only in the input
			textInputRange = el.createTextRange();
			textInputRange.moveToBookmark(range.getBookmark());
			// Check if the start and end of the selection are at the very end
			// of the input, since moveStart/moveEnd doesn't return what we want
			// in those cases
			endRange = el.createTextRange();
			endRange.collapse(false);
			if (textInputRange.compareEndPoints("StartToEnd", endRange) > -1) {
				start = end = len;
			} else {
				start = -textInputRange.moveStart("character", -len);
				start += normalizedValue.slice(0, start).split("\n").length - 1;
				if (textInputRange.compareEndPoints("EndToEnd", endRange) > -1) {
					end = len;
				} else {
					end = -textInputRange.moveEnd("character", -len);
					end += normalizedValue.slice(0, end).split("\n").length - 1;
				}
			}
		}
	}
	return {
		start: start,
		end: end
	};
}

var selectedInput = null;
var selectedText = {start:-1,end:-1};

function untagSelected(tag, leftDelimiter, rightDelimiter) {
	var v = $(selectedInput).val();
	var pre = v.slice(0,selectedText.start);
	var range = v.slice(selectedText.start,selectedText.end);
	var post = v.slice(selectedText.end);
	while (range.indexOf(" ")==range.length-1) {
		range = range.slice(0,range.length-1);
		post = " " + post;
	}
	var tagName = tag.indexOf(" ")>0?tag.substr(0,tag.indexOf(" ")):tag;
	var startTag = leftDelimiter + tag + rightDelimiter;
	var startRe = new RegExp(leftDelimiter + tag + "(.*?)" + rightDelimiter, "gi");
	var endTag = leftDelimiter + "/" + tagName + rightDelimiter; 
	var endRe = new RegExp(leftDelimiter + "/" + tag + rightDelimiter, "gi");
	var preMatch = pre.match(startRe);
	var postMatch = post.match(endRe);
	if (preMatch!=null && postMatch!=null) {
    	var preMatch = preMatch[preMatch.length-1];
    	var postMatch = postMatch[0];
    	if (pre.endsWith(preMatch) && post.startsWith(postMatch)) {
    		var newPre = pre.replace(preMatch,'');
    		var newPost = post.replace(postMatch,'');
    		$(selectedInput).val(newPre+range+newPost);
    		// Set selection.
    		var offset = newPre.length-pre.length;
    		selectedText = {start:selectedText.start+offset,end:selectedText.start+offset+range.length};
    		setInputSelection(selectedInput,selectedText);
        }
		return true;
	}
	return false;
}

function tagSelected(tag, leftDelimiter, rightDelimiter) {
	var v = $(selectedInput).val();
	var pre = v.slice(0,selectedText.start);
	var range = v.slice(selectedText.start,selectedText.end);
	var post = v.slice(selectedText.end);
	while (range.indexOf(" ")==range.length-1) {
		range = range.slice(0,range.length-1);
		post = " " + post;
	}
	var tagName = tag.indexOf(" ")>0?tag.substr(0,tag.indexOf(" ")):tag;
	var tagAttrs = tag.indexOf(" ")>0?tag.substr(tag.indexOf(" ")):"";
	if (tagName == 'a' && tagAttrs == '') {
		if (range.indexOf("@") > 0) {
			tagAttrs = ' href="mailto:'+range+'"';
		}
		else if (range.indexOf("://") > 0) {
			tagAttrs = ' href="'+range+'" target="_blank"';
		}
	}
	if (tagName == 'a' && tagAttrs == '') {
		zmiBrowseObjs('','',getZMILang());
	} 
	else {
		var startTag = leftDelimiter + tagName + tagAttrs + rightDelimiter;
		var endTag = leftDelimiter + "/" + tagName + rightDelimiter;
		var newRange = startTag + range + endTag; 
		$(selectedInput).val(pre+newRange+post);
		// Set selection.
		var offset = startTag.length;
		selectedText = {start:selectedText.start+offset,end:selectedText.start+offset+range.length};
		setInputSelection(selectedInput,selectedText);
		return true;
	}
	return false;
}

function formatSelected(tag, leftDelimiter, rightDelimiter) {
	if (!untagSelected(tag, leftDelimiter, rightDelimiter)) {
		tagSelected(tag, leftDelimiter, rightDelimiter);
	}
}

/**
 * Set text-format for input.
 */
function setTextFormatInput( tag, fmName, elName) {
	self.fm = document.forms[ fmName];
	self.el = self.fm.elements[ elName];
	if (typeof self.el == 'undefined') {
		self.el = document.getElementsByName(elName)[0];
	}
	// Avoid loosing focus by fitting textarea to content amount
	$('#' + elName ).height(document.getElementById(elName).scrollHeight);
	formatSelected(tag,'<','>');
}

/**
 * Store caret.
 */
function storeCaret(input) {
	selectedInput = input;
	selectedText = getInputSelection(input);
}

// ############################################################################
// ### Record-Sets
// ############################################################################

function zmiRecordSetMoveRow(context, qIndex, delta) {
	var $form = $(context).closest('form');
	if (typeof qIndex != "undefined") {
		var $btnGroup = $(context).closest('.btn-group');
		var $input = $("input:checkbox:first",$btnGroup);
		$form.append('<input type="hidden" name="qindex:int" value="' + $input.val() + '">');
	}
	$form.append('<input type="hidden" name="pos:int" value="' + (qIndex+1) + '">');
	$form.append('<input type="hidden" name="newpos:int" value="' + (qIndex+1+delta) + '">');
	$('input[name="action"]',$form).val('move');
	$form.submit();
}

function zmiRecordSetDeleteRow(context, qIndex) {
	var $form = $(context).closest('form');
	if (typeof qIndex != "undefined") {
		var $btnGroup = $(context).closest('.btn-group');
		var $input = $("input:checkbox:first",$btnGroup);
		$input.prop('checked',true).change();
	}
	if (confirm(getZMILangStr('MSG_CONFIRM_DELOBJS').replace('%i',$("input[name='qindices:list']:checked").length))) {
		$('input[name="action"]',$form).val('delete');
		$form.submit();
	}
	else if (typeof qIndex != "undefined") {
		var $input = $('input[value="'+qIndex+'"]',$form);
		$input.prop('checked',false).change();
	}
	return false;
}

function zmiRecordSetDuplicateRow(context, qIndex) {
	var $form = $(context).closest('form');
	if (typeof qIndex != "undefined") {
		var $btnGroup = $(context).closest('.btn-group');
		var $input = $("input:checkbox:first",$btnGroup);
		$input.prop('checked',true).change();
	}
	if (confirm(getZMILangStr('MSG_CONFIRM_DUPLICATEOBJS').replace('%i',$("input[name='qindices:list']:checked").length))) {
		$('input[name="action"]',$form).val('duplicate');
		$form.submit();
	}
	else if (typeof qIndex != "undefined") {
		var $input = $('input[value="'+qIndex+'"]',$form);
		$input.prop('checked',false).change();
	}
	return false;
}
// ############################################################################
// ### HORIZONTAL SCROLLING MAIN NAVIGATION FOR SMALL SCREENS
// ############################################################################
$ZMI.registerReady(function(){
	var hidWidth;
	var scrollBarWidths = 40;
	var widthOfList = function(){
		var itemsWidth = 0;
		$('.wrapper .nav.nav-tabs li').each(function(){
			var itemWidth = $(this).outerWidth();
			itemsWidth+=itemWidth;
		});
		return itemsWidth;
	};
	var widthOfHidden = function(){
		return (($('.wrapper').outerWidth())-widthOfList()-getLeftPosi())-scrollBarWidths;
	};
	var getLeftPosi = function(){
		try {
			return $('.wrapper .nav.nav-tabs').position().left;
		} catch(err) {
			return 0
		}
	};
	var reAdjust = function(){
		if (($('.wrapper').outerWidth()) < widthOfList()) {
			$('.scroller-right').show();
		}
		else {
			$('.scroller-right').hide();
		}
		
		if (getLeftPosi()<0) {
			$('.scroller-left').show();
		}
		else {
			$('.item').animate({left:"-="+getLeftPosi()+"px"},'slow');
			$('.scroller-left').hide();
		}
	}
	$('.scroller-right').click(function() {
		$('.scroller-left').fadeIn('slow');
		$('.scroller-right').fadeOut('slow');
		$('.wrapper .nav.nav-tabs').animate({left:"+="+widthOfHidden()+"px"},'slow',function(){ });
	});
	$('.scroller-left').click(function() {
		$('.scroller-right').fadeIn('slow');
		$('.scroller-left').fadeOut('slow');
		$('.wrapper .nav.nav-tabs').animate({left:"-="+getLeftPosi()+"px"},'slow',function(){ });
	});
	reAdjust();
	$(window).on('resize',function(e){
			reAdjust();
	});
});
// ############################################################################
// ### BACK-TO-TOP-SCROLL BUTTON
// ############################################################################
$ZMI.registerReady(function(){
	// Reference: https://getflywheel.com/layout/sticky-back-to-top-button-tutorial/
	const scrollToTopButton = document.getElementById('js-top');
	if ( scrollToTopButton ) {
		const scrollFunc = () => {
			let y = window.scrollY;
			if (y > 0) {
				scrollToTopButton.className = "back-to-top show";
			} else {
				scrollToTopButton.className = "back-to-top hide";
			}
		};
		window.addEventListener("scroll", scrollFunc);
		const scrollToTop = () => {
			const c = document.documentElement.scrollTop || document.body.scrollTop;
			if (c > 0) {
				window.requestAnimationFrame(scrollToTop);
				window.scrollTo(0, c - c / 10);
			}
		}
		scrollToTopButton.onclick = function(e) {
			e.preventDefault();
			scrollToTop();
		}
	}
});

// /////////////////////////////////////////////////////////////////////////////
//  Config
// /////////////////////////////////////////////////////////////////////////////

/**
 * Returns configuration-files.
 */
var zmiExpandConfFilesProgress = false;
function zmiExpandConfFiles(el, pattern) {
	if (!zmiExpandConfFilesProgress) {
		if ( $("option",el).length==1) {
			zmiExpandConfFilesProgress = true;
			// Set wait-cursor.
			$ZMI.setCursorWait("zmiExpandConfFiles");
			var first = null;
			if ( $("option",el).length==1) {
				first = $("option:first",el).html();
				$("option:first",el).html(getZMILangStr('MSG_LOADING'));
			}
			// JQuery.AJAX.get
			$.get( 'getConfFiles',{pattern:pattern},function(data) {
						if (first!=null) {
							$("option:first",el).html(first);
						}
						var items = $("item",data);
						for (var i = 0; i < items.length; i++) {
							var item = $(items[i]);
							var value = item.attr("key");
							var label = item.text();
							$(el).append('<option value="'+value+'">'+label+'</option>');
						}
						zmiExpandConfFilesProgress = false;
						// Reset wait-cursor.
						$ZMI.setCursorAuto("zmiExpandConfFiles");
					});
		}
	}
}

// /////////////////////////////////////////////////////////////////////////////
//  Multiselect
// /////////////////////////////////////////////////////////////////////////////

/**
 * Remove option from multiselect
 */
ZMI.prototype.removeFromMultiselect = function(src) { 
	if (typeof src == "string") {
		src = document.getElementById(src);
	}
	var selected = new Array(); 
	var index = 0; 
	while (index < src.options.length) { 
		if (src.options[index].selected) { 
			selected[index] = src.options[index].selected; 
		} 
		index++; 
	}
	index = 0; 
	var count = 0; 
	while (index < selected.length) { 
		if (selected[index]) 
			src.options[count] = null; 
		else 
			count++; 
		index++; 
	} 
	sortOptions(src); 
}

/**
 * Append option to multiselect
 */
ZMI.prototype.appendToMultiselect = function(src, data, defaultSelected) {
	var label = data;
	var value = data;
	if (typeof data == "object") {
		label = data.label;
		value = data.value;
		if (data.orig) {
			label = data.orig;
		}
	}
	if (typeof src == "string") {
		src = document.getElementById(src);
	}
	for ( var i = 0; i < src.options.length; i++) {
		if ( src.options[i].value == value) {
			return;
		}
	}
	if (typeof defaultSelected == "undefined") {
		defaultSelected = false;
	}
	var option = new Option( label, value, defaultSelected);
	src.options[ src.length] = option;
}

/**
 * Select single option from multiselect.
 */
ZMI.prototype.selectFromMultiselect = function(fm, srcElName, dstElName) {
	var src = fm.elements[srcElName];
	var dst = fm.elements[dstElName];
	var selected = new Array();
	var index = 0;
	while (index < src.options.length) {
		if (src.options[index].selected) {
			var newoption = new Option(src.options[index].text, src.options[index].value, true, true);
			dst.options[dst.length] = newoption;
			selected[index] = src.options[index].selected;
		}
		index++;
	}
	index = 0;
	var count = 0;
	while (index < selected.length) {
		if (selected[index])
			src.options[count] = null;
		else
			count++;
		index++;
	}
	sortOptions(src);
	sortOptions(dst);
	return false;
}

/**
 * Select all options from multiselect.
 */
ZMI.prototype.selectAllFromMultiselect = function(fm, srcElName, dstElName) {
	var src = fm.elements[srcElName];
	var dst = fm.elements[dstElName];
	var index = 0;
	while (index < src.options.length) {
		src.options[index].selected = true;
		index++;
	}
	this.selectFromMultiselect(fm,srcElName,dstElName);
	return false;
}

/**
 * Add option.
 *
 * @param object
 * @param name
 * @param value
 * @param selectedValue
 */
function addOption( object, name, value, selectedValue) {
	var defaultSelected = value.length > 0 && value == selectedValue;
	var selected = value.length > 0 && value == selectedValue;
	object.options[object.length] = new Option( name, value, defaultSelected, selected);
}
  
/**
 * Sort options.
 */
function sortOptions(what) {
	var copyOption = new Array();
	for (var i=0;i<what.options.length;i++)
		copyOption[i] = new Array(what[i].text,what[i].value);
	copyOption.sort();
	for (var i=what.options.length-1;i>-1;i--) {
		what.options[i] = null;
	}
	for (var i=0;i<copyOption.length;i++)
		addOption(what,copyOption[i][0],copyOption[i][1])
}
