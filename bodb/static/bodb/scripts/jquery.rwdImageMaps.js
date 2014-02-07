/*
* rwdImageMaps jQuery plugin v1.5
*
* Allows image maps to be used in a responsive design by recalculating the area coordinates to match the actual image size on load and window.resize
*
* Copyright (c) 2013 Matt Stow
* https://github.com/stowball/jQuery-rwdImageMaps
* http://mattstow.com
* Licensed under the MIT license
*/
;(function($) {
	$.fn.rwdImageMaps = function() {
		var $img = this;
		
		var rwdImageMap = function() {
			$img.each(function() {
                if (typeof($(this).attr('usemap')) == 'undefined' || $(this).attr('class')=='panButton')
					return;
				var that = this,
					$that = $(that);
				
				// Since WebKit doesn't know the height until after the image has loaded, perform everything in an onload copy
				$('<img />').load(function() {
                    var attrW = 'origWidth',
						attrH = 'origHeight',
						w = $that.attr(attrW),
						h = $that.attr(attrH);
                    if (!w || !h) {
						var temp = new Image();
						temp.src = $that.attr('src');
						if (!w)
							w = temp.width;
						if (!h)
							h = temp.height;
					}

					var wPercent = $that.width()/100,
						hPercent = $that.height()/100,
						map = $that.attr('usemap').replace('#', ''),
						c = 'coords';
					$('map[name="' + map + '"]').find('area').each(function() {
                        var $this = $(this);
						if (!$this.data(c))
							$this.data(c, $this.attr(c));
						
						var coordPairs = $this.data(c).split(' ');
                        var newCoordString = '';
						for (var i = 0; i < coordPairs.length; ++i) {
                            var coord=coordPairs[i].split(',');
                            if(i>0)
                                newCoordString+=' ';
                            newCoordString+=Math.round(((coord[0]/w)*100)*wPercent)+","+Math.round(((coord[1]/h)*100)*hPercent);
						}
                        $this.attr(c, newCoordString);
					});
				}).attr('src', $that.attr('src'));
			});
		};
		$(window).resize(rwdImageMap).trigger('resize');
		
		return this;
	};
})(jQuery);