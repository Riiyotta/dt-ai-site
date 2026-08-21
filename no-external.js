/*
 * no-external.js -- keeps this clone fully self-contained.
 *
 * The captured bundles still contain third-party integrations (Google gtag,
 * reCAPTCHA, form posts to api.column.com). Their URLs have been stripped from
 * the bundles; this file is the backstop that guarantees nothing reaches the
 * network, and stubs the globals those integrations expect so the page does not
 * throw or spin.
 */
(function () {
  var ORIGIN = window.location.origin;

  function isExternal(url) {
    if (!url) return false;
    var s = String(url);
    if (s.indexOf('data:') === 0 || s.indexOf('blob:') === 0 || s === 'about:blank') return false;
    if (!/^https?:\/\//i.test(s)) return false;
    return s.indexOf(ORIGIN) !== 0;
  }

  // -- analytics no-ops ------------------------------------------------------
  window.dataLayer = window.dataLayer || [];
  window.gtag = window.gtag || function () {};
  window.ga = window.ga || function () {};

  // -- reCAPTCHA stub: resolves immediately with a dummy token ---------------
  window.grecaptcha = window.grecaptcha || {
    ready: function (cb) { if (typeof cb === 'function') setTimeout(cb, 0); },
    execute: function () { return Promise.resolve('local-stub-token'); },
    render: function () { return 0; },
    reset: function () {},
  };

  // -- block cross-origin fetch ---------------------------------------------
  var nativeFetch = window.fetch;
  if (nativeFetch) {
    window.fetch = function (input, init) {
      var url = typeof input === 'string' ? input : (input && input.url);
      if (isExternal(url)) {
        console.warn('[no-external] blocked fetch:', url);
        return Promise.resolve(new Response('{}', {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        }));
      }
      return nativeFetch.apply(this, arguments);
    };
  }

  // -- block cross-origin XHR -----------------------------------------------
  var nativeOpen = XMLHttpRequest.prototype.open;
  XMLHttpRequest.prototype.open = function (method, url) {
    if (isExternal(url)) {
      console.warn('[no-external] blocked XHR:', url);
      arguments[1] = 'about:blank';
    }
    return nativeOpen.apply(this, arguments);
  };

  // -- block cross-origin sendBeacon ----------------------------------------
  if (navigator.sendBeacon) {
    var nativeBeacon = navigator.sendBeacon.bind(navigator);
    navigator.sendBeacon = function (url) {
      if (isExternal(url)) { console.warn('[no-external] blocked beacon:', url); return true; }
      return nativeBeacon.apply(null, arguments);
    };
  }

  // -- neutralise injected <script>/<img>/<link>/<iframe> --------------------
  // <a> is deliberately left alone: its hrefs were rewritten at build time.
  var LOADERS = { SCRIPT: 'src', IMG: 'src', IFRAME: 'src', LINK: 'href', SOURCE: 'src', TRACK: 'src' };

  function scrub(node) {
    if (!node || node.nodeType !== 1) return;
    var attr = LOADERS[node.tagName];
    if (attr && isExternal(node.getAttribute(attr))) {
      console.warn('[no-external] blocked <' + node.tagName.toLowerCase() + '>:', node.getAttribute(attr));
      node.setAttribute(attr, 'about:blank');
    }
  }

  var nativeSetAttribute = Element.prototype.setAttribute;
  Element.prototype.setAttribute = function (name, value) {
    if (LOADERS[this.tagName] === name && isExternal(value)) {
      console.warn('[no-external] blocked <' + this.tagName.toLowerCase() + '>:', value);
      arguments[1] = 'about:blank';
    }
    return nativeSetAttribute.apply(this, arguments);
  };

  new MutationObserver(function (records) {
    for (var i = 0; i < records.length; i++) {
      var added = records[i].addedNodes;
      for (var j = 0; j < added.length; j++) {
        scrub(added[j]);
        if (added[j].querySelectorAll) {
          var kids = added[j].querySelectorAll('script,img,iframe,link,source,track');
          for (var k = 0; k < kids.length; k++) scrub(kids[k]);
        }
      }
    }
  }).observe(document.documentElement, { childList: true, subtree: true });
})();
