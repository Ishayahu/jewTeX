(function e(t,n,r){function s(o,u){if(!n[o]){if(!t[o]){var a=typeof require=="function"&&require;if(!u&&a)return a(o,!0);if(i)return i(o,!0);throw new Error("Cannot find module '"+o+"'")}var f=n[o]={exports:{}};t[o][0].call(f.exports,function(e){var n=t[o][1][e];return s(n?n:e)},f,f.exports,e,t,n,r)}return n[o].exports}var i=typeof require=="function"&&require;for(var o=0;o<r.length;o++)s(r[o]);return s})({1:[function(require,module,exports){
  window.onload = function () {
    
    var links = Array.from(document.getElementsByClassName('js-ajax-link'));
    var asides = Array.from(document.getElementsByTagName('aside'));
  
    links.forEach(function (target) {
      
      target.addEventListener('click', function (e) {
  
        // initialize modal
        var elem = document.createElement('div');
        elem.className = 'modal';
        elem.innerHTML = `
          <div class="modal-header">
            <span class="modal-dragPanel">drag this</span>
            <span class="modal-close">X</span>
          </div>
          <div class="modal-body">
            <div class="modal-content">
              <em>Loading...</em>
            </div>
          </div>`;
  
        // get tagret link coords
        var coords = target.getBoundingClientRect(),
            top = coords.top,
            bottom = coords.bottom,
            left = coords.left,
            right = coords.right;
  
        // calculate coords for modal position
        var elem_top = e.pageY - 155,
            elem_left = left - 150 + (right - left)/2;
  
        // apply position values
        if (e.clientY < 160) {
          elem.style.top = (e.pageY + 10) + 'px';
        } else {
          elem.style.top = elem_top + 'px';
        }
        elem.style.left = elem_left + 'px';
  
        // insert modal into DOM
        var parent = target.parentElement;
        parent.insertBefore(elem, target);
  
        var body = elem.getElementsByClassName('modal-content')[0];
  
        // get data info
        ajaxUrl = target.dataset['ajaxUrl'];
        fetch(ajaxUrl).then(function (res) {
          return res.text();
        }).then(function (html) { body.innerHTML = html })
  
        var close = elem.getElementsByClassName('modal-close')[0];
        close.addEventListener('click', function () {
          var parent = elem.parentElement;
          parent.removeChild(elem);
        })
  
        elem.onmousedown = function(e) {
  
          var dragPanel = elem.getElementsByClassName('modal-dragPanel')[0];
          var dragPanelCoords = dragPanel.getBoundingClientRect();
  
          if (e.clientX > dragPanelCoords.left && 
              e.clientX < dragPanelCoords.right && 
              e.clientY > dragPanelCoords.top && 
              e.clientY < dragPanelCoords.bottom) {
  
            elem.style.position = 'absolute';
            moveAt(e);
            document.body.appendChild(elem);
          
            elem.style.zIndex = 1000; 
          
            function moveAt(e) {
  
              elem.style.left = e.pageX - elem.offsetWidth / 2 + 'px';
              elem.style.top = e.pageY - elem.offsetHeight / 2 + 'px';
  
              var asides = Array.from(document.getElementsByTagName('aside'));
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
          
            elem.onmouseup = function() {
              document.onmousemove = null;
              elem.onmouseup = null;
  
              asides.forEach(function (target) {
  
                if (target.classList.contains('active')) {
                  elem.removeAttribute('style')
                  elem.style.position = 'relative';
                  elem.style.zIndex = '10';
                  var contentElem = target.getElementsByClassName('content')[0];
                  contentElem.appendChild(elem);
                }
  
                uninitAside(target);
                target.onmouseover = null;
                target.onmouseout = null;
            
              })
  
            }
  
            function initAside (aside) {
              aside.classList.add('active')
              aside.style.minWidth = '300px'
              aside.style.minHeight = '150px'
            }
  
            function uninitAside (aside) {
              aside.classList.remove('active');
              aside.removeAttribute('style');
            }
  
          }
  
        }
  
      })
      
    })
    
  }
  },{}]},{},[1]);

  