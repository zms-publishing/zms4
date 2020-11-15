test( "zmi.core.js::test.String.prototype", function() {
	var s0 = "  ab c  ";
	equal( s0.removeWhiteSpaces(), "abc", "removeWhiteSpaces passed!" );
	equal( s0.leftTrim(), "ab c  ", "leftTrim passed!" );
	equal( s0.rightTrim(), "  ab c", "rightTrim passed!" );
	equal( s0.basicTrim(), "ab c", "basicTrim passed!" );
	equal( s0.superTrim(), "ab c", "superTrim passed!" );
	var s1 = "abcdefghijk";
	ok( s1.startsWith("abc"), "startsWith passed!" );
	ok( !(s1.startsWith("xyz")), "!startsWith passed!" );
	ok( s1.endsWith("ijk"), "endsWith passed!" );
	ok( !(s1.endsWith("xyz")), "!endsWith passed!" );
});

test( "zmi.core.js::test.Array.prototype", function() {
	var a0 = ['a','b','c','b',1,2,3];
	equal( a0.indexOf('b'), 1, "indexOf passed!" );
	equal( a0.lastIndexOf('b'), 3, "lastIndexOf passed!" );
	ok( a0.contains('b'), "contains passed!" );
	ok( !a0.contains('d'), "!contains passed!" );
});

test( "zmi.core.js::test.ZMI", function() {
	equal($ZMI.getLangStr("DC.Creator"), "Autor", "getLangStr(key,lang) passed!" );
	equal($ZMI.getLangStr("DC.Creator","ger"), "Autor", "getLangStr(key,lang) passed!" );
	equal(getZMILangStr("DC.Creator"), "Autor", "getZMILangStr(key) passed!" );
	equal(getZMILangStr("ATTR_ATTRS"), "Attribute", "getZMILangStr(key) passed!" );
});
