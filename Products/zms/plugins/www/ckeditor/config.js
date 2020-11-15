/**
 * @license Copyright (c) 2003-2016, CKSource - Frederico Knabben. All rights reserved.
 * For licensing, see LICENSE.md or http://ckeditor.com/license
 */

CKEDITOR.editorConfig = function( config ) {
	// Define changes to default configuration here.
	// For complete reference see:
	// http://docs.ckeditor.com/#!/api/CKEDITOR.config
	config.emailProtection = 'encode';
	// config.forcePasteAsPlainText = true
	config.skin = 'bootstrapck';
	// Make dialogs simpler.
	config.removeDialogTabs = 'image:advanced;link:advanced';
	// Linkbutton
	// Mediabutton
	// @see http://stackoverflow.com/questions/1957156/ckeditor-how-to-add-a-custom-button-to-the-toolbar-that-calls-a-javascript-funct
	config.extraPlugins = 'linkbutton,mediabutton';
	//  Toolbar: 
	// @see http://docs.ckeditor.com/#!/guide/dev_toolbar
	// @see http://ckeditor.com/apps/ckeditor/4.4.0/samples/plugins/toolbar/toolbar.html
	config.toolbar = 'ZMSBasicToolbar';
	config.toolbar_ZMSBasicToolbar = [
		{ name: 'styles',      items: [ 'Format' ] },
		{ name: 'paragraph',   items: ['Bold','Italic','Underline','JustifyLeft','JustifyCenter','JustifyRight','NumberedList','BulletedList','Outdent','Indent'] },
		{ name: 'undo',        items: [ 'Undo', 'Redo' ] },
		{ name: 'editing',     items: [ 'Find' ] }, //'/', <== Line-Break
		{ name: 'links',       items: [ 'linkbutton', 'Unlink' ] },
		{ name: 'insert',      items: [ 'Anchor', 'Table' ] },
		{ name: 'tools',       items: [ 'Source', 'ShowBlocks', 'Maximize', 'Scayt', '-', 'About' ] }
	];
	config.toolbar_ZMSBasicInsertToolbar = [
		{ name: 'styles',      items: [ 'Format' ] },
		{ name: 'paragraph',   items: ['Bold','Italic','Underline','JustifyLeft','JustifyCenter','JustifyRight','NumberedList','BulletedList','Outdent','Indent'] },
		{ name: 'undo',        items: [ 'Undo', 'Redo' ] },
		{ name: 'tools',       items: [ 'Source', 'ShowBlocks', 'Maximize', 'Scayt', '-', 'About' ] }
	];
	var prefix = "ckeditor.config";
	var confProperties = $ZMI.getConfProperties(prefix);
	for (var k in confProperties) {
		var v = confProperties[k];
		var k = k.substr((prefix+".").length);
		// Toolbar
		if (k.indexOf("toolbar.")==0) {
			var name = k.substr("toolbar.".length);
			for (var ck in config) {
				if (ck.indexOf("toolbar_")==0) {
					var found = false;
					for (var i=0; i<config[ck].length; i++) {
						if (config[ck][i]["name"]==name) {
							config[ck][i]["items"] = v.split(",");
							found = true;
							break;
						}
					}
					if (!found) {
						config[ck].push({name:name,items:v.split(",")});
					}
				}
			}
		}
		// Other
		else {
			config[k] = v;
		}
	}

	// Set the most common block elements.
	$ZMI.CKEDITOR_editorConfig(config);
};

CKEDITOR.on( 'dialogDefinition', function( event ) {
	var dialogDefinition = event.data.definition,
		genericOnShow = dialogDefinition.onShow;
	dialogDefinition.onShow = function() {
		genericOnShow.apply( this );
		var dialog = CKEDITOR.dialog.getCurrent();
		if (dialog.getName() == 'link') {
			subject = dialog.getContentElement('info','emailSubject');
			if (subject.getValue() == '') {
				subject.setValue(' ');
			}
		}
	}
});
