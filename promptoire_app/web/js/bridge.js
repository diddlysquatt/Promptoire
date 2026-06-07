/* bridge.js — talk to the Python API, with a mock fallback for browser preview */
(function () {
  "use strict";
  const PR = (window.PROMPTOIRE = window.PROMPTOIRE || {});

  const hasPy = () => !!(window.pywebview && window.pywebview.api);

  // Resolve when the pywebview API is ready, or immediately in mock mode.
  let readyResolve;
  const readyPromise = new Promise((res) => (readyResolve = res));
  let resolved = false;
  function markReady() { if (!resolved) { resolved = true; readyResolve(); } }

  window.addEventListener("pywebviewready", markReady);
  // If pywebview already injected, or we're in a plain browser, resolve soon.
  setTimeout(() => { if (hasPy() || !window.pywebview) markReady(); }, 60);
  // Hard fallback so the UI never hangs.
  setTimeout(markReady, 1200);

  async function call(method, ...args) {
    if (hasPy() && typeof window.pywebview.api[method] === "function") {
      try { return await window.pywebview.api[method](...args); }
      catch (e) { return { ok: false, error: String(e) }; }
    }
    return MOCK[method] ? MOCK[method](...args) : { ok: false, error: "no-bridge:" + method };
  }

  PR.bridge = { ready: () => readyPromise, call, isMock: () => !hasPy() };

  /* ----------------------------- mock backend ---------------------------- */
  const mkId = (s) => "prm_" + Math.abs(hash(s)).toString(16).slice(0, 12);
  function hash(s){let h=0;for(let i=0;i<s.length;i++){h=(h<<5)-h+s.charCodeAt(i)|0;}return h;}

  const mockCats = [
    { id: "cat_code", name: "Coding", color: "#3b82f6", collapsed:false, subcategories:[], prompts: [
      { id: mkId("handoff"), type:"text", title:"New-chat handoff brief", prompt:"Create a NEW CHAT HANDOFF that summarizes everything needed to continue immediately: objective, current state, constraints, decisions, key files/paths, commands to run, known bugs, and next steps in priority order.", tags:["workflow","context"], note:"", favorite:true, uses:12 },
      { id: mkId("secrev"), type:"text", title:"Pragmatic security review", prompt:"Perform a pragmatic security review. Identify attack surfaces and misconfigs: injection, authz/authn flaws, secrets leakage, insecure defaults, dependency risks, PII handling. Provide prioritized, minimal-scope fixes.", tags:["security"], note:"", favorite:false, uses:5 },
      { id: mkId("refactor"), type:"text", title:"Refactor for clarity", prompt:"Refactor {code} for readability without changing behavior. Keep the public API. Explain each change in one line.", tags:["refactor"], note:"", favorite:false, uses:2 },
    ]},
    { id: "cat_art", name: "AI Art", color: "#f472b6", collapsed:false, subcategories:[], prompts: [
      { id: mkId("cinematic"), type:"image", title:"Cinematic portrait", prompt:"cinematic portrait of {subject}, dramatic rim lighting, 85mm, shallow depth of field, film grain, moody color grade", negative:"blurry, lowres, extra fingers, watermark", model:"Midjourney v6", params:"--ar 4:5 --stylize 250", tags:["portrait","cinematic"], note:"", favorite:true, uses:9 },
      { id: mkId("iso"), type:"image", title:"Isometric game asset", prompt:"isometric {object}, clean vector style, soft studio lighting, pastel palette, game asset, centered", negative:"text, busy background", model:"SDXL", params:"Steps: 30, CFG: 6", tags:["isometric","asset"], note:"", favorite:false, uses:3 },
    ]},
    { id: "cat_law", name: "Law", color: "#34d399", collapsed:false, subcategories:[], prompts: [
      { id: mkId("clause"), type:"text", title:"Contract clause explainer", prompt:"Explain the following clause in plain English, flag risks for the {party}, and suggest safer alternative language.", tags:["contracts"], note:"", favorite:false, uses:1 },
    ]},
  ];
  function walk(cats){ let out=[]; for(const c of cats){ for(const p of c.prompts){ out.push({p,c}); } if(c.subcategories) out=out.concat(walk(c.subcategories)); } return out; }

  const MOCK = {
    get_state: () => ({ ok:true, categories: mockCats, stats: stats(), version:"2.0.0-preview",
      hotkey_available:true, platform:"windows",
      settings: { theme:"matrix", accent:"", hotkey:"ctrl+alt+space",
        behavior:{copy_then_hide:true,hide_on_blur:true,open_at_cursor:true,paste_after_copy:false,launch_at_startup:false,show_tray:true},
        window:{width:460,height:560,opacity:1.0}, bulk_improve:{meta_prompt:"You are a senior prompt engineer..."} } }),
    search: (q="", type="all", fav=false) => {
      q=(q||"").toLowerCase(); let res=[];
      for(const {p,c} of walk(mockCats)){
        if(type==="text"&&p.type!=="text")continue; if(type==="image"&&p.type!=="image")continue;
        if(fav&&!p.favorite)continue;
        if(q&&!(p.title.toLowerCase().includes(q)||p.prompt.toLowerCase().includes(q)||(p.tags||[]).join(" ").toLowerCase().includes(q)))continue;
        res.push(Object.assign({}, p, {category_id:c.id, category_name:c.name, category_color:c.color, path:[c.name]}));
      }
      res.sort((a,b)=>(b.favorite?1:0)-(a.favorite?1:0));
      return { ok:true, results:res, count:res.length };
    },
    copy_prompt: (id, resolved) => ({ ok:true, spring:true, title:"Prompt" }),
    copy_text: () => ({ ok:true }),
    toggle_favorite: (id) => { for(const {p} of walk(mockCats)){ if(p.id===id){ p.favorite=!p.favorite; return {ok:true,favorite:p.favorite}; } } return {ok:false}; },
    get_export: () => ({ ok:true, json: JSON.stringify({version:3,categories:mockCats},null,2) }),
    copy_export: () => ({ ok:true, chars: 1234 }),
    merge_preview: () => ({ ok:true, preview:{added:[{id:"new_1",title:"Example new prompt",type:"text",category_name:"Coding"}], updated:[{id:"prm_x",title:"Refactor for clarity",type:"text",category_name:"Coding",changes:{prompt:{}}, before_title:"Refactor for clarity"}], unchanged_count:4, new_categories:[], incoming_total:6} }),
    apply_merge: () => ({ ok:true, result:{updated:1,added:1,new_categories:0}, stats:stats(), categories:mockCats }),
    update_settings: (p) => ({ ok:true, settings:{} }),
    set_hotkey: () => ({ ok:true, applied:true, available:true }),
    add_prompt: () => ({ ok:true, prompt:{} }), update_prompt: () => ({ ok:true }),
    delete_prompt: () => ({ ok:true, removed:{} }), add_category: () => ({ ok:true, category:{} }),
    hide_window: () => ({ ok:true }), open_external: () => ({ ok:true }), quit_app: () => ({ ok:true }),
    backup_now: () => ({ ok:true }), notify_blur: () => ({ ok:true }),
  };
  function stats(){ const all=walk(mockCats); return { total:all.length, text:all.filter(x=>x.p.type==="text").length, image:all.filter(x=>x.p.type==="image").length, favorites:all.filter(x=>x.p.favorite).length, categories:mockCats.length }; }
})();
