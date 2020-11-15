/**
 * $ZMI: Register functions to be executed on document.ready 
 */
ZMI = function() { this.readyFn = []};
ZMI.prototype.registerReady = function(fn) {this.readyFn.push(fn)};
ZMI.prototype.ready = function(fn) {this.readyFn.push(fn)};
ZMI.prototype.runReady = function() {this.readyFn.map(x=>x())};
$ZMI = new ZMI();

/**
 * $: Register 
 */
if (typeof $ == "undefined") {
	$ = function(arg0, arg1) {
		if (typeof arg0 == "function") {
			$ZMI.registerReady(arg0);
		}
		return $ZMI;
	}
}

/**
 * Turbolinks
 */
if (typeof Turbolinks != "undefined") {
	Turbolinks.setProgressBarDelay(0);
	document.addEventListener("turbolinks:visit", function() {
		var ts = performance.now();
		console.log("BO turbolinks:visit " + ts);
	});
	document.addEventListener("turbolinks:load", function() {
		var ts = performance.now();
		console.log("BO turbolinks:load " + ts);
		$ZMI.runReady();
		console.log("EO turbolinks:load " + ts + "->" + (performance.now()-ts) + "msec");
	});
}
