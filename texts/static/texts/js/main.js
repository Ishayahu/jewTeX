
(function e(t,n,r){function s(o,u){if(!n[o]){if(!t[o]){var a=typeof require=="function"&&require;if(!u&&a)return a(o,!0);if(i)return i(o,!0);throw new Error("Cannot find module '"+o+"'")}var f=n[o]={exports:{}};t[o][0].call(f.exports,function(e){var n=t[o][1][e];return s(n?n:e)},f,f.exports,e,t,n,r)}return n[o].exports}var i=typeof require=="function"&&require;for(var o=0;o<r.length;o++)s(r[o]);return s})({1:[function(require,module,exports){
  var storage = {
    asides: []
  }
  
  window.onload = function () {

    var asides = Array.from(document.getElementsByTagName('aside'));
    asides.forEach(function(aside) {
      storage.asides.push({
        element: aside,
        cards: []
      })
    })

    function initAjaxLink (scope=null) {

      var scope = scope || document;
      var links = Array.from(scope.getElementsByClassName('js-ajax-link'));
    
      links.forEach(function (target) {
        
        target.addEventListener('click', function (e) {
    
          // initialize modal
          var elem = document.createElement('div');
          elem.className = 'modal';
          elem.innerHTML = `
            <div class="modal-header">
              <span class="modal-dragPanel"></span>
              <span class="modal-close">X</span>
            </div>
            <div class="modal-body">
              <div class="layer">
                <div class="modal-content">
                  <em>Loading...</em>
                </div>
                <div class="modal-expand-x js-resize-x"></div>
              </div>
              <div class="layer">
                <div class="modal-expand-y js-resize-y"></div>
                <div class="_empty"></div>
              </div>
            </div>`;
    
          // get tagret link coords
          var coords = target.getBoundingClientRect(),
              top = coords.top,
              bottom = coords.bottom,
              left = coords.left,
              right = coords.right;
    
          // calculate coords for modal position
          var elem_top = e.pageY - 220,
              elem_left = left - 200 + (right - left)/2,
              elem_right = elem_left + 300;
    
          // apply position values
          if (e.clientY < 220) {
            elem.style.top = (e.pageY + 20) + 'px';
          } else {
            elem.style.top = elem_top + 'px';
          }
          if (elem_left < 0) {
            elem.style.left = '10px';
          } else if (elem_right > window.outerWidth) {
            elem.style.right = '10px';
          } else {
            elem.style.left = elem_left + 'px';
          }
    
          // insert modal into DOM
          var parent = document.querySelector('.cardStorage');
          parent.appendChild(elem)
    
          var body = elem.getElementsByClassName('modal-content')[0];
          var dragPanel = elem.getElementsByClassName('modal-dragPanel')[0];
          var resizeX = elem.querySelector('.js-resize-x');
          var resizeY = elem.querySelector('.js-resize-y');
    
          // get data info
          ajaxUrl = target.dataset['ajaxUrl'];
          fetch(ajaxUrl).then(function (res) {
            return res.json();
          }).then(function (json) { 
            body.innerHTML = json['content'];
            dragPanel.innerHTML = json['title'];
            elem.classList.add(json['cardColor']);
            
            initAjaxLink(scope=elem);
          })
    
          var close = elem.getElementsByClassName('modal-close')[0];
          close.addEventListener('click', function () {
            var parent = elem.parentElement;
            parent.removeChild(elem);
          })

          elem.onmousedown = function (e) { dragElem(e) }
          elem.ontouchstart = function (e) { dragElem(e.changedTouches[0]) };
  
          function dragElem(e) {
          
            elem.onmouseup = endDragging;
            elem.ontouchend = endDragging;
    
            var dragPanel = elem.getElementsByClassName('modal-dragPanel')[0];
            var dragPanelCoords = dragPanel.getBoundingClientRect();

            var offsetY = e.pageY - elem.offsetTop;
            var offsetX = e.pageX - elem.offsetLeft;

            if (e.clientX > dragPanelCoords.left && 
                e.clientX < dragPanelCoords.right && 
                e.clientY > dragPanelCoords.top && 
                e.clientY < dragPanelCoords.bottom) {
    
              elem.style.position = 'absolute';
              moveAt(e);
              document.body.appendChild(elem);
            
              elem.style.zIndex = 1000; 
            
              function moveAt(e) {

                elem.style.left = (e.pageX - offsetX) + 'px';
                elem.style.top = (e.pageY - offsetY) + 'px';
    
                asides.forEach(function (aside) {
    
                  var coords = aside.getBoundingClientRect();
    
                  if (e.clientX < coords.right && e.clientX > coords.left && e.clientY > coords.top && e.clientY < coords.bottom) {
                    if (!aside.classList.contains('active')) {
                      initAside(aside);
                    }
                  } else {
                    uninitAside(aside)
                  }
    
                })
              }
            
              document.onmousemove = function(e) {
                moveAt(e);
              }
            
              document.ontouchmove = function(e) {
                moveAt(e.changedTouches[0]);
              }

            } else if (e.target === resizeX) {
              window.onmousemove = function (e) {
                e.cancelBubble = true;
                if (e.stopPropagation) e.stopPropagation();
                window.getSelection().collapseToStart();
                elem.style.width = (e.pageX - elem.getBoundingClientRect().left) + 'px';
                body.style.width = (e.pageX - elem.getBoundingClientRect().left - 5) + 'px';
                resizeY.style.width = (e.pageX - elem.getBoundingClientRect().left - 5) + 'px';
              }
              window.onmouseup = function (e) {
                window.onmousemove = null;
              }
            } else if (e.target === resizeY) {
              window.onmousemove = function (e) {
                e.cancelBubble = true;
                if (e.stopPropagation) e.stopPropagation();
                window.getSelection().collapseToStart();
                elem.style.height = (e.pageY - elem.offsetTop) + 'px';
                body.style.height = (e.pageY - elem.offsetTop - 70) + 'px';
              }
              window.onmouseup = function (e) {
                window.onmousemove = null;
              }
            }

          }
        
          function endDragging (e) {
  
            document.onmousemove = null;
            document.ontouchmove = null;
            elem.onmouseup = null;
            elem.ontouchend = null;
  
            asides.forEach(function (aside) {
  
              if (aside.classList.contains('active')) {
  
                // do not let cards go over the left, top and right borders
                if (elem.offsetTop < aside.offsetTop) elem.style.top = aside.offsetTop + 'px'
                if (elem.offsetLeft < aside.offsetLeft) elem.style.left = aside.offsetLeft + 'px'
                if ((elem.offsetLeft + elem.offsetWidth) > (aside.offsetLeft + aside.offsetWidth)) elem.style.left = aside.offsetLeft + aside.offsetWidth - elem.offsetWidth + 'px'
  
                elem.setAttribute('data-top-position', elem.offsetTop)
                elem.setAttribute('data-left-position', elem.offsetLeft)
  
                var contentElem = aside.getElementsByClassName('content')[0];
                contentElem.appendChild(elem);
  
                let storageAside = storage.asides.find(item => item.element === aside);
  
                if (storageAside) {
                  if (!storageAside.cards.some(item => item === elem)) storageAside.cards.push(elem)
                }
  
                // get the lowest elem in aside to calculate aside bottom border
                var lowestElem = storageAside.cards[0];
                if (storageAside) {
                  storageAside.cards.forEach(item => {
                    if (Number(item.offsetTop)+item.offsetHeight > Number(lowestElem.offsetTop)+lowestElem.offsetHeight) {
                      lowestElem = item
                    }
                  })
                  if (!lowestElem) lowestElem = elem;
                }
  
                aside.style.height = (Number(lowestElem.offsetTop)+lowestElem.offsetHeight-aside.offsetTop+5) + 'px';
  
              }
  
              uninitAside(aside);
              aside.onmouseover = null;
              aside.onmouseout = null;
    
      })

    }

    function initAside (aside) {
      aside.classList.add('active')
      aside.style.minWidth = '300px'
      aside.style.minHeight = '200px'
    }

    function uninitAside (aside) {
      aside.classList.remove('active');
    }

  })
      
})

}

    initAjaxLink()
    
  }
  },{}]},{},[1]);

  