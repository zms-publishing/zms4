/**
 * @see http://www.pro4j.de/erstellen-eines-plugins-fur-den-ckeditor-30
 * @see http://docs.ckeditor.com/#!/guide/plugin_sdk_integration_with_acf
 */
CKEDITOR.plugins.add('linkbutton', {
	init : function( editor )
	{
		editor.addCommand( 'linkbuttonDlg', new CKEDITOR.dialogCommand( 'linkbuttonDlg', {
					allowedContent:'a[data-id,href,target]; img[data-id,src]'
				}
		) );
 
		editor.ui.addButton( 'linkbutton',
			{
				label : 'Link einfügen/editieren',
				command : 'linkbuttonDlg',
				icon: '/++resource++zms_/ckeditor/plugins/linkbutton/images/linkbutton.png'
			});
		CKEDITOR.dialog.add( 'linkbuttonDlg', this.path+'dialogs/link.js');

	}
});
