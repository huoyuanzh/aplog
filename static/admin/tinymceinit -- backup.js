tinyMCE.init({
	mode : "exact",
	elements:"content",
	theme : "advanced",
	plugins : "safari,pagebreak,style,layer,table,save,advhr,advimage,advlink,emotions,inlinepopups,insertdatetime,media,searchreplace,paste,directionality,fullscreen,nonbreaking,xhtmlxtras,template,prettify,wordpress,wpeditimage",

	theme_advanced_buttons1:"bold,italic,strikethrough,|,bullist,numlist,blockquote,|,forecolor,backcolor,|,justifyleft,justifycenter,justifyright,|,link,unlink,image,code,|,wp_more,fullscreen,prettify,wp_adv",
    theme_advanced_buttons2:"styleselect,formatselect,fontselect,fontsizeselect,underline,justifyfull,forecolor,|,pastetext,pasteword,removeformat",
    theme_advanced_buttons3:"media,charmap,emotions,|,outdent,indent,|,undo,redo",
    theme_advanced_buttons4:"",
	theme_advanced_toolbar_location : "top",
	theme_advanced_toolbar_align : "left",
	theme_advanced_statusbar_location : "bottom",
	theme_advanced_resizing : true,
	language : "ch",
	content_css : "/tinymce/wordpress.css"
});