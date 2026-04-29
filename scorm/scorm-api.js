/* Minimal SCORM 1.2 wrapper — marks the module complete on launch.
   Silently no-ops if launched outside an LMS (e.g. opened locally). */
(function () {
  'use strict';

  function findAPI(win) {
    var depth = 0;
    while (win && win.API == null && win.parent != null && win.parent !== win && depth < 500) {
      depth++;
      win = win.parent;
    }
    return win ? win.API : null;
  }

  function getAPI() {
    var api = findAPI(window);
    if (api == null && window.opener != null && typeof window.opener !== 'undefined') {
      try { api = findAPI(window.opener); } catch (e) { /* cross-origin opener */ }
    }
    return api;
  }

  var api = getAPI();
  var initialized = false;

  function safeCall(fn, label) {
    try { return fn(); } catch (e) {
      // Don't let SCORM errors break the page
      if (window.console && console.warn) console.warn('SCORM ' + label + ' failed:', e);
      return null;
    }
  }

  function init() {
    if (!api) return false;
    var ok = safeCall(function () { return api.LMSInitialize(''); }, 'LMSInitialize');
    initialized = (ok === 'true' || ok === true);
    return initialized;
  }

  function markComplete() {
    if (!api || !initialized) return;
    safeCall(function () { return api.LMSSetValue('cmi.core.lesson_status', 'completed'); }, 'LMSSetValue lesson_status');
    safeCall(function () { return api.LMSSetValue('cmi.core.score.raw', '100'); }, 'LMSSetValue score');
    safeCall(function () { return api.LMSCommit(''); }, 'LMSCommit');
  }

  function finish() {
    if (!api || !initialized) return;
    safeCall(function () { return api.LMSCommit(''); }, 'LMSCommit (finish)');
    safeCall(function () { return api.LMSFinish(''); }, 'LMSFinish');
    initialized = false;
  }

  // Initialize as soon as possible
  if (init()) {
    markComplete();
  }

  // Make sure we tell the LMS goodbye when the learner closes the tab
  window.addEventListener('beforeunload', finish);
  window.addEventListener('unload', finish);
  // Some LMS players use pagehide instead of unload
  window.addEventListener('pagehide', finish);
})();
