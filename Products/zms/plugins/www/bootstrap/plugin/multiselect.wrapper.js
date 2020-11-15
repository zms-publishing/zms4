ZMI.prototype.multiselect = function(context) {
				$.plugin('multiselect_js',{
					context: context,
					files: [
						'/++resource++zms_/bootstrap/plugin/multiselect.min.js'
					]});
				$.plugin('multiselect_js').get("select.zmi-select[multiple]:not(.d-none)",function(){
						$("select.zmi-select[multiple]:not(.d-none)",context).each(function() {
								var multiselect_name = $(this).attr("name");
								var multiselect_id = multiselect_name.substr(0,multiselect_name.indexOf(":"));
								var searchable = $("option",this).length>=$ZMI.getConfProperty('plugin.bootstrap.multiselect.wrapper.search.options.min',15);
								var html = '<div class="row twosided_multiselect'+(searchable?' searchable':'')+'">';
								html += ''
									+ '<div class="col-xs-5">'
									+ '<select id="'+multiselect_id+'" class="form-control" size="8" multiple="multiple">';
								$("option:not(:selected)",this).each(function() {
										html += ''
											+ '<option value="'+$(this).attr("value")+'">'+$(this).html()+'</option>';
									});
								html += ''
									+ '</select>'
									+ '</div><!-- .col-xs-5 -->'
									+ '<div class="col-xs-2">'
									+ '<button type="button" id="'+multiselect_id+'_rightAll" class="btn btn-secondary btn-block">'+$ZMI.icon('fas fa-angle-right')+'</button>'
									+ '<button type="button" id="'+multiselect_id+'_rightSelected" class="btn btn-secondary btn-block">'+$ZMI.icon('icon-angle-right')+'</i></button>'
									+ '<button type="button" id="'+multiselect_id+'_leftSelected" class="btn btn-secondary btn-block">'+$ZMI.icon('icon-angle-left')+'</i></button>'
									+ '<button type="button" id="'+multiselect_id+'_leftAll" class="btn btn-secondary btn-block">'+$ZMI.icon('fas fa-angle-left')+'</button>'
									+ '</div><!-- .col-xs-2 -->'
									+ '<div class="col-xs-5">'
									+ '<select id="'+multiselect_id+'_to" name="'+multiselect_name+'" class="form-control form-on-submit-selected" size="8" multiple="multiple">';
								$("option:selected",this).each(function() {
										html += ''
											+ '<option value="'+$(this).attr("value")+'">'+$(this).html()+'</option>';
									});
								html += ''
									+ '</select>'
									+ '</div><!-- .col-xs-5 -->'
									+ '</div><!-- .row -->';
								var options = {};
								if (searchable) {
									options['search'] = {
											left: '<input type="text" name="q" class="form-control" placeholder="'+getZMILangStr('BTN_SEARCH')+'..." />',
											right: '<input type="text" name="q" class="form-control" placeholder="'+getZMILangStr('BTN_SEARCH')+'..." />'
										};
								}
								$(this).replaceWith(html);
								$("#"+multiselect_id).multiselect(options);
							});
					});
}