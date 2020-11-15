	$(function() {
		if ( $('.prettyTextDiff').length > 0 ) {
			$('#repo-changesets').prepend('<h4>Changesets</h4>');
		}
		$(".prettyTextDiff").each(function() {
			var diffContainer = ".diff";
			$(this).prettyTextDiff({
				cleanup:true,
				originalContainer:".original",
				changedContainer:".changed",
				diffContainer:diffContainer
			});
			var $diffContainer = $(diffContainer,this);
			var lines = $diffContainer.html().replace(/<span>/gi,'').replace(/<\/span>/gi,'').split("<br>");
			var show = [];
			var changed = false;
			for (var i = 0; i < lines.length; i++) {
				var line = lines[i];
				changed |= line.indexOf("<"+"del>")>=0 || line.indexOf("<ins>")>=0;
				if (changed) {
					show.push(i);
				}
				changed &= !(line.indexOf("<"+"/del>")>=0 || line.indexOf("</ins>")>=0);
			}
			var html = [];
			changed = false;
			for (var i = 0; i < lines.length; i++) {
				var line = lines[i];
				changed |= line.indexOf("<"+"del>")>=0 || line.indexOf("<"+"ins>")>=0;
				line = '<'+'span class="line-number'+(changed?' line-changed':'')+'">'+(i+1)+'</span> '+lines[i];
				if (!(show.contains(i-1) || show.contains(i) || show.contains(i+1))) {
					line = '<'+'span class="diff-unchanged d-none">'+line+'<'+'/span>';
				}
				else {
					line = line+'<'+'br/>';
				}
				html.push(line);
				changed &= !(line.indexOf("<"+"/del>")>=0 || line.indexOf("<"+"/ins>")>=0);
			}
			$diffContainer.html(html.join(""));
			$("strong",$(this).closest("tr").prev("tr")).addClass("zmi-helper-clickable").click(function() {
				if ($(".diff-unchanged.d-none",$diffContainer).length > 0) {
					$(".diff-unchanged",$diffContainer).removeClass("d-none").after("<br>");
				}
				else if ($(".diff-unchanged",$diffContainer).length > 0) {
					$(".diff-unchanged",$diffContainer).addClass("d-none").next("br").remove();
				}
			});
		});
	});
	function focus_anchorid(anchorid) {
		$('.table.focus').removeClass('focus');
		$(document).scrollTop( $(anchorid).offset().top );
		$(anchorid).addClass('focus');
	}
