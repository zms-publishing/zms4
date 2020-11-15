var CKEditor_mediaCounter = 0;
var CKEditor_editor = null;

function CKEditor_uploadMediaDone() {
	CKEditor_mediaCounter++;
	var response = $('iframe#CKEditor_uploadMedia').contents().text();
	if (response) {
		var data = eval("("+response+")");
		var html = '';
		if (typeof data["imghires"] != "undefined") {
			html = '<a href="'+data["imghires"]["absolute_url"]+'" class="fancybox"><img src="'+data["image"]["absolute_url"]+'" alt="" class="image"/></a>';
		}
		else if (typeof data["image"] != "undefined") {
			html = '<img src="'+data["image"]["absolute_url"]+'" alt="" class="image"/>';
		}
		else if (typeof data["file"] != "undefined") {
			html = '<a href="'+data["file"]["absolute_url"]+'" target="_blank" class="file">'+data["file"]["filename"]+'</a>';
		}
		var element = CKEDITOR.dom.element.createFromHtml(html);
		CKEditor_editor.insertElement(element);
		CKEditor_editor = null;
	}
}

CKEDITOR.dialog.add( 'mediabuttonDlg', function( editor )
{
	var commonLang = editor.lang.common,
		linkLang = editor.lang.link;

	return {
		title : getZMILangStr('CAPTION_CHOOSEOBJ'),
		minWidth : 280,
		minHeight : 80,
		contents : [
			{
				id : 'info',
				label : linkLang.info,
				title : linkLang.info,
				elements :
				[
					{
						type : 'html',
						html : ''
							+ '<div id="mediaDialog">'
								+ '<iframe id="CKEditor_uploadMedia" name="CKEditor_uploadMedia" stc="" style="display:none" onload="CKEditor_uploadMediaDone()"></iframe>'
								+ '<form action="metaobj_manager/ZMSLib.uploadMedia" method="post" target="CKEditor_uploadMedia" enctype="multipart/form-data">'
								  + '<input type="hidden" name="form_id" value="'+$("form#form0 input[name=form_id]").val()+'"/>'
								  + '<input type="hidden" name="lang" value="'+$("form#form0 input[name=lang]").val()+'"/>'
								  + '<input type="hidden" name="key" value="' + CKEditor_mediaCounter + '"/>'
									+ '<table cellspacing="0">'
									+ '<colgroup>'
										+ '<col width="20%"/>'
										+ '<col width="80%"/>'
									+ '</colgroup>'
									+ '<tr id="tr_fileContainer"  valign="top">'
										+ '<td nowrap="nowrap" class="form-label"><img src="/++resource++zms_/img/upload.gif" border="0" style="vertical-align:middle" /></td>'
										+ '<td id="fileContainer" class="form-element"></td>'
									+ '</tr>'
									+ '</table>'
								+ '</form>'
							+ '</div>'
					}
				]
			}
		],
		onShow : function()
		{
			CKEditor_editor = this.getParentEditor();
			var html = ''
				+ '<input class="form-element" name="file" type="file" size="25">'
				+ '<div class="form-small">'
					+ '<input type="checkbox" id="thumbnail" name="thumbnail:int" value="1" checked="checked">'
					+ getZMILangStr('ACTION_GENERATE_PREVIEW')
				+'</div>';
			$('div#mediaDialog #fileContainer').html(html);
		},
		onOk : function()
		{
			if ($("div#mediaDialog input[name=file]").val()) {
				$("div#mediaDialog form").submit();
			}
		}
	};
});
