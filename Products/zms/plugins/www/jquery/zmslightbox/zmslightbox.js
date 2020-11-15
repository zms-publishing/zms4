// GLOBALS zlb = _zms_light_box
var zmslightbox_obj;
var zlb_viewport = $('meta[name="viewport"]').attr('content');
var zlb_cur_xpos = 0;                // mouse position X
var zlb_cur_ypos = 0;                // mouse position Y
var zlb_ww = $(window).width();      // window width
var zlb_wh = $(window).height();     // window height
var zlb_wt = $(window).scrollTop();  // vertical scroll position
var zlb_cx = zlb_ww/2;               // window centerX
var zlb_cy = zlb_wt + zlb_wh/2;      // window centerY
var zlb_iw = 0;                      // visible imgobj.width
var zlb_ih = 0;                      // visible imgobj.height
var zlb_iw_f = 0;                    // full imgobj.width
var zlb_ih_f = 0;                    // full imgobj.height
var zlb_img_scale = 1                // imgobj scaling


// CONSTRUCTION
function add_zmslightbox(hiurl) {
	$('body').wrapInner('<section id="zmslightbox-mask"></section>')
	$('body').append('<figure id="zmslightbox">\
			<div id="zmslightbox-bg" onclick="remove_zmslightbox()"></div>\
			<div id="zmslightbox-controls" onclick="remove_zmslightbox()"><span id="close-zmslightbox">Close Lightbox</span></div>\
			<div id="zmslightbox-wrapper"><img src="'+hiurl+'" /></div>\
		</figure>');
	// Add Navigation
	$('#zmslightbox-wrapper').append('<i id="zlb_nav_right"></i>');
	$('#zmslightbox-wrapper').prepend('<i id="zlb_nav_left"></i>');
	$('#zlb_nav_right').on('click', function(evt) { get_next_zlb(this_img=hiurl, dir='next'); });
	$('#zlb_nav_left').on('click', function(evt) { get_next_zlb(this_img=hiurl, dir='previous'); });

	$('#zmslightbox-wrapper img').on('click', function(evt) {
			zlb_cur_xpos = evt.pageX - $(this).offset().left;
			zlb_cur_ypos = evt.pageY - $(this).offset().top;
			$(this).toggleClass('fullimage');
			zlb_iw_f = $(this).width();
			zlb_ih_f = $(this).height();
			if ( zlb_iw_f > zlb_ww || zlb_ih_f > zlb_wh ){
				release_zmslightbox();
				zlb_img_scale = zlb_iw_f/zlb_iw;
				center_zmslightbox($('#zmslightbox-wrapper img'));
				zlb_shift_x = (zlb_cur_xpos * zlb_img_scale)-zlb_ww/2;
				zlb_shift_y = (zlb_cur_ypos * zlb_img_scale)-zlb_wh/2;
				$(window).scrollLeft(zlb_shift_x);
				$(window).scrollTop(zlb_shift_y);
			} else {
				$(this).addClass('fullscreen');
				center_zmslightbox($('#zmslightbox-wrapper img'));
			};
	});
	$('#zmslightbox-wrapper img').hide();
	$('body').addClass('zmslightbox');
	handle_zmslightbox_history();
};

// REMOVAL
function remove_zmslightbox(evt_from_history) {
	evt_from_history = evt_from_history || false;
	$('meta[name="viewport"]').attr('content',zlb_viewport);
	$('#zmslightbox').remove();
	$('body > #zmslightbox-mask').contents().unwrap();
	$('body').removeClass('zmslightbox');
	$('body').removeClass('masked');
	$('html, body').scrollTop( zmslightbox_obj.offset().top );
	if (!evt_from_history) { history.back() };
};

// CENTERING
function center_zmslightbox(imgobj) {
	zlb_ww = $(window).width();
	zlb_wh = $(window).height();
	zlb_wt = $(window).scrollTop();
	zlb_cx = zlb_ww/2;
	zlb_cy = zlb_wt + zlb_wh/2;
	zlb_iw = imgobj.width();
	zlb_ih = imgobj.height();
	if ( zlb_wh > $('body').height() ) {
		$('#zmslightbox-bg').css('height', zlb_wh+'px');
	} else {
		$('#zmslightbox-bg').css('height',$('body').height()+'px');
	};
	if ( zlb_ih > zlb_wh && !( imgobj.hasClass('fullimage') ) ) {
		imgobj.css('height',$(window).height() + 'px');
		zlb_iw = imgobj.width();
		zlb_ih = imgobj.height();
	} else {
		imgobj.css('height','auto');
	};
	var zlb_c_il = zlb_cx-(zlb_iw/2);
	var zlb_c_it = zlb_cy-(zlb_ih/2);
	$('#zmslightbox-wrapper').css('top',zlb_c_it + 'px');
	if ( zlb_ih + zlb_c_it > $(window).height() && $('body').hasClass('masked') ) {
		$('#zmslightbox-wrapper').css('top',0);
	};
	$('#zmslightbox-wrapper img').show('slow');
};

// SUPERSIZING
// Show modal content exclusively to allow window scrolling
function release_zmslightbox(){
	if ($('meta[name="viewport"]')) {
		$('meta[name="viewport"]').attr('content','width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no');
	} else {
		$('head').append('<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no" />');
	}
	$('body').addClass('masked');
	$('body > #zmslightbox-mask').hide();
	$('#zmslightbox-wrapper').css('top',0);
	$('#zmslightbox-bg').css('height','100%');
	zlb_wt = 0;
};

// NAVIGATE NEXT/PREVIOUS IMAGE
function get_next_zlb(this_img='', dir='next') {
	// remove_zmslightbox();
	$('#zmslightbox').remove();
	$('body > #zmslightbox-mask').contents().unwrap();
	$('body').removeClass('zmslightbox');
	$('body').removeClass('masked');
	var hireslist = $('.ZMSGraphic img').map(function(){
		return $(this).attr('data-hiresimg');
	}).get();
	var i = hireslist.indexOf(this_img);
	if ( dir=='next' ) {
		if ( i < (hireslist.length - 1) ) {
			$('.ZMSGraphic img[data-hiresimg="' + hireslist[i+1] + '"]').click();
		} else {
			console.log('Reached end of image list');
		};
	} else {
		if ( i > 0 ) {
			$('.ZMSGraphic img[data-hiresimg="' + hireslist[i-1] + '"]').click();
		} else {
			console.log('Reached end of image list');
		};
	};
};

// HANDLE WINDOW EVENTS:
// Resize, Device Rotation, History-Back
$(window).resize(function() {
	try {
		center_zmslightbox($('#zmslightbox-wrapper img'))
	} catch(err) {
		return false;
	}
});
window.onorientationchange = function() {
	try {
		center_zmslightbox($('#zmslightbox-wrapper img'))
	} catch(err) {
		return false;
	}
};
$(document).on('keyup',function(evt) {
	if ( ( $('#zmslightbox-wrapper').length > 0 ) && ( evt.keyCode ==27 || evt.keyCode == 8 ) ) {
		remove_zmslightbox();
	};
});
function handle_zmslightbox_history() {
	if (typeof history.pushState === 'function') {
		history.pushState(null, 'ZMSLightBox', null);
		window.onpopstate = function () {
			if ($('#zmslightbox') ) {
				// HISTORY.BACK TO CONTENT PAGE
				remove_zmslightbox(evt_from_history=true);
			};
		};
	};
};


// #################################
// EXECUTION
// #################################
function show_zmslightbox(img) {
	zmslightbox_obj = img;
	add_zmslightbox(img.attr('data-hiresimg'));
	$('#zmslightbox-wrapper img').on('load', function() {
		center_zmslightbox($('#zmslightbox-wrapper img'));
	});
	$('#zmslightbox-wrapper').attr('title',img.closest('.ZMSGraphic').find('.text').text());
};
