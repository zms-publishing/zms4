test( "zmi.internal.js::testRelativateUrl", function() {
	var relurl = $ZMI.relativateUrl("/kunden/tagwerk/content/impressum/","","http://office.taenzer.de:9080/kunden/tagwerk/content/e221");
	equal( relurl, "./../impressum/", "Passed!" );
	var relurl = $ZMI.relativateUrl("http://server/content/e2/e3","","/content/e1");
	equal( relurl, "./../e2/e3", "Passed!" );
	var relurl = $ZMI.relativateUrl("http://server/content/e2/e3","","http://server/content/e1");
	equal( relurl, "./../e2/e3", "Passed!" );
	var relurl = $ZMI.relativateUrl("http://server/content/e1/e3","","http://server/content/e1");
	equal( relurl, "./e3", "Passed!" );
	var relurl = $ZMI.relativateUrl("http://server/content/e2/e3","","http://server/content/e1/e4/e5");
	equal( relurl, "./../../../e2/e3", "Passed!" );
	var relurl = $ZMI.relativateUrl("http://server/content/e2/e3","#e6","http://server/content/e1/e4");
	equal( relurl, "./../../e2/e3#e6", "Passed!" );
});
