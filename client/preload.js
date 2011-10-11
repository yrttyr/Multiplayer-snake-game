"use strict";

(function Preload() {
	window.preload = {
		'images': {},
		'imgAmount': 0,
		'imgEndLoadAmount': 0,
		'imgLoadComplete': function(e) {
			preload.imgEndLoadAmount += 1;
			preload.testAllLoad();
		},
		'testAllLoad': function() {
			if(this.imgEndLoadAmount === this.imgAmount) {	
				this.callback(this.images);
				delete window.this;
			}
		},
		'start': function (imageList, callback) {
			this.callback = callback;
			this.imgAmount = imageList.length
			this.searchImage(imageList);
		},
		'searchImage': function (imageList) {
			for(var folderName in imageList) {
				this.loadImg(imageList[folderName]);
			}
		},
		'loadImg': function (fullPath) {
			function createDict(obj, path) {
				var direct = path.pop();
				if(direct) {
					if(! (direct in obj)) {
						obj[direct] = {};
					}
					return createDict(obj[direct], path);	
				}
				return obj;
			}
			//console.error(fullPath);
			var path = fullPath.split('/');
			var name = /(.+).png/.exec(path.pop())[1];
			path.reverse();
			var obj = createDict(this, path);

			obj[name] = new Image();
			obj[name].onload = this.imgLoadComplete;
			obj[name].onerror = function() {console.error('Load Image Error');};
			obj[name].src = fullPath;
		}
	};
})();
