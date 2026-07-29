/* bridge.js — talk to the Python API, with a mock fallback for browser preview */
(function () {
  "use strict";
  const PR = (window.PROMPTOIRE = window.PROMPTOIRE || {});

  // Mode resolution. pywebview injects `window.pywebview` *after* our classic
  // scripts evaluate (file:// + WebView2), so "no pywebview yet" must NOT be
  // read as "browser preview" — that race used to render mock data inside the
  // real app. We start "unknown", give the injection a grace window, and even
  // if we guessed mock, flip to real and re-sync the moment it appears.
  let mode = window.pywebview ? "real" : "unknown"; // real | mock | unknown
  const isReal = () => mode === "real" || !!window.pywebview;
  const apiReady = (m) => !!(window.pywebview && window.pywebview.api &&
                             typeof window.pywebview.api[m] === "function");

  let readyResolve;
  const readyPromise = new Promise((res) => (readyResolve = res));
  let resolved = false;
  function markReady() { if (!resolved) { resolved = true; readyResolve(); } }

  function goReal() {
    const wasMock = mode === "mock";
    mode = "real";
    markReady();
    if (wasMock && PR.app && PR.app.onBridgeReal) PR.app.onBridgeReal();
  }
  window.addEventListener("pywebviewready", goReal);
  if (mode === "real") markReady();
  // Grace window: only commit to mock if pywebview still hasn't appeared.
  setTimeout(() => {
    if (window.pywebview) goReal();
    else if (mode === "unknown") { mode = "mock"; markReady(); }
  }, 400);
  // Belt & braces: some WebView backends are late with the ready event.
  const probe = setInterval(() => {
    if (window.pywebview) { clearInterval(probe); goReal(); }
  }, 250);
  setTimeout(() => clearInterval(probe), 10000);

  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

  async function call(method, ...args) {
    await readyPromise;
    if (isReal()) {
      // Real app: NEVER fall back to mock. Wait for the bridge to expose the
      // method (handles the brief window between page load and api injection).
      for (let i = 0; i < 40 && !apiReady(method); i++) await sleep(50);
      if (apiReady(method)) {
        try { return await window.pywebview.api[method](...args); }
        catch (e) { return { ok: false, error: String(e) }; }
      }
      return { ok: false, error: "bridge-not-ready: " + method };
    }
    // Browser/preview only: mock data so the UI can be developed without Python.
    return MOCK[method] ? MOCK[method](...args) : { ok: false, error: "no-bridge: " + method };
  }

  PR.bridge = { ready: () => readyPromise, call, isMock: () => !isReal() };

  /* ----------------------------- mock backend ---------------------------- */
  const mkId = (s) => "prm_" + Math.abs(hash(s)).toString(16).slice(0, 12);
  function hash(s){let h=0;for(let i=0;i<s.length;i++){h=(h<<5)-h+s.charCodeAt(i)|0;}return h;}

  const mockCats = [
    { id: "cat_code", name: "Coding", icon: "💻", color: "#3b82f6", collapsed:false, subcategories:[], prompts: [
      { id: mkId("handoff"), type:"text", title:"New-chat handoff brief", prompt:"Create a NEW CHAT HANDOFF that summarizes everything needed to continue immediately: objective, current state, constraints, decisions, key files/paths, commands to run, known bugs, and next steps in priority order.", tags:["workflow","context"], note:"", favorite:true, uses:12 },
      { id: mkId("secrev"), type:"text", title:"Pragmatic security review", prompt:"Perform a pragmatic security review. Identify attack surfaces and misconfigs: injection, authz/authn flaws, secrets leakage, insecure defaults, dependency risks, PII handling. Provide prioritized, minimal-scope fixes.", tags:["security"], note:"", favorite:false, uses:5 },
      { id: mkId("refactor"), type:"text", title:"Refactor for clarity", prompt:"Refactor {code} for readability without changing behavior. Keep the public API. Explain each change in one line.", tags:["refactor"], note:"", favorite:false, uses:2 },
    ]},
    { id: "cat_art", name: "AI Art", icon: "🎨", color: "#f472b6", collapsed:false, prompts: [
      { id: mkId("cinematic"), type:"image", title:"Cinematic portrait", prompt:"cinematic portrait of {subject}, dramatic rim lighting, 85mm, shallow depth of field, film grain, moody color grade", negative:"blurry, lowres, extra fingers, watermark", model:"Midjourney v6", params:"--ar 4:5 --stylize 250", tags:["portrait","cinematic"], note:"", favorite:true, uses:9 },
    ], subcategories: [
      { id: "cat_iso", name: "Game Assets", icon: "🕹️", color: "", collapsed:false, subcategories:[], prompts: [
        { id: mkId("iso"), type:"image", title:"Isometric game asset", prompt:"isometric {object}, clean vector style, soft studio lighting, pastel palette, game asset, centered", negative:"text, busy background", model:"SDXL", params:"Steps: 30, CFG: 6", tags:["isometric","asset"], note:"", favorite:false, uses:3 },
        { id: mkId("sprite"), type:"image", title:"Pixel sprite sheet", prompt:"16-bit pixel art sprite sheet of {character}, 8 walk frames, side view, transparent background", negative:"blur, antialiasing", model:"SDXL", params:"Steps: 28, CFG: 7", tags:["pixel","sprite"], note:"", favorite:false, uses:1 },
      ]},
      { id: "cat_mecha", name: "Mecha", icon: "🤖", color: "#fb923c", collapsed:false, subcategories:[], prompts: [
        { id: mkId("mecha"), type:"image", title:"Chromatic rift mecha", prompt:"insanely detailed alien mecha emerging from a kaleidoscopic dimensional rift, chromatic liquid metal armor", negative:"lowres", model:"Midjourney v7", params:"--ar 16:9", tags:["mecha","maximalist"], note:"", favorite:false, uses:0 },
      ]},
    ]},
    { id: "cat_law", name: "Law", icon: "⚖️", color: "#34d399", collapsed:false, subcategories:[], prompts: [
      { id: mkId("clause"), type:"text", title:"Contract clause explainer", prompt:"Explain the following clause in plain English, flag risks for the {party}, and suggest safer alternative language.", tags:["contracts"], note:"", favorite:false, uses:1 },
    ]},
  ];
  const mockSettings = {
    theme:"matrix", accent:"", density:"compact", hotkey:"ctrl+alt+space",
    behavior:{copy_then_hide:true,hide_on_blur:true,open_at_cursor:true,paste_after_copy:false,launch_at_startup:false,show_tray:true},
    window:{width:460,height:560,opacity:1.0}, bulk_improve:{
      outline_prompt:"Improve this Promptoire outline. Return only the outline.",
      meta_prompt:"You are a senior prompt engineer..."
    },
    ai:{provider:"openai",api_key:"",model:"gpt-5.6",base_url:""},
    links:{coffee:"https://buymeacoffee.com/promptoire",repo:"https://github.com/diddlysquatt/Promptoire"}
  };
  function walk(cats, path, color){ let out=[]; path=path||[]; for(const c of cats){ const eff=c.color||color||""; const here=path.concat([c.name]); for(const p of c.prompts){ out.push({p,c,path:here,color:eff}); } if(c.subcategories) out=out.concat(walk(c.subcategories, here, eff)); } return out; }

  const MOCK = {
    get_state: () => ({ ok:true, categories: mockCats, stats: stats(), version:"2.3.0-preview",
      hotkey_available:true, platform:"windows",
      settings: mockSettings }),
    search: (q="", type="all", fav=false) => {
      q=(q||"").toLowerCase(); let res=[];
      const toks=q.split(/\s+/).filter(Boolean);
      const terms=toks.filter(t=>!t.startsWith("#"));
      const tagTerms=toks.filter(t=>t.startsWith("#")&&t.length>1).map(t=>t.slice(1));
      for(const {p,c,path,color} of walk(mockCats)){
        if(type==="text"&&p.type!=="text")continue; if(type==="image"&&p.type!=="image")continue;
        if(fav&&!p.favorite)continue;
        const tags=(p.tags||[]).map(t=>t.toLowerCase());
        if(tagTerms.length&&!tagTerms.every(tt=>tags.some(t=>t.startsWith(tt))))continue;
        const hay=(p.title+" "+p.prompt+" "+tags.join(" ")+" "+path.join(" ")).toLowerCase();
        if(terms.length&&!terms.every(t=>hay.includes(t)))continue;
        res.push(Object.assign({}, p, {category_id:c.id, category_name:c.name, category_color:color, category_icon:c.icon||"", path:path}));
      }
      res.sort((a,b)=>(b.favorite?1:0)-(a.favorite?1:0));
      return { ok:true, results:res, count:res.length };
    },
    copy_prompt: (id, resolved, keepOpen) => ({ ok:true, spring:!keepOpen, title:"Prompt" }),
    copy_text: () => ({ ok:true }),
    get_clipboard_text: () => ({ ok:true, text:"Path: AI Art > Characters > Portraits\nTitle: Cinematic portrait\nType: image\nPrompt: A dramatic 85mm portrait of {subject}, rim lighting, shallow depth of field --ar 4:5 --stylize 250\nTags: portrait, cinematic" }),
    toggle_favorite: (id) => { for(const {p} of walk(mockCats)){ if(p.id===id){ p.favorite=!p.favorite; return {ok:true,favorite:p.favorite}; } } return {ok:false}; },
    get_export: () => ({ ok:true, json: JSON.stringify({version:3,categories:mockCats},null,2) }),
    copy_export: () => ({ ok:true, chars: 1234 }),
    copy_outline_export: () => ({ ok:true, chars: 987 }),
    bulk_prompt_defaults: () => ({ ok:true,
      outline_prompt:"Improve this Promptoire outline. Return only the outline.",
      meta_prompt:"You are a senior prompt engineer. Return only valid JSON." }),
    save_outline_file: () => ({ ok:true, path:"prompts-outline.txt" }),
    merge_preview: () => ({ ok:true, preview:{added:[{id:"new_1",title:"Cinematic portrait",type:"image",category_name:"AI Art / Characters / Portraits"}], updated:[{id:"prm_x",title:"Refactor for clarity",type:"text",category_name:"Coding",changes:{prompt:{}}, before_title:"Refactor for clarity"}], unchanged_count:4, duplicates:[], ambiguous:[], new_categories:["AI Art / Characters", "AI Art / Characters / Portraits"], incoming_total:6} }),
    apply_merge: () => ({ ok:true, result:{updated:1,added:1,new_categories:0,duplicates_skipped:0,ambiguous_skipped:0}, stats:stats(), categories:mockCats }),
    ai_improve: () => ({ ok:false, error:"(preview mode — connect the real app and set an API key to use this)" }),
    update_settings: (p) => ({ ok:true, settings: mergeSettings(mockSettings, p || {}) }),
    set_hotkey: (combo) => {
      mockSettings.hotkey = combo;
      return { ok:true, applied:true, available:true };
    },
    add_prompt: () => ({ ok:true, prompt:{} }), update_prompt: () => ({ ok:true }),
    delete_prompt: (id) => { for(const c of allCats()){ const i=(c.prompts||[]).findIndex(p=>p.id===id); if(i>=0) return {ok:true, removed:c.prompts.splice(i,1)[0]}; } return {ok:false}; },
    restore_prompt: (catId, p, idx) => { const c=findCat(catId); if(c) c.prompts.splice(idx<0?c.prompts.length:idx,0,p); return {ok:true}; },
    add_category: (name, parentId) => { const cat={id:"cat_"+Math.random().toString(36).slice(2,8), name, icon:"", color:"", collapsed:false, prompts:[], subcategories:[]}; const par=parentId&&findCat(parentId); if(par) par.subcategories.push(cat); else mockCats.push(cat); return {ok:true, category:cat}; },
    update_category: (id, fields) => { const c=findCat(id); if(!c) return {ok:false}; Object.assign(c, fields||{}); return {ok:true, category:c}; },
    delete_category: (id) => { const rm=(list)=>{ const i=list.findIndex(c=>c.id===id); if(i>=0){list.splice(i,1);return true;} return list.some(c=>rm(c.subcategories||[])); }; return {ok:rm(mockCats)}; },
    reorder_category: (id, to) => { const find=(list)=>{ const i=list.findIndex(c=>c.id===id); if(i>=0){ const[c]=list.splice(i,1); list.splice(Math.max(0,Math.min(to,list.length)),0,c); return true;} return list.some(x=>find(x.subcategories||[])); }; return {ok:find(mockCats)}; },
    move_prompt: (pid, catId, index) => { const dest=findCat(catId); if(!dest) return {ok:false}; let moved=null; for(const c of allCats()){ const i=(c.prompts||[]).findIndex(p=>p.id===pid); if(i>=0){ moved=c.prompts.splice(i,1)[0]; break; } } if(!moved) return {ok:false}; const prompts=dest.prompts||(dest.prompts=[]); if(Number.isInteger(index)&&index>=0&&index<=prompts.length) prompts.splice(index,0,moved); else prompts.push(moved); return {ok:true}; },
    reorder_prompt: (catId, from, to) => { const c=findCat(catId); if(!c||!c.prompts[from]) return {ok:false}; const[p]=c.prompts.splice(from,1); c.prompts.splice(Math.max(0,Math.min(to,c.prompts.length)),0,p); return {ok:true}; },
    hide_window: () => ({ ok:true }), begin_window_resize: () => ({ ok:true }),
    open_external: () => ({ ok:true }), open_data_folder: () => ({ ok:true, path:"." }), quit_app: () => ({ ok:true }),
    backup_now: () => ({ ok:true }), notify_blur: () => ({ ok:true }),
  };
  function allCats(){ const out=[]; (function w(l){ for(const c of l){ out.push(c); w(c.subcategories||[]); } })(mockCats); return out; }
  function findCat(id){ return allCats().find(c=>c.id===id) || null; }
  function stats(){ const all=walk(mockCats); return { total:all.length, text:all.filter(x=>x.p.type==="text").length, image:all.filter(x=>x.p.type==="image").length, favorites:all.filter(x=>x.p.favorite).length, categories:mockCats.length }; }
  function mergeSettings(target, patch){
    for(const key in patch){
      const value=patch[key];
      if(value && typeof value==="object" && !Array.isArray(value)){
        if(!target[key] || typeof target[key]!=="object" || Array.isArray(target[key])) target[key]={};
        mergeSettings(target[key], value);
      } else target[key]=value;
    }
    return target;
  }
})();
