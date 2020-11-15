ZMI.prototype.multiselect = function(context) {
	$("select.zmi-select[multiple]:not(.d-none)",context).each(function() {
		var refreshContainer = function($container) {
			var c = 0;
			var $select = $container.parent().prev();
			$("option",$select).prop("selected","");
			$container.children().each(function() {
				var data_value = $(this).attr("data-value");
				var val = ($container.hasClass("zmi-sortable")?c+":":"")+data_value;
				$("option[data-value='"+data_value+"']",$select).prop({selected:"selected",value:val});
				c++;
			});
			// sortable(".zmi-select.zmi-sortable", "reload");
		}
		var refreshDropdown = function($select,$dropdown) {
			if ($select.attr('data-autocomplete-add')=="false" 
					|| $(".dropdown-item.d-none",$dropdown).length==$(".dropdown-item",$dropdown).length) {
				$dropdown.hide("normal");
			}
			else {
				$dropdown.show("normal");
			}
		}
		var $select = $(this);
		$select.next(".zmi-select-container").remove();
		var html = ''
			+ '<div class="zmi-select-container form-inline">'
			+ '<div class="'+$select.attr('class').replace('form-control','')+'">'
			+ '</div>'
			+ '<div class="btn-group btn-group-sortable">\n'
			+ '<button type="button" class="btn btn-secondary dropdown-toggle" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false">\n'
			+ '<i class="fas fa-plus mr-1"></i>'
			+ '</button>'
			+ '<div class="dropdown-menu scrollable-menu">';
		var c = 0;
		$("option",$select).each(function() {
			var v = $(this).attr('value');
			$(this).attr('data-value',v);
			html += ''
				+ '<a class="dropdown-item" href="javascript:;" data-value="'+v+'">\n'
				+ $(this).text()
				+ '</a>\n';
			c++;
		});
		html += ''
			+ '</div>'
			+ '</div>'
			+ '</div>';
		$select.addClass("d-none").after(html);
		var $container = $select.next().children(":first");
		var $dropdown = $container.next();
		refreshDropdown($select,$dropdown);
		$("a.dropdown-item",$dropdown).click(function() {
			$(this).addClass("d-none");
			var data_value = $(this).attr('data-value');
			$container.append(''
				+'<div class="btn btn-light" data-value="'+data_value+'">'
				+'<a href="javascript:;">'+$ZMI.icon('icon-times')+'</a> '
				+$(this).text()
				+'</div> '
			);
			$(".btn a:last",$container).click(function() {
				var $parent = $(this).parent();
				$("a.dropdown-item[data-value='"+data_value+"']",$dropdown).removeClass("d-none");
				$parent.remove();
				refreshDropdown($select,$dropdown);
				refreshContainer($container);
			});
			refreshDropdown($select,$dropdown);
			refreshContainer($container);
		});
		$("option:selected",this).each(function() {
			var v = $(this).attr('data-value');
			$("a.dropdown-item[data-value='"+v+"']",$dropdown).click();
		});
		pluginSortable(".zmi-select.zmi-sortable",function() {
			sortable(".zmi-select.zmi-sortable",{
				forcePlaceholderSize: true,
				placeholderClass: 'btn btn-light sortable-placeholder',
			});
			$(".zmi-select.zmi-sortable").bind('sortupdate', function() {
				refreshContainer($container);
			});
		});
	});
}