/*	
 *	jQuery zoom plugin
 *	Demo and documentation:
 *	http://e-smartdev.com/#!jsPluginList/panAndZoomJQuery
 *	
 *	Copyright (c) 2012 Damien Corzani
 *	http://e-smartdev.com/
 *
 *	Dual licensed under the MIT and GPL licenses.
 *	http://en.wikipedia.org/wiki/MIT_License
 *	http://en.wikipedia.org/wiki/GNU_General_Public_License
 */
(function( $ ){

  $.fn.smartZoom = function(method) {
    // define global vars
	var targetElement = this; // the element target of the plugin
	
	/**
	 * define public methods that user user could call 
	 */
    var publicMethods = {
    	/**
		  * initialize zoom component
		  * @param {Object} options = {'top': '0' zoom target container top position in pixel
		  * 						   'left': '0' zoom target container left position in pixel
		  * 						   'width' : '100%' zoom target container width in pixel or in percent
		  * 						   'height' : '100%' zoom target container height in pixel or in percent 
		  *                            'easing' : 'smartZoomEasing' jquery easing function used when the browser doesn't support css transitions
		  * 						   'maxScale' : 3 the max scale that will be applied on the zoom target
		  *							   'dblClickMaxScale' : 1.8 the max scale that will be applied on the zoom target on double click
		  *  				     	   'mouseEnabled' : true enable plugin mouse interaction 
		  *					           'scrollEnabled' : true enable plugin mouse wheel behviour
		  *					           'dblClickEnabled' : true enable plugin mouse doubleClick behviour
		  *					           'mouseMoveEnabled' : true enable plugin target drag behviour
		  * 					       'moveCursorEnabled' : true show moveCursor for drag
		  *                            'containerBackground' : '#FFFFFF' zoom target container background color (if containerClass is not set)
		  *                            'containerClass' : '' class to apply to zoom target container if you whant to change background or borders (don't change size or position via the class)
		  * 						  } 
		  */
	    init : function(options) {
	    	// is smartZoomData exists on the targetElement, we have already initialize it
	    	if(targetElement.data('smartZoomData'))
	    		return; 
	    		
	    	// Create some defaults, extending them with any options that were provided
			settings = $.extend( {
		      'top' : "0",
		      'left' : "0",
		      'width' : "100%",
		      'height' : "100%",
		      'easing' : "smartZoomEasing",
		      'maxScale' : 3,
		      'dblClickMaxScale' : 1.8,
		      'mouseEnabled' : true,
		      'scrollEnabled' : true,
		      'dblClickEnabled' : true,
		      'mouseMoveEnabled' : true,
		      'moveCursorEnabled' : true,
		      'containerBackground' : "#FFFFFF",
		      'containerClass' : ""
		    }, options);
		    
		    // create the container that will contain the zoom target
		    var zoomContainerId = "smartZoomContainer"+new Date().getTime();
		    var containerDiv = $('<div id="'+zoomContainerId+'" class="'+settings.containerClass+'"></div>"');
		    targetElement.before(containerDiv);
		    targetElement.remove();
		    containerDiv = $('#'+zoomContainerId);
		    containerDiv.css({'overflow':'hidden'});
		    if(settings.containerClass == "")
		   		containerDiv.css({'background-color':settings.containerBackground});
		    containerDiv.append(targetElement);
			
			// smartZoomData is used to saved every plugin vars
		    targetElement.data('smartZoomData', {
               settings : settings, // given settings
               containerDiv : containerDiv, // target container
               originalMap:null,
               originalSize: {width:targetElement.width(), height:targetElement.height()}, // plugin target size at the beginning
               originalPosition: targetElement.offset(), // plugin target position at the beginning 
               transitionObject:getBrowserTransitionObject(), // use to know if the browser is compatible with css transition
               mouseWheelDeltaFactor:0.15, // enable to slow down the zoom via mouse wheel
               currentWheelDelta:0, // the current mouse wheel delta used to calculate scale to apply
               adjustedPosInfos:null, // use to save the adjust information in "adjustToContainer" method (so we can access the normal target size in plugin when we whant)
               moveCurrentPosition:null, // save the current mouse/touch position use in "moveOnMotion" method   
               moveLastPosition:null, // save the last mouse/touch position use in "moveOnMotion" method
               lastScale:1.0
            });

			// adjust the contain and target size into the page
		    adjustToContainer();

			// listening mouse and touch events
			if(settings.mouseEnabled == true){
	        	if(settings.mouseMoveEnabled == true)
		        	targetElement.bind('mousedown.smartZoom', mouseDownHandler);
		        if(settings.scrollEnabled == true){
		        	containerDiv.bind('mousewheel.smartZoom', mouseWheelHandler);
			        containerDiv.bind( 'mousewheel.smartZoom DOMMouseScroll.smartZoom', containerMouseWheelHander);
		        }
		        if(settings.dblClickEnabled == true)
		        	containerDiv.bind('dblclick.smartZoom', mouseDblClickHandler);
	        }
	       	document.ondragstart = function () { return false; }; // allow to remove browser default drag behaviour
	        
		    $(window).bind('resize.smartZoom', windowResizeEventHandler); // call "adjustToContainer" on resize
	    },
	   /**
		  * zoom function used into the plugin and accessible via direct call (ex : $('#zoomImage').smartZoom('zoom', 0.2);)
		  * @param {Number} scaleToAdd : the scale to add to the plugin target current scale (often < 1) 
		  * @param {Point} globalRequestedPosition {'x': global requested position in x
		  * 						                'y': global requested position in y
		  * 	   						           }  if this parameter is missing the zoom will target the object center
		  * @param {Number} duration : zoom effect duration 700ms by default
		  */
	    zoom : function(scaleToAdd, globalRequestedPosition, duration){
	    	
	    	var smartData = targetElement.data('smartZoomData');
	    	var globaRequestedX;
	    	var globaRequestedY;
	    	if(!globalRequestedPosition){ // use target center if globalRequestedPosition is not set
	    		var containerRect = getRect(smartData.containerDiv);
		    	globaRequestedX = containerRect.x + containerRect.width/2;
		    	globaRequestedY = containerRect.y + containerRect.height/2;
		    }else{
		    	globaRequestedX = globalRequestedPosition.x;
		    	globaRequestedY = globalRequestedPosition.y;
		    }
		    
	    	// stop previous effect before make calculation
	    	stopAnim(); 
	    	
	  		var targetRect = getTargetRect(true); // the target rectangle in global position
	 		var originalSize = smartData.originalSize;
	    	var newScale = (targetRect.width / originalSize.width) + scaleToAdd; // calculate new scale to apply

	    	// manage scale min, max
	  		newScale = Math.max(smartData.adjustedPosInfos.scale, newScale); // the scale couldn't be lowest than the initial scale
	  		newScale = Math.min(smartData.settings.maxScale, newScale); // the scale couldn't be highest than the max setted by user

	        var newWidth = originalSize.width * newScale; // new size to apply according to new scale
		  	var newHeight = originalSize.height * newScale;
		  
		  	var positionGlobalXDiff = globaRequestedX - targetRect.x; // the position difference between with the target position
		  	var positionGlobalYDiff = globaRequestedY - targetRect.y;
		  	var sizeRatio =  newWidth / targetRect.width;
		
		  	var newGlobalX = targetRect.x - ((positionGlobalXDiff * sizeRatio) - positionGlobalXDiff); // apply the ratio to positionGlobalDiff and then find the final target point
		  	var newGlobalY = targetRect.y - ((positionGlobalYDiff * sizeRatio) - positionGlobalYDiff);
		    var validPosition = getValidTargetElementPosition(newGlobalX, newGlobalY, newWidth, newHeight); // return a valid position from the calculated position 
		
			if(duration == null) // default effect duration is 700ms
				duration = 700;
				
			animate(targetElement, validPosition.x, validPosition.y, newWidth, newHeight, duration, function(){ // set the new position and size via the animation function
				smartData.currentWheelDelta = 0; // reset the weelDelta when zoom end
			 	updateMouseMoveCursor(); // remove "move" cursor when zoom end
			});
			
			zoomMap( newScale );
			
	    },
	     /**
		  * pan function accessible via direct call (ex : $('#zoomImage').smartZoom('pan', 5, 0);)
		  * @param {Number} xToAdd : a number to add to the object current position in X
		  * @param {Point} yToAdd : a number to add to the object current position in Y
		  * @param {Number} duration : move effect duration 700ms by default
		  */
	    pan : function(xToAdd, yToAdd, duration){
	    	if(xToAdd == null || yToAdd == null) // check params
	    		return;
	    		
	    	if(duration == null) // default pan duration is 700ms
				duration = 700;
	    	var currentPosition = targetElement.offset();
	    	
	    	var targetRect = getTargetRect();
	    	var validPosition = getValidTargetElementPosition(currentPosition.left+xToAdd, currentPosition.top+yToAdd, targetRect.width, targetRect.height); // add the given numbers to the current coordinates and valid the result
	    	
	    	if(validPosition.x != currentPosition.left || validPosition.y != currentPosition.top){
	    		// stop previous effect before make calculation
	    		stopAnim();
				animate(targetElement, validPosition.x, validPosition.y, targetRect.width, targetRect.height, duration);
			}
	    },
	     /**
		  * destroy function accessible via direct call (ex : $('#zoomImage').smartZoom('destroy');)
		  * use this function to clean and remove smartZoom plugin 
		  */
	    destroy : function() {
	    	var smartData = targetElement.data('smartZoomData');
	    	if(!smartData)
	    		return;
	    	stopAnim(); // stop current animation
	    	var containerDiv = smartData.containerDiv;
	    	// remove all listenerns 
	        targetElement.unbind('mousedown.smartZoom');
	        containerDiv.unbind('mousewheel.smartZoom');
	        containerDiv.unbind('dblclick.smartZoom');
	    	containerDiv.unbind( 'mousewheel.smartZoom DOMMouseScroll.smartZoom');
		    $(window).unbind('resize.smartZoom');
			$(document).unbind('mousemove.smartZoom');
			$(document).unbind('mouseup.smartZoom');

			targetElement.css({"cursor":"default"}); // reset default cursor
		    containerDiv.before(targetElement); // move target element to original container 
	   		animate(targetElement, smartData.originalPosition.left, smartData.originalPosition.top,  smartData.originalSize.width, smartData.originalSize.height, 5); // reset initial position
	   		targetElement.removeData('smartZoomData');// clean saved data
		    containerDiv.remove(); // remove zoom container
	    },
	    /**
	     * call this funcion to know if the plugin is used 
	     */
	    isPluginActive : function(){
	    	return targetElement.data('smartZoomData') != undefined;
	    }
    };
    
    if (publicMethods[method] ) { // if the parameter is an existing method, then we call this method
    	return publicMethods[method].apply( this, Array.prototype.slice.call( arguments, 1 ));
    } else if (typeof method === 'object' || ! method ) { // else if it's an object we initilize the plugin
    	if(targetElement[0].tagName.toLowerCase() == "img" && !targetElement[0].complete){ // if the target is an image when wait for image loading before initialization
    		targetElement.bind('load.smartZoom',{arguments:arguments[0]},  imgLoadedHandler);
   	  	}else{
    		publicMethods.init.apply( targetElement, [arguments[0]]);
    	} 
    } else {
    	$.error( 'Method ' +  method + ' does not exist on e-smartzoom jquery plugin' );
    }  
    
    function zoomMap(newScale) {
         // resize image map
        var smartData = targetElement.data('smartZoomData');
        var relScale=newScale/smartData['lastScale'];
        var map = document.getElementById(targetElement.attr("useMap").substring(1));
        if (map != null) {
            for (var i = 0; i < map.areas.length; i++) {
                var area = map.areas[i];
                var newCoordString="";
                if(area.shape=='poly')
                {
                    var coordPairs = area.coords.split(' ');
                    for (var j=0; j<coordPairs.length; j++) {
                        var coord=coordPairs[j].split(',');
                        if(j>0)
                           newCoordString+=' ';
                        newCoordString+=Math.round(coord[0] * relScale)+","+Math.round(coord[1] * relScale);
                    }
                }
                else if(area.shape=='circle')
                {
                    var coords=area.coords.split(',');
                    var newCoordX=Math.round(coords[0]*relScale);
                    var newCoordY=Math.round(coords[1]*relScale);
                    var newRad=Math.round(coords[2]*relScale);
                    newCoordString=newCoordX+","+newCoordY+","+newRad;
                }
                else
                {
                    var coords = area.coords.split(',');
                    for (var j=0; j<coords.length/2; j++) {
                        if(j>0)
                            newCoordString+=',';
                        var newCoordx=Math.round(coords[j*2]*relScale);
                        var newCoordy=Math.round(coords[j*2+1]*relScale);
                        newCoordString+=newCoordx+","+newCoordy;
                    }
                }
                area.coords = newCoordString;
            }
        }
        smartData['lastScale']=newScale;
    }
    
    /**
     * call zoom function on mouse wheel event
 	 * @param {Object} e : mouse event
 	 * @param {Object} delta : wheel direction 1 or -1
     */
    function mouseWheelHandler(e, delta){
    	var smartData = targetElement.data('smartZoomData');
		if(smartData.currentWheelDelta*delta < 0) // if current and delta have != sign we set 0 to go to other direction
			smartData.currentWheelDelta = 0;
		smartData.currentWheelDelta += delta; // increment delta zoom faster when the user use wheel again
    	publicMethods.zoom(smartData.mouseWheelDeltaFactor*smartData.currentWheelDelta, {"x":e.pageX, "y":e.pageY}); // 0.15
    }
	  
	/**
     * prevent page scroll when scrolling on zoomableContainer
 	 * @param {Object} e : mouse event
     */  
    function containerMouseWheelHander(e){
   		e.preventDefault();
    }
    
    /**
     * update mouse cursor (move or default) if the zoom target is draggable 
     */
    function updateMouseMoveCursor(){
		var smartData = targetElement.data('smartZoomData');
    	if(smartData.settings.mouseMoveEnabled != true || smartData.settings.moveCursorEnabled != true)
    		return;
		var targetRect = getTargetRect();
    	var currentScale = (targetRect.width / smartData.originalSize.width);
    	if(parseInt(currentScale*100)>parseInt(smartData.adjustedPosInfos.scale*100)) // multiply by 100 to resolve precision problem
    		targetElement.css({"cursor":"move"});     
    	else	
    		targetElement.css({"cursor":"default"});
    }
    
    /**
     * call "zoomOnDblClick" when user double click
     * @param {Object} e : mouse event
     */
    function mouseDblClickHandler(e){
    	 zoomOnDblClick(e.pageX, e.pageY);
    }
    
    /**
     * save mouse position on mouse down (positions will be used in moveOnMotion function)
     * @param {Object} e : mouse event 
     */
    function mouseDownHandler(e){
    	e.preventDefault(); // prevent default browser drag
		$(document).bind('mousemove.smartZoom', mouseMoveHandler); // add mouse move and mouseup listeners to enable drag
		$(document).bind('mouseup.smartZoom', mouseUpHandler);
		var smartData = targetElement.data('smartZoomData'); // save mouse position on mouse down
		smartData.moveCurrentPosition = new Point(e.pageX, e.pageY);
		smartData.moveLastPosition =  new Point(e.pageX, e.pageY);
    }
    
    /**
     * call "moveOnMotion" when the mouse move after mouseDown
     * @param {Object} e : mouse event
     */
    function mouseMoveHandler(e){
    	moveOnMotion(e.pageX, e.pageY, 0);
	}
    
    /**
     *  stop the drag on mouseup
     * @param {Object} e : mouse event
     */
    function mouseUpHandler(e){
    	
    	var smartData = targetElement.data('smartZoomData');
    	if(smartData.moveLastPosition.distance(smartData.moveCurrentPosition) > 4){ // smooth the drag end when user move the mouse fast
			var interpolateP = smartData.moveLastPosition.interpolate(smartData.moveCurrentPosition, -4);
			moveOnMotion(interpolateP.x, interpolateP.y, 500);
		}
		
		$(document).unbind('mousemove.smartZoom'); // remove listeners when drag is done
		$(document).unbind('mouseup.smartZoom');    	
    }
    
    /**
     *  manage plugin target move after mouse or finger motion
     * @param {Number} xPos : new x position to set
     * @param {Number} yPos : new y position to set 
     * @param {Number} duration : move effect duration
     */
    function moveOnMotion(xPos, yPos, duration){
    	stopAnim();// stop previous effect before make calculation
    	
    	var smartData = targetElement.data('smartZoomData');
    	smartData.moveLastPosition.x = smartData.moveCurrentPosition.x; // save the current position in "moveLastPosition" before moving the plugin target
    	smartData.moveLastPosition.y = smartData.moveCurrentPosition.y; // (moveLastPosition will be use to smooth last motion in "touchEndHandler" and "mouseUpHandler")
    	
    	var currentPosition = targetElement.offset(); // the target current position
    	var targetRect = getTargetRect(); // current target size
    	
    	var newMarginLeft = currentPosition.left + (xPos - smartData.moveCurrentPosition.x); // add current mouseX (orTouchX) position difference to the target position
    	var newMarginTop = currentPosition.top + (yPos - smartData.moveCurrentPosition.y);
    	
    	var validPosition = getValidTargetElementPosition(newMarginLeft, newMarginTop, targetRect.width, targetRect.height); // check if the new position is valid
	   	
	   	animate(targetElement, validPosition.x, validPosition.y, targetRect.width, targetRect.height, duration); // move to the right position
	   	
	 	smartData.moveCurrentPosition.x = xPos; // save the new position
		smartData.moveCurrentPosition.y = yPos;
	}
    
    /**
     * manage zoom when user double click or double tap 
     * @param {Number} pageX : double click (or tap) x position in page
     * @param {Number} pageY : double click (or tap) y position in page
     */
    function zoomOnDblClick(pageX, pageY){
    	var smartData = targetElement.data('smartZoomData');
 		var originalSize = smartData.originalSize; // original target size
 		var targetRect = getTargetRect(); // current target size
    	var currentScale = (targetRect.width / originalSize.width); // the current target scale
    	var originalScale = smartData.adjustedPosInfos.scale; // original scale
    	var dblClickMaxScale = parseFloat(smartData.settings.dblClickMaxScale); // the doucble click or double tap max scale
    	
    	var scaleDiff; // if the current scale is close from "dblClickMaxScale" go to "originalScale" else go to "dblClickMaxScale" 
    	if(currentScale.toFixed(2)>dblClickMaxScale.toFixed(2) || Math.abs(dblClickMaxScale - currentScale)>Math.abs(currentScale-originalScale)){
    		scaleDiff = dblClickMaxScale - currentScale;
    	}else{
    		scaleDiff = originalScale - currentScale;
    	}
    	publicMethods.zoom(scaleDiff, {"x":pageX, "y":pageY});	 
    }
    
    /**
     * stop the animation
     */
    function stopAnim(){
    	
    	var smartData = targetElement.data('smartZoomData');
    	if(smartData.transitionObject){ // if css transformation is surpported
    		if(smartData.transitionObject.cssAnimTimer) // stop the transformation end handler if it exists
    			clearTimeout(smartData.transitionObject.cssAnimTimer); 
			var originalSize = smartData.originalSize; // get the original target size   			
	   		var targetRect = getTargetRect(); // the target current size
	   	
		   	var cssObject = new Object(); // set the current current target size and the target scale to css transformation so it stop previous transformation
		  	cssObject[smartData.transitionObject.transition] = 'all 0s'; // apply transformation now
		  	if(smartData.transitionObject.css3dSupported){
			  	cssObject[smartData.transitionObject.transform] = 'translate3d('+targetRect.x+'px, '+targetRect.y+'px, 0) scale3d('+targetRect.width/originalSize.width+','+targetRect.height/originalSize.height+', 1)';
			}else{
		  		cssObject[smartData.transitionObject.transform] = 'translateX('+targetRect.x+'px) translateY('+targetRect.y+'px) scale('+targetRect.width/originalSize.width+','+targetRect.height/originalSize.height+')';
		    }
		  	targetElement.css(cssObject);	
    			
    	}else{
    		targetElement.stop(); // if we use a jquery transformation, just call stop function
    	}
    	updateMouseMoveCursor(); // update mouse move cursor after animation stop (set the cross cursor or not)
    }
    
    /**
     * manage position validation
     * @param {Number} marginLeft : global x position
     * @param {Number} marginTop : global y position
     * @param {Number} width : element width
     * @param {Number} height : element height
     */
    function getValidTargetElementPosition(xPosition, yPosition, width, height){
    	var smartData = targetElement.data('smartZoomData');
    	 // adjusting if the content is out of the initial content box from "adjustedPosInfos"
	    var newMarginTop = Math.min(smartData.adjustedPosInfos.top, yPosition); // adjust in top 
	    newMarginTop += Math.max(0, (smartData.adjustedPosInfos.top + smartData.adjustedPosInfos.height) - (newMarginTop + height)) // adjust in bottom
	    var newMarginLeft = Math.min(smartData.adjustedPosInfos.left, xPosition); // adjust in left
	    newMarginLeft += Math.max(0, (smartData.adjustedPosInfos.left + smartData.adjustedPosInfos.width) - (newMarginLeft + width)); // adjust in right
	    return new Point(newMarginLeft.toFixed(2), newMarginTop.toFixed(2));
    }
    
    /**
     * when the plugin target is an image we wait for image loading before initilization 
     * @param {Object} e : load event
     */
    function imgLoadedHandler(e){
    	targetElement.unbind('load.smartZoom');
    	publicMethods.init.apply( targetElement, [e.data.arguments]); 
    }
    
	/**
	 * this function fit the plugin target to the zoom container at initialization and when the window is resized
	 */    
    function adjustToContainer(){
    	
 		var smartData = targetElement.data('smartZoomData');
 		var containerDiv = smartData.containerDiv; // the zoom container 
 		var originalSize = smartData.originalSize; // target original size
 		
 		// get the zoomable container position from settings
        if(containerDiv.parent().width()>0 && containerDiv.parent().height())
        {
 		    var parentOffset = containerDiv.parent().offset();
 		    var containerDivNewLeft = getContainerDivPositionFromSettings(smartData.settings.left, parentOffset.left, containerDiv.parent().width());
 		    var containerDivNewTop = getContainerDivPositionFromSettings(smartData.settings.top, parentOffset.top, containerDiv.parent().height());

     		containerDiv.offset({left: containerDivNewLeft, top: containerDivNewTop}); // apply position find
  	    	containerDiv.width(getContainerDivSizeFromSettings(smartData.settings.width, containerDiv.parent().width(), containerDivNewLeft - parentOffset.left)); // apply size found to zoomablecontainer
		    containerDiv.height(getContainerDivSizeFromSettings(smartData.settings.height, containerDiv.parent().height(), containerDivNewTop - parentOffset.top));

            var containerRect = getRect(containerDiv); // get the rectangle from the new containerDiv position and size
	  	    var scaleToFit = Math.min(Math.min(containerRect.width/originalSize.width, containerRect.height/originalSize.height), 1).toFixed(2); // scale to use to include the target into containerRect
	  	    var newWidth = originalSize.width * scaleToFit; // we could now find the new size
	  	    var newHeight = originalSize.height * scaleToFit;

	        // store the position and size information in adjustedPosInfos object
	  	    smartData.adjustedPosInfos = {"left":(containerRect.width - newWidth)/2 + parentOffset.left, "top": (containerRect.height - newHeight)/2 + parentOffset.top, "width": newWidth, "height" : newHeight, "scale":scaleToFit};
	  	    stopAnim();
	  	    // call animate method with 10 ms duration to apply new target position and size
	  	    animate(targetElement,  smartData.adjustedPosInfos.left , smartData.adjustedPosInfos.top, newWidth, newHeight, 0);
	  	    updateMouseMoveCursor();
        }
    }
    
    /**
     * animate the plugin target  
     * @param {Object} target : the element to animate
     * @param {Number} globalLeft : the global x target position 
     * @param {Number} globalTop : the global y target position 
     * @param {Number} width : targeted width
     * @param {Number} width : targeted height
     * @param {Number} duration : effect duration
     * @param {Function} callback : function to call when effect end
     * 
     */
    function animate(target, globalLeft, globalTop, width, height, duration, callback){
    	
    	var smartData = targetElement.data('smartZoomData');
 		var parentOffset = smartData.containerDiv.offset();
   		var left = globalLeft - parentOffset.left; // get the relative position from parent 
   		var top = globalTop - parentOffset.top;
   		
    	if (smartData.transitionObject != null) { // use css transition if supported
    		var originalSize = smartData.originalSize;
		  	var cssObject = new Object();
		  	cssObject[smartData.transitionObject.transform+'-origin'] = '0 0';
		  	cssObject[smartData.transitionObject.transition] = 'all '+duration / 1000+'s ease-out'; // set effect duration
		  	
		  	if(smartData.transitionObject.css3dSupported) // use css 3d translate if supported
		  		cssObject[smartData.transitionObject.transform] = 'translate3d('+left+'px, '+top+'px, 0) scale3d('+width/originalSize.width+','+height/originalSize.height+', 1)';
		  	else
		  		cssObject[smartData.transitionObject.transform] = 'translateX('+left+'px) translateY('+top+'px) scale('+width/originalSize.width+','+height/originalSize.height+')';
		  	target.css(cssObject); // apply css transformation
		  	if(callback != null) // add callback at end if the parameter is set
		  		smartData.transitionObject.cssAnimTimer = setTimeout(callback, duration);
		}else{ // use JQuery animate if css transition is not supported
	    	
	    	target.animate({"margin-left": left, "margin-top": top, "width": width, "height" : height}, {duration:duration, easing:smartData.settings.easing, complete:function() {
			 	if(callback != null)
			 		callback();
			}});
		}
    }
    
	/**
	 * get the plugin target rectangle on screen 
	 * @param {Boolean} globalPosition : if true return global position else return relative position
	 * @return {Object} {'x':'x Position', 'y':'y Position', 'width':' element width', 'height': 'element height'}
	 */	    
    function getTargetRect(globalPosition){
    	var smartData = targetElement.data('smartZoomData');
		var width = targetElement.width(); // get the current object size
		var height = targetElement.height();
		var position = targetElement.offset(); // global position
		var x = parseInt(position.left); // save global position in vars
		var y = parseInt(position.top);
		
		var parentOffset = smartData.containerDiv.offset(); // get zoomable container global position
		
		if(globalPosition != true){ // set local position
			x = parseInt(x) - parentOffset.left;    		
			y = parseInt(y) - parentOffset.top;  
		}
		
    	if (smartData.transitionObject != null) { // if CSS3 transition is enabled
    		var transformMatrix = targetElement.css(smartData.transitionObject.transform);
    		if(transformMatrix && transformMatrix != "" && transformMatrix.search('matrix') != -1){ // get the target css matrix tranform 
    			var scale;
    			var arrValues;
    			if(transformMatrix.search('matrix3d') != -1){ // check the matrix type
    				arrValues = transformMatrix.replace('matrix3d(','').replace(')','').split(',');
    				scale = arrValues[0]; // get target current scale
    			}else{
    				arrValues = transformMatrix.replace('matrix(','').replace(')','').split(',');
    				scale = arrValues[3];// get target current scale
    				x = parseFloat(arrValues[4]);// get target current position
    				y = parseFloat(arrValues[5]);
					if(globalPosition){ // adjust for global
						x = parseFloat(x) + parentOffset.left;    		
						y = parseFloat(y) + parentOffset.top;
			    	}
    			}
    			width = scale * width; // find the actual object size thanks to current scale
    			height = scale * height;
    		}
    	}
    	return {'x' : x,'y' : y, 'width' : width, 'height' : height};
    }
    
    /**
	 * return an object that contains the kind of CSS3 supported transition
	 *  @return {Object} {'transition':'-webkit-transition', 'transform':'-webkit-transform', 'css3dSupported':'true'}
	 */	 
    function getBrowserTransitionObject(){
    	
	   if(jQuery.browser.opera) // performance issues with Opera and css transition JS is better
	   	  return null;
    	
	   var pageBody = document.body || document.documentElement;
	   var bodyStyle = pageBody.style;
	   
	   var transitionTestArr = ['transition', 'WebkitTransition', 'MozTransition', 'MsTransition', 'OTransition']; // all type all transitions to test
	   var transitionArr = ['transition', '-webkit-transition', '-moz-transition', '-ms-transition', '-o-transition'];
	   var transformArr = ['transform', '-webkit-transform', '-moz-transform', '-ms-transform', '-o-transform'];
		
	   var length = transitionTestArr.length;
	   var transformObject;
	   for(var i=0; i<length; i++){ // for all kind of css transition we make a test
	   		if(bodyStyle[transitionTestArr[i]] != null){
   				transformStr = transformArr[i];
	   			var div = $('<div style="position:absolute;">Translate3d Test</div>');
			    $('body').append(div); // try a transformation on a new div each time
			    transformObject = new Object();
			    transformObject[transformArr[i]] = "translate3d(20px,0,0)";
			    div.css(transformObject);
			    css3dSupported = (div.offset().left == 20); // if translate3d(20px,0,0) via transformArr[i] == 20px the transformation is valid for this browser
			    div.empty().remove();
	   			if(css3dSupported){ // return the kind of transformation supported
					return {transition:transitionArr[i], transform:transformArr[i], css3dSupported:css3dSupported};
				}	   			
	   		}
	   }
	   return null; 
    }
    
    /**
	 * get the plugin target rectangle on screen 
	 * @param {Object} settingsValue : a number or a string value given in plugin params
	 * @param {Number} zoomableContainerParentValue : zoomable container parent width or height
	 * @param {Number} divPosDiff : zoomable container parent and zoomable container position difference
	 * @return {Number} return the zoomable container size (in pixel) from setting value (pixel or percent)
	 */	 
    function getContainerDivSizeFromSettings(settingsValue, zoomableContainerParentValue, divPosDiff){
    	if(settingsValue.search && settingsValue.search("%") != -1)
	  		return (zoomableContainerParentValue - divPosDiff)* (parseInt(settingsValue)/100);
	  	else
	  		return parseInt(settingsValue);
    }
    
     /**
	 * get the plugin target rectangle on screen 
	 * @param {Object} settingsValue : a number or a string value given in plugin params
	 * @param {Number} zoomableContainerParentPosValue : zoomable container parent global x  or y
	 * @param {Number} zoomableContainerParentSizeValue : zoomable container parent width or height
	 * @return {Number} return the zoomable container position (in pixel) from setting value (pixel or percent) 
	 */	 
    function getContainerDivPositionFromSettings(settingsValue, zoomableContainerParentPosValue, zoomableContainerParentSizeValue){
    	if(settingsValue.search && settingsValue.search("%") != -1)
	  		return zoomableContainerParentPosValue + zoomableContainerParentSizeValue * (parseInt(settingsValue)/100);
	  	else
	  		return zoomableContainerParentPosValue + parseInt(settingsValue);
    }
    
    /**
     * reinit the component when the user resize the window 
     */
   	function windowResizeEventHandler(){
   		adjustToContainer();
   	}

 	/**
	 * return a retangle from a JQuery object 
	 * @param {Object} jqObject : a JQuery object like $('#myObject')
	 * @return {Object} return {'x':objectX, 'y':objectY, 'width':objectWidth, 'height':objectHeight} 
	 */	 
   	function getRect(jqObject) {
  		var offset = jqObject.offset();
	  	if(!offset)
	  		return null;
		var formX = offset.left;
		var formY = offset.top; 
	    return {'x':formX, 'y':formY, 'width':jqObject.outerWidth(), 'height':jqObject.outerHeight()};
	}
	 
	/**
	 * Point Class
	 * @param {Number} x : point position on X axis
	 * @param {Number} y : point position on Y axis
	 */
	function Point(x, y) {
	    this.x = x;
	    this.y = y;
	     /**
	     * return point informations into a string
	     * @return {String} return (x=5, y=5) 
	     */
	    this.toString = function() {
		    return '(x=' + this.x + ', y=' + this.y + ')';
		};
	    /**
	     * return a new point who is the interpolation of this and the given point 
	     * the new point position is calculate thanks to percentInterpolate (the distance between this and pointToInterpolate in percent)
	     * @return {Point} return {'x':interpolateX, 'y':interpolateY}  
	     */
	    this.interpolate = function(pointToInterpolate, percentInterpolate) {
		    var x = percentInterpolate * this.x + (1 - percentInterpolate) * pointToInterpolate.x;
		    var y = percentInterpolate * this.y + (1 - percentInterpolate) * pointToInterpolate.y;
			return new Point(x, y);
		};
		/**
		 * return the distance between "this" point and the given point  
		 * @return {Number} distance between this and "point"    
		 */
		this.distance = function(point) {
		    return Math.sqrt(Math.pow((point.y - this.y) ,2) + Math.pow((point.x - this.x),2));
		} 
	}
	
	   	
  };
})( jQuery );

/*
 * add smartZoomEasing and smartZoomOutQuad to jQuery easing function 
 */
$.extend($.easing,
{
    smartZoomEasing: function (x, t, b, c, d) {
        return $.easing['smartZoomOutQuad'](x, t, b, c, d);
    },
    smartZoomOutQuad: function (x, t, b, c, d) {
        return -c *(t/=d)*(t-2) + b;
    }
});

/*! Copyright (c) 2011 Brandon Aaron (http://brandonaaron.net)
 * Licensed under the MIT License (LICENSE.txt).
 *
 * Thanks to: http://adomas.org/javascript-mouse-wheel/ for some pointers.
 * Thanks to: Mathias Bank(http://www.mathias-bank.de) for a scope bug fix.
 * Thanks to: Seamus Leahy for adding deltaX and deltaY
 *
 * Version: 3.0.6
 * 
 * Requires: 1.2.2+
 */
(function(e){function r(t){var n=t||window.event,r=[].slice.call(arguments,1),i=0,s=true,o=0,u=0;t=e.event.fix(n);t.type="mousewheel";if(n.wheelDelta){i=n.wheelDelta/120}if(n.detail){i=-n.detail/3}u=i;if(n.axis!==undefined&&n.axis===n.HORIZONTAL_AXIS){u=0;o=-1*i}if(n.wheelDeltaY!==undefined){u=n.wheelDeltaY/120}if(n.wheelDeltaX!==undefined){o=-1*n.wheelDeltaX/120}r.unshift(t,i,o,u);return(e.event.dispatch||e.event.handle).apply(this,r)}var t=["DOMMouseScroll","mousewheel"];if(e.event.fixHooks){for(var n=t.length;n;){e.event.fixHooks[t[--n]]=e.event.mouseHooks}}e.event.special.mousewheel={setup:function(){if(this.addEventListener){for(var e=t.length;e;){this.addEventListener(t[--e],r,false)}}else{this.onmousewheel=r}},teardown:function(){if(this.removeEventListener){for(var e=t.length;e;){this.removeEventListener(t[--e],r,false)}}else{this.onmousewheel=null}}};e.fn.extend({mousewheel:function(e){return e?this.bind("mousewheel",e):this.trigger("mousewheel")},unmousewheel:function(e){return this.unbind("mousewheel",e)}})})(jQuery)
