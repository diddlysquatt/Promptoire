/* state.js — shared application state + derived helpers */
(function () {
  "use strict";
  const PR = (window.PROMPTOIRE = window.PROMPTOIRE || {});

  const state = {
    categories: [],
    settings: {},
    stats: {},
    version: "",
    platform: "windows",
    hotkeyAvailable: true,

    view: "launcher",       // launcher | editor | bulk | settings
    query: "",
    filter: "all",          // all | text | image | favorites
    results: [],
    selected: 0,

    pinned: false,
    suppressBlur: false,    // set while native dialogs are open
  };
  PR.state = state;

  // Walk every prompt with its owning category.
  PR.eachPrompt = function (cb) {
    (function walk(cats) {
      for (const c of cats) {
        for (const p of c.prompts || []) cb(p, c);
        if (c.subcategories) walk(c.subcategories);
      }
    })(state.categories);
  };

  PR.findCategory = function (id) {
    let found = null;
    (function walk(cats) {
      for (const c of cats) {
        if (c.id === id) { found = c; return; }
        if (c.subcategories) walk(c.subcategories);
      }
    })(state.categories);
    return found;
  };

  PR.findPrompt = function (id) {
    let res = null;
    PR.eachPrompt((p, c) => { if (p.id === id) res = { p, c }; });
    return res;
  };

  PR.allTags = function () {
    const set = new Set();
    PR.eachPrompt((p) => (p.tags || []).forEach((t) => set.add(t)));
    return [...set].sort();
  };
})();
