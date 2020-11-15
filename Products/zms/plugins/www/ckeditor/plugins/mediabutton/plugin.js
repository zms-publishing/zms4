/**
 * @see http://www.pro4j.de/erstellen-eines-plugins-fur-den-ckeditor-30
 * @see http://docs.ckeditor.com/#!/guide/plugin_sdk_integration_with_acf
 */
CKEDITOR.plugins.add('mediabutton', {
	init : function( editor )
	{
		editor.addCommand( 'mediabuttonDlg', new CKEDITOR.dialogCommand( 'mediabuttonDlg', {
					allowedContent:'img[!src]'
				}
		) );
 
		editor.ui.addButton( 'mediabutton',
			{
				label : getZMILangStr('BTN_UPLOAD')+'/'+getZMILangStr('BTN_INSERT'),
				command : 'mediabuttonDlg',
				icon: this.path+'images/media-button.png'
			});

		CKEDITOR.dialog.add( 'mediabuttonDlg', this.path+'dialogs/link.js?ts='+new Date());

	}
});
