/*
 * @see http://nicolas.rudas.info/jQuery/getPlugin/
 */
 
function pluginLanguage() {
	return getZMILangStr('LOCALE',{'nocache':""+new Date()});
}

/**
 * jQuery UI Autocomplete
 */
function zmiAutocomplete(s, o) {
	pluginAutocomplete(s,function() {
		try {
			var prev_el = $(s).autocomplete(o).prev()[0];
			if ( $(prev_el).attr('class')!='input-group-prepend' ) {
				$(s).autocomplete(o).before('<div class="input-group-prepend"><span class="input-group-text"><i class="fas fa-search"></i></span></div>');
				$(s).closest('.col-sm-10,td').wrapInner('<div class="input-group"></div>');
			}
		} catch (error) {
			console.error(error);
			$(s).autocomplete(o).before('<div class="input-group-prepend"><span class="input-group-text"><i class="fas fa-search"></i></span></div>');
			$(s).closest('.col-sm-10,td').wrapInner('<div class="input-group"></div>');
		}
	});
}


/**
 * ZMSLightbox
 */
$(function(){
	$('a.zmslightbox,a.fancybox')
		.each(function() {
				var $img = $("img",$(this));
				$img.attr("data-hiresimg",$(this).attr("href"));
				$(this).click(function() {
						return showFancybox($img);
					});
			});
});

function pluginFancybox(s, c) {
	$.plugin('zmslightbox',{
		files: ['/++resource++zms_/jquery/zmslightbox/zmslightbox.js',
				'/++resource++zms_/jquery/zmslightbox/zmslightbox.css']
		});
	$.plugin('zmslightbox').get(s,c);
}

function showFancybox($sender) {
	pluginFancybox('body',function() {
			show_zmslightbox($sender);
		});
	return false;
}


/**
 * Autocomplete
 * @see http://bassistance.de/jquery-plugins/jquery-plugin-autocomplete/
 */
function pluginAutocomplete(s, c) {
	$.plugin('autocomplete',{
		files: ['/++resource++zms_/jquery/autocomplete/jquery.autocomplete.min.js',
				'/++resource++zms_/jquery/autocomplete/jquery.autocomplete.css']
	});
	$.plugin('autocomplete').get(s,c);
}


/**
 * Sortable
 * @see https://github.com/lukasoppermann/html5sortable
 */
function pluginSortable(s, c) {
	$.plugin('sortable',{
		files: ['/++resource++zms_/jquery/sortable/html5sortable.min.js',
				'/++resource++zms_/jquery/sortable/html5sortable.css']
	});
	$.plugin('sortable').get(s,c);
}


/**
 * jquery-cropper - the jQuery Image Cropping Plugin
 * @see https://github.com/fengyuanchen/jquery-cropper/
 */
function runPluginCropper(s,c) {
	$.plugin('cropper',{
		files: ['/++resource++zms_/jquery/cropper/cropper.min.js',
				'/++resource++zms_/jquery/cropper/cropper.css',
				'/++resource++zms_/jquery/cropper/jquery-cropper.min.js']
		});
	$.plugin('cropper').get(s,c);
}
