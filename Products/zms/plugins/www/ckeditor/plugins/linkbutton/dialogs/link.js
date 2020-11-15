var zmiDialog = null;
var data_id = null;

/**
 * Select object.
 */
function zmiSelectObject(sender) {
  var uid = $(sender).attr('data-uid');
  var abs_url = $(sender).attr('data-link-url');
  data_id = uid;
  zmiDialog.getContentElement('info', 'url').setValue(abs_url);
  zmiDialog.click("ok");
  return false;
}

/**
 * Resize object.
 */
function zmiResizeObject() {
  var $myDiv = $("#myDiv");
  var $cke_dialog = $myDiv.parents(".cke_dialog");
  var $cke_dialog_footer = $(".cke_dialog_footer",$cke_dialog);
  var height = $cke_dialog_footer.offset().top-$myDiv.offset().top-10;
  $myDiv.css("height",height);
}

CKEDITOR.dialog.add( 'linkbuttonDlg', function( editor )
{
  var plugin = CKEDITOR.plugins.linkbutton,
      p = function() {
          var a = this.getDialog(),
            b = a.getContentElement("target", "popupFeatures"),
            a = a.getContentElement("target", "linkTargetName"),
            m = this.getValue();
            if (b && a)
              switch (b = b.getElement(), b.hide(), a.setValue(""), m) {
                default:
                  a.setValue(m), a.getElement().hide()
              }
        };

  var parseLink = function( editor, element )
  {
    var href = '',
      retval = {};
    // Record down the selected element in the dialog.
    this._.selectedElement = element;
    return retval;
  };

  var commonLang = editor.lang.common,
    linkLang = editor.lang.link;

  return {
    title : getZMILangStr('CAPTION_CHOOSEOBJ'),
    minWidth : 450,
    minHeight : 360,
    contents : [
      {
        id : 'info',
        label : linkLang.info,
        title : linkLang.info,
        elements :
        [
          {
            type: "hbox",
            widths: ["25%", "75%"],
            children: [
              {
                id: "linkType",
                type: "select",
                label: linkLang.type,
                required: true,
                "default": "url",
                items: [
                    [linkLang.toUrl, "url"],
                    [linkLang.toEmail, "email"]
                  ],
                commit: function(data) {
                    data.type = this.getValue();
                  }
              },
              {
                id : 'url',
                type : 'text',
                label : commonLang.url,
                required: true,
                onLoad : function () {
                  this.allowOnChange = true;
                  zmiDialog = this.getDialog();
                  zmiDialog.on("resize",function(event){zmiResizeObject()});
                  zmiResizeObject();
                  var href = self.location.href;
                  href = href.substr(0,href.lastIndexOf("/"));
                  $ZMI.objectTree.init("#myDiv",href,{'toggleClick.callback':'zmiResizeObject'});
                   // Workaround for ZMSINSERT case
                  urllabel0 = $('body.zmi.modal-open .cke_dialog_body label')[0];
                  urllabel1 = $('body.zmi.modal-open .cke_dialog_body label')[1];
                  $(urllabel0).html('<span style="color:silver;font-weight:normal">Link-Typ</span>')
                  $(urllabel1).html('<span style="color:silver;font-weight:normal">URL</span> erst &auml;nderbar, wenn Textabschnitt eingef&uuml;gt wurde')
                },
                validate : function() {
                  var dialog = this.getDialog();
                  var func = CKEDITOR.dialog.validate.notEmpty( linkLang.noUrl );
                  return func.apply( this );
                },
                setup : function( data ) {
                  this.allowOnChange = false;
                  if ( data.url )
                    this.setValue( data.url.url );
                  this.allowOnChange = true;
                },
                commit : function(data) {
                  if ( !data.url )
                    data.url = {};
                  data.url.url = this.getValue();
                  this.allowOnChange = false;
                }
              }
            ]
          },
          {
            type: 'html',
            html : '<div id="myDiv" class="zmi-sitemap" style="overflow:auto"></div>'
          }
        ]
      },
      {
        id : 'target',
        label : linkLang.target,
        title : linkLang.target,
        elements : [{
            type: "select",
            id: "linkTargetType",
            label: commonLang.target,
            "default": "notSet",
            style: "width : 100%;",
            items: [
                [commonLang.notSet, "notSet"],
                [commonLang.targetNew, "_blank"],
                [commonLang.targetTop, "_top"],
                [commonLang.targetSelf, "_self"],
                [commonLang.targetParent, "_parent"]
              ],
            onChange: p,
            setup: function(data) {
                data.target && this.setValue(data.target.type || "notSet");
                p.call(this)
              },
            commit: function(data) {
                data.target || (data.target = {});
                data.target.type = this.getValue()
              }
            }
        ]
      }
    ],
    onShow : function()
    {
      var editor = this.getParentEditor(),
        selection = editor.getSelection(),
        element = null;

      // Fill in all the relevant fields if there's already one link selected.
      try {
        if ( ( element = plugin.getSelectedLink( editor ) ) && element.hasAttribute( 'href' ) )
          selection.selectElement( element );
        else
          element = null;
      } catch(err) {
        element = null;
      }

      this.setupContent( parseLink.apply( this, [ editor, element ] ) );
    },
    onOk : function()
    {
      var attributes = {},
        data = {},
        me = this,
        editor = this.getParentEditor();
      
      this.commitContent( data );
      
      // Compose the URL.
      var linkType = data.type;
      var url = ( data.url && CKEDITOR.tools.trim( data.url.url ) ) || '';
      var target = ( data.target && CKEDITOR.tools.trim( data.target.type ) ) || '';
      if (url.indexOf("<") == 0) {
        var element = CKEDITOR.dom.element.createFromHtml(url);
        editor.insertElement(element);
      }
      else {
        if (linkType == 'email' && (url.indexOf('mailto:')<0)) {
          var enc = [];
          for (var i = 0; i < url.length; i++) {
            enc.push(url.charCodeAt(i));
          }
          url = 'javascript:void(location.href=\'mailto:\'+String.fromCharCode('+enc.join()+'))';
        }
        if (linkType == 'url' && (url.indexOf('.')!=0 && url.indexOf('://')<0)) {
          url = 'http://'+url;
        }
        if (data_id != null) {
        	attributes[ 'data-id' ] = data_id;
        }
        attributes[ 'href' ] = url;
        if (target != "notSet") {
          attributes[ 'target' ] = target;
        }
        // Create element if current selection is collapsed.
        var selection = editor.getSelection();
        var b = selection.getRanges()[0];
        if (b.collapsed ) {
          var a = new CKEDITOR.dom.text( url, editor.document );
          b.insertNode(a);
          b.selectNodeContents(a);
        }
        // Apply style.
        var g = editor.document;
        var c = new CKEDITOR.style( { element : 'a', attributes : attributes } );
        c.type = CKEDITOR.STYLE_INLINE;   // need to override... dunno why.
        c.applyToRange(b,g);
        b.select();
      }
    }
  };
});