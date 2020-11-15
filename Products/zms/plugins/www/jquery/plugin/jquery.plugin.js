/*****************************************************************************
 * $.plugin - jQuery Plugin for on-demand loading of scripts and styles
 *
 * Documentation : http://nicolas.rudas.info/jQuery/getPlugin/
 * Downloads	 : http://code.google.com/p/lazyloader/downloads/
 * Issues		 : http://plugins.jquery.com/project/getPlugin/
 *
 * Version: 081002 - 02 Oct 2008
 *
 * ====================================================
 ** USAGE:
 * ====================================================
 * $.plugin(name,settings)		Create a new plugin with specified name and settings
 * $.plugin(name)				Access to plugin object
 * $.plugin(name).get()			Load specified plugin and call default callback when ready
 * $.plugin(name,function)		Load specified plugin and call function when ready (overide default callback)
 * $.plugin()					Load all necessary plugins
 *
 * ====================================================
 ** OPTIONS:
 * ====================================================
 *	@param name 		{String}	What you want to name your plugin
 *
 *	@param settings 	{Object}	The settings for this plugin
 *									- 	files		{Array,String}		List of files you want to load
 *									-	selectors	{Array,String}		If elements match these selector, the plugin will be loaded
 *									-	callback	{Function}			Function to be called after a plugin has loaded
 *									-	cache		{Boolean}			Cache files in browser's memory
 *									-	ajax		{Object}			Ajax options (same as in jQuery.ajax)
 *									-	context		{Object, jQuery}	The document where you want files to be inserted
 *									-	target		{Object, jQuery}	The element where you want files to be inserted
 *									-	init		{Function}			Function to be called when setting-up plugin
 *									-	preLoad		{Function}			Function to be called before loading each file
 *									-	postLoad	{Function}			Function to be called after loading each file
 *
 *	@param callback 	{Function}	A Function to call after plugin has loaded. Overrides default callback
 *									
 * ====================================================
 ** API:
 * ====================================================
 * $.plugin(name)
 *				.get([callback])	Load specified plugin and call callback when ready
 *									If no callback specified, default callback is called
 *									
 *				.getFile(url)		Load specified file and call default callback when ready
 *
 *				.isNeeded()			Check if plugin is needed (according to selectors provided)
 *									Returns TRUE if it is needed, otherwise returns plugin object
 *
 * ====================================================
 ** EXAMPLES:
 * ====================================================
 * Create a Tabs Plugin:
 *		$.plugin('tabs',{
 *			files: ['../styles/tabs.css',
 *					'../scripts/tabs.js'],
 *			selectors: ['.tabs'],
 *			callback : function(){ $('.tabs').tabs(); } 
 *		});
 *		
 *		$.plugin('tabs').get();
 *
 * Create a Loader Plugin:
 *		$.plugin('loader',{
 *			files: 		['../styles/mystyles.css',
 *						'../scripts/myscript.js',
 *						'../scripts/myscript2.js',
 *						'../scripts/myscript3.js']
 *			selectors:	['body'],
 *			init		: 	function(url){ $('body').append('<ol id="now-loading"></ol>'); },
 *			preLoad		:	function(url){
 *								$('#now-loading').append('<li data-file="'+url+'">Loading: '+url+'</li>')
 *						},
 *			postLoad	:	function(url){
 *								$( 'li[data-file="'+url+'"]' , '#now-loading').css('text-decoration','line-through') });
 *						}
 *		});
 *		
 *		$.plugin('loader',function(){ $('#now-loading').remove(); });
 *
 ******************************/

// Storage objects
	$.plugins = $.plugins || {};
	$.plugins.cache = window.sessionStorage || {};
// Default Settings	
	$.plugins.settings = {
		cache : true,
		ajax : { cache : true },
		context : $(document),
		target : $('head',this.context),
		init : function(){},
		preLoad : function(){},
		postLoad : function(){}
	};
	
	var defaults = $.plugins.settings,
		cache = $.plugins.cache;

// Plugin Constructor
	Plugin = function(name /* string */,settings /* object literal*/){
		var that = this;
		this.name = name;
		for(var i in settings) { that[i] = settings[i]; };
		this.context = this.context || settings.context;
		this.target = this.target || settings.target;
		this.loaded = {};
		this.queue = [];
		this.tmp_callback = [];
		
		this.init.apply(this);
		
		return this;
	};
		
	Plugin.prototype.getFile = function(url /* string */){
		if(!url || typeof url != 'string') { throw new Error('$.plugin.getFile(url) - url {String} must be specified') ;}
		var that = this,
			extension = url.split('.')[url.split('.').length-1],
			fileId = url.replace(/\W/gi,''),
			cached = cache[url],
			caching = (defaults.cache === true || defaults.cache == 'true');
		if(extension.indexOf('?')>0) {
			extension = extension.substr(0,extension.indexOf('?'));
		}
		if(extension != 'css' && extension != 'js') {
			throw new Error( '$.plugin.getFile(url) - Invalid extension:'+ extension + '\n\t'+url); return this;}
			
		// Ignore if caching is enabled and file has already been loaded
		if(caching && this.loaded[url]) {
			return this;
		}
		
	// Call Preload callback (queueing etc)
		this.beforeGet(url);
		
	// Remove previously appended files from DOM	
		$('[data-file-id="'+fileId+'"]').remove();
		

	// If caching is enabled and file is cached
	// Note: External files are not cached
		if(caching && cached && cached != 'undefined') {
			if(extension == 'css') {
				var base_url = url.substr(0,url.lastIndexOf('/')+1);
				this.target.append('<style type="text\/css" rel="stylesheet" data-file-id="'+fileId+'">'+cached+'<\/style>');
			}
			else if(extension == 'js') {
				this.target.append('<script type="text\/javascript" async="true" data-file-id="'+fileId+'">'+cached+'<\/script>');
			}
				
		// Call postLoad callback (queueing etc)
		// Timeout needed to make sure that queue of files (this.queue) has correct value
			setTimeout(function(){that.afterGet(url);},1);
			
	// If no caching or file is not cached
		} else {
			
		// Handle Styles	
			if(extension == 'css') {
				$.get(url,function(response) {
						var base_url = url.substr(0,url.lastIndexOf('/')+1);
						response = response.replace(/url\(\'/g,'url(\''+base_url);
						response = response.replace(/AlphaImageLoader\(src\=\'/g,'AlphaImageLoader(src=\''+base_url);
						that.loaded[url] = true;
						cache[url] = response;
						that.target.append('<style type="text\/css" rel="stylesheet" data-file-id="'+fileId+'">'+response+'<\/style>');
						that.afterGet(url);
				});
			}
		// Handle Scripts	
			else if(extension == 'js') {
				(function(){
					var opts = $.extend({dataType: "script",url: url},defaults.ajax),
						onSuccess = opts.success || function(){};
					
					opts.success = function(){
						onSuccess.apply(this,arguments);
						
						var response = (typeof arguments[0] == 'string') ? arguments[0] : null;
						cache[url] = response;
						that.loaded[url] = true;
						that.afterGet(url);
					};
					
					$.ajax(opts);
				})();
			}
		}
		
		return this;
	};
	
	Plugin.prototype.beforeGet = function(url/* string */){
	// Push this file in waiting queue
	// Queue is used to know which files are waiting to be loaded
	// Load Callback for each plugin is called only when all files have loaded
		this.queue.push(url);
	
	// Call preload callback
		defaults.preLoad.call(this,url);
		return this;
	};
	
	Plugin.prototype.afterGet = function(url/* string */){
		var that = this,
			index = $.inArray(url,this.queue);
			
	// Try to catch some weird situtation
	// where postLoad is called for a file that was not in queue
		if(index == -1) {
			throw new Error('$.plugin.afterGet(url) - Ignoring postLoad for file that should not be in queue:\n '+url); return this; }
	
	// Remove file from waiting queue
		this.queue.splice(index,1);
		
	// If no other files in queue, call callback
	// Timeout needed to make sure that callback is called
	// after files have been parsed by browser
		if(this.queue.length == 0) {
			this.run();
		}
	
	// Call postLoad callback
		defaults.postLoad.call(this,url);
		
		return this;
	};

	Plugin.prototype.run = function(){
		var that = this;
		for (var i=0;i<this.tmp_callback.length;i++) {
			(function(){
				var callback = that.tmp_callback[i];
				setTimeout(function(){callback.apply(that);},1);
			})();
		}
		this.tmp_callback = [];
	}

	Plugin.prototype.set = function(settings){
		var that = this;
		for (var key in settings) {
			that[key] = settings[key];
		}
	}

	Plugin.prototype.get = function(){
		var that = this,
			files = (typeof this.files == 'string') ? [this.files] : this.files,
			callback = arguments[1] || this.callback;
 		this.selectors = arguments[0] || this.selectors;
		
		// Do not load files if they are not needed
		if(this.isNeeded() !== true) {
			return this;
		}
		
		// Store Load callback
		// This will be called when all files have finished loading
		this.tmp_callback.push( callback);
		
		// Do not load files if they are already queued
		this.files = [];
		if (files.length == this.queue.length) {
			if(this.queue.length == 0) {
				this.run();
			}
			return this;
		}
		
		// Load each file specified for this plugin
		var getFile = function(file){that.getFile(file);};
		var that = this;
		for(var i=0;i<files.length;i++){
			(function(){
				var file = files[i];
				getFile(file);
			})();
		}
		
		return this;
	};
	
	Plugin.prototype.isNeeded = function(){
		var that = this,
			selectors = (typeof this.selectors == 'string') ? [this.selectors] : this.selectors,
			isNeeded;
	// If at least one selector matches return true
	// and don't go through the rest
		for(var i=0;i<selectors.length;i++){
			var selector = selectors[i];
			if( $(selector,that.context).length > 0 ) { isNeeded = true; break; }
		};
		
	// Return true if its needed, otherwise plugin instance
		return isNeeded || this;
	};
	
	$.extend($, {		
		plugin : function(name /* string */,param /* object literal or function */){
			var self = $.plugin;
		// If no arguments passed, get all plugins		
			if (arguments.length == 0) {
				for(var i in $.plugins) { if(i == 'settings' || i == 'cache') { continue;} $.plugins[i].get();};
				return self; }
				
		// First argument must be a string, the plugin's name
			else if ( typeof name != 'string' ) {
				throw new Error('$.plugin(name,[settings||callback])\n\t\t@param name\t\t{String}\n\t\t@param settings\t{Object}\n\t\t@param callback\t{Function}');
				
				return self; }
				
		// When settings provided, create a new Plugin
			if(typeof param == 'object' && typeof $.plugins[name] == 'undefined') {
				var plugin = $.plugins[name];
				if(typeof plugin != 'object') {
					$.plugins[name] = new Plugin(name,$.extend(defaults,param));
				}
			}
		// Otherwise either return plugin instance or get plugin's files
			else { 
				var plugin = $.plugins[name];
				if(typeof plugin != 'object') { throw new Error('$.plugin: '+name+' is not specified'); return self; }
			// When function provided, get specified plugin
				if(typeof param == 'function') {plugin.get(param);}
			// Otherwise, return plugin object	
				else if(!param) { return plugin; }
			}
			
			return self;
		},
	// Backwards compatibility
		getPlugin : function(){ return $.plugin.apply(this,arguments);	}
	});
