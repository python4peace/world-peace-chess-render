/* ==================================================================
   Reuben Soul World Peace Chess  -  ROYAL THEME  v2  (Grand Edition)

   WHITE ARMY : ruby crimson + polished gold, emerald jewels
   BLACK ARMY : royal amethyst + polished gold, turquoise jewels
   BOARD      : ivory marble + emerald velvet, ornate gold frame
   EXTRAS     : shimmering title, floating gold dust, pieces drop in,
                gold sparkle burst on every move, selected piece lifts
                and glows, capture rings, confetti on checkmate / win.

   Put this file in:  static/royal-theme.js
   and add before </body> in templates/index.html:
       <script src="/static/royal-theme.js?v=2" defer></script>

   All 12 pieces are drawn in code (vector, razor sharp at any size),
   so there are no image files to upload and the file is small.
   Works with Unicode glyph boards (outline = white, solid = black)
   and with data-piece="wK" / "bN" style boards.
   ================================================================== */
(function () {
  'use strict';
  if (window.__royalThemeLoaded) return;
  window.__royalThemeLoaded = true;

  var reduce = !!(window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches);

  /* ================================================================
     1.  STYLES
     ================================================================ */
  var CSS = `
:root{--piece-w:124%}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{margin:0;padding:16px;min-height:100vh;color:#f4ecd8;font-family:Georgia,'Palatino Linotype','Times New Roman',serif;
  background:
   radial-gradient(ellipse 80% 45% at 50% -8%,rgba(242,193,78,.24),transparent 70%),
   radial-gradient(circle at 10% 90%,rgba(125,50,170,.30),transparent 45%),
   radial-gradient(circle at 92% 72%,rgba(200,30,55,.24),transparent 45%),
   linear-gradient(180deg,#14213d 0%,#0a1224 55%,#070b17 100%);
  background-attachment:fixed}
main{max-width:780px;margin:auto;position:relative;z-index:1}

/* ---- Title ---- */
h1{font-size:clamp(22px,5.6vw,38px);margin:4px 0 12px;text-align:center;letter-spacing:2px;font-weight:700;
  background:linear-gradient(100deg,#8a6410 0%,#fff1a8 18%,#f2c14e 34%,#fffbe0 50%,#f2c14e 66%,#fff1a8 82%,#8a6410 100%);
  background-size:250% 100%;-webkit-background-clip:text;background-clip:text;color:transparent;-webkit-text-fill-color:transparent;
  filter:drop-shadow(0 2px 2px rgba(0,0,0,.75)) drop-shadow(0 0 14px rgba(242,193,78,.35));
  animation:royalShine 6s linear infinite}
h1:before,h1:after{content:'\\265B';display:inline-block;margin:0 .45em;font-size:.82em;-webkit-text-fill-color:transparent}
@keyframes royalShine{to{background-position:-250% 0}}

/* ---- Controls ---- */
button,select{padding:11px 14px;border-radius:10px;border:1px solid #c9a54a;
  background:linear-gradient(#38557f,#1a2b47);color:#fbeab5;font-family:inherit;font-size:15px;
  box-shadow:inset 0 1px 0 rgba(255,255,255,.18),0 2px 6px rgba(0,0,0,.4)}
button{cursor:pointer;transition:transform .12s,box-shadow .12s,filter .12s}
button:hover:not(:disabled){transform:translateY(-1px);box-shadow:inset 0 1px 0 rgba(255,255,255,.25),0 5px 14px rgba(242,193,78,.4);filter:brightness(1.1)}
button:disabled{cursor:default;opacity:.5}
.bar{display:flex;gap:8px;flex-wrap:wrap;margin:12px 0}
.clock{font:bold 38px monospace;background:linear-gradient(#2e4668,#1a2a44);border:1px solid #9a7a28;border-radius:14px;
  padding:12px 16px;margin:12px 0;display:flex;align-items:center;justify-content:space-between;color:#ffe8a3;
  text-shadow:0 0 12px rgba(242,193,78,.55);box-shadow:inset 0 1px 0 rgba(255,255,255,.15),0 6px 18px rgba(0,0,0,.45)}
.clock small{font:17px Georgia,serif;color:#e8d6a0;text-shadow:none}
.running{outline:3px solid #f2c14e;box-shadow:0 0 26px rgba(242,193,78,.6)}
.low{color:#ff7b7b;text-shadow:0 0 12px rgba(255,80,80,.7)}

/* ---- The board: ornate gold frame, ivory marble + emerald velvet ---- */
#board{display:grid;grid-template-columns:repeat(8,1fr);border:14px solid transparent;border-radius:10px;
  margin-top:clamp(36px,10vw,84px);
  background:linear-gradient(#0b1b17,#0b1b17) padding-box,
             linear-gradient(135deg,#fff6c0 0%,#d9a520 16%,#7a5a0c 30%,#f8d35e 48%,#a87a10 66%,#fff1a8 82%,#8a6410 100%) border-box;
  box-shadow:0 20px 44px rgba(0,0,0,.72),0 0 0 2px #4a3506,0 0 0 4px rgba(255,226,130,.35),0 0 54px rgba(242,193,78,.22)}
.sq{position:relative;aspect-ratio:1;border:0;border-radius:0;padding:0;display:flex;align-items:center;justify-content:center;
  overflow:visible;font-size:clamp(24px,7.8vw,60px);color:#090909;font-family:'DejaVu Sans','Segoe UI Symbol',serif;
  box-shadow:none;transition:box-shadow .15s}
.sq:hover:not(:disabled){transform:none;filter:none;box-shadow:inset 0 0 0 3px rgba(255,214,102,.75),inset 0 0 18px rgba(255,214,102,.45)}
.light{background:var(--orn-l),
  linear-gradient(115deg,transparent 38%,rgba(150,110,60,.11) 39%,transparent 41%,transparent 62%,rgba(150,110,60,.08) 63%,transparent 65%),
  radial-gradient(circle at 30% 25%,#fffaf0,#efe0bb 70%,#dcc592);
  box-shadow:inset 0 0 14px rgba(120,80,20,.18)}
.dark{background:var(--orn-d),
  linear-gradient(65deg,transparent 30%,rgba(255,255,255,.07) 31%,transparent 33%),
  radial-gradient(circle at 30% 25%,#1f8a72,#0f5846 75%,#0a3d31);
  box-shadow:inset 0 0 16px rgba(0,0,0,.35)}
.selected{box-shadow:inset 0 0 0 4px #ffd75e,inset 0 0 30px rgba(255,241,168,.9)!important}
.sq.selected{z-index:6}
#board .sq.last,#board .sq.lastmove,#board .sq.last-move,#board .sq.from,#board .sq.to{box-shadow:inset 0 0 0 3px rgba(255,214,102,.6),inset 0 0 20px rgba(255,214,102,.45)}
#board .sq.check,#board .sq.in-check,#board .sq.king-check{box-shadow:inset 0 0 0 4px #ff4d4d,inset 0 0 28px rgba(255,60,60,.95)!important}

/* legal moves: glowing gold gem; captures: crimson ring */
.legal:after{content:'';position:absolute;width:26%;height:26%;border-radius:50%;
  background:radial-gradient(circle at 35% 30%,#fffbd0,#f2c14e 55%,#b8860b);
  box-shadow:0 0 0 1.5px rgba(80,50,0,.55),0 0 12px rgba(255,214,102,.95);z-index:3;animation:royalDot 1.6s ease-in-out infinite}
.legal.has-royal:after{width:86%;height:86%;background:transparent;animation:none;
  box-shadow:inset 0 0 0 4px rgba(255,90,90,.95),0 0 18px rgba(255,70,70,.85)}
@keyframes royalDot{50%{transform:scale(1.18)}}
.coord{position:absolute;left:3px;bottom:2px;font:10px Arial;color:#3b2a10;opacity:.75;z-index:1}
.dark .coord{color:#f3dba0}

/* ---- 3D royal pieces ---- */
.sq img.pc{position:absolute;left:50%;bottom:-7%;width:var(--piece-w);max-width:none;height:auto;transform:translateX(-50%);
  z-index:2;pointer-events:none;user-select:none;-webkit-user-drag:none;transform-origin:50% 92%;
  transition:transform .18s ease,filter .18s ease;animation:royalDrop .34s cubic-bezier(.2,.9,.3,1.15)}
img.pc.pw{filter:drop-shadow(0 6px 4px rgba(0,0,0,.55)) drop-shadow(0 0 1.5px rgba(255,236,170,.8))}
img.pc.pb{filter:drop-shadow(0 6px 4px rgba(0,0,0,.6)) drop-shadow(0 0 2px rgba(210,190,255,.9))}
img.pc.still{animation:none}
.sq:hover img.pc{transform:translateX(-50%) translateY(-4px) scale(1.05)}
.sq:hover img.pc.pw{filter:drop-shadow(0 11px 8px rgba(0,0,0,.6)) drop-shadow(0 0 12px rgba(255,214,102,.75))}
.sq:hover img.pc.pb{filter:drop-shadow(0 11px 8px rgba(0,0,0,.65)) drop-shadow(0 0 12px rgba(200,170,255,.8))}
.sq.selected img.pc{animation:royalLift 1.3s ease-in-out infinite;
  filter:drop-shadow(0 14px 8px rgba(0,0,0,.55)) drop-shadow(0 0 16px rgba(255,214,102,1))}
.sq.has-royal{font-size:0;color:transparent}
@keyframes royalDrop{from{opacity:0;transform:translateX(-50%) translateY(-24px) scale(1.1)}60%{opacity:1}to{opacity:1;transform:translateX(-50%)}}
@keyframes royalLift{0%,100%{transform:translateX(-50%) translateY(-6px) scale(1.08)}50%{transform:translateX(-50%) translateY(-11px) scale(1.1)}}

/* ---- Panels ---- */
#status,#notice{padding:11px 14px;background:linear-gradient(#2c4268,#182744);border:1px solid #8a6d22;border-radius:10px;
  margin:8px 0;color:#fbefd0;box-shadow:inset 0 1px 0 rgba(255,255,255,.12),0 3px 10px rgba(0,0,0,.35)}
#notice:empty{display:none}#notice{color:#ffd484}
#moves{max-height:140px;overflow:auto;line-height:1.7}
input{width:100%;padding:9px;margin:4px 0;background:#1d3048;color:#e8f1fb;border:1px solid #8a6d22;border-radius:6px}
p,label{font-size:14px;color:#c9d4e3}
a{color:#ffd978}
#links{margin:12px 0}
details{margin:16px 0}
[hidden]{display:none!important}
body.clean #creator,body.clean #links,body.clean #actions,body.clean #notes,body.clean footer{display:none!important}
button:focus-visible,a:focus-visible{outline:3px solid #f2c14e}

/* ---- Floating gold dust + sparkle / confetti layers ---- */
#royal-dust{position:fixed;inset:0;pointer-events:none;z-index:0;overflow:hidden}
#royal-dust i{position:absolute;bottom:-14px;width:var(--s);height:var(--s);border-radius:50%;opacity:0;
  background:radial-gradient(circle,#fff6c0,#f2c14e 55%,transparent 72%);animation:royalFloat var(--d) linear infinite;animation-delay:var(--l)}
@keyframes royalFloat{0%{transform:translate3d(0,0,0) scale(.6);opacity:0}10%{opacity:.85}90%{opacity:.45}100%{transform:translate3d(var(--x),-112vh,0) scale(1.2);opacity:0}}
#royal-fx{position:fixed;inset:0;pointer-events:none;z-index:9999;overflow:hidden}
.rspark{position:fixed;width:8px;height:8px;margin:-4px 0 0 -4px;border-radius:50%;
  background:radial-gradient(circle,#fff,#ffd75e 55%,transparent 72%);animation:rspark .7s ease-out forwards}
@keyframes rspark{to{transform:translate(var(--dx),var(--dy)) scale(.2);opacity:0}}
.rconf{position:fixed;top:-16px;width:9px;height:14px;border-radius:2px;animation:rconf var(--t) ease-in forwards}
@keyframes rconf{to{transform:translate3d(var(--dx),108vh,0) rotate(var(--r));opacity:.9}}
@media (prefers-reduced-motion:reduce){h1,.legal:after,.sq img.pc,.sq.selected img.pc{animation:none!important}}
`;

  /* ornamental filigree drawn faintly inside every square */
  function orn(col, op) {
    var svg = "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><g fill='none' stroke='" + col +
      "' stroke-opacity='" + op + "' stroke-width='1.2'><rect x='7' y='7' width='86' height='86' rx='6'/>" +
      "<path d='M50 14 L86 50 L50 86 L14 50 Z'/><circle cx='50' cy='50' r='9'/>" +
      "<path d='M7 20 Q20 20 20 7 M93 20 Q80 20 80 7 M7 80 Q20 80 20 93 M93 80 Q80 80 80 93'/></g></svg>";
    return 'url("data:image/svg+xml,' + encodeURIComponent(svg) + '") center/94% no-repeat';
  }
  CSS += ':root{--orn-l:' + orn('#b8860b', 0.32) + ';--orn-d:' + orn('#f5c542', 0.26) + '}';

  var st = document.createElement('style');
  st.id = 'royal-theme-css';
  st.textContent = CSS;
  document.head.appendChild(st);

  /* ================================================================
     2.  THE ROYAL PIECES  (drawn in code as vector art)
     ================================================================ */
  var PAL = {
    w: { b1: '#ff9a9a', b2: '#d91f33', b3: '#5e0618', edge: '#33020b',
         j1: '#c4ffe4', j2: '#17c27a', j3: '#055c3c' },
    b: { b1: '#d6c4ff', b2: '#7a45dc', b3: '#240a5c', edge: '#10032b',
         j1: '#c8fff9', j2: '#1fd2c8', j3: '#06625f' }
  };

  function f(p) { return p[0].toFixed(1) + ',' + p[1].toFixed(1); }

  /* "lathe": turn a list of [y, halfWidth] into a smooth symmetrical silhouette */
  function lathe(pts) {
    var R = pts.map(function (p) { return [50 + p[1], p[0]]; });
    var L = pts.map(function (p) { return [50 - p[1], p[0]]; }).reverse();
    function sm(a) {
      var d = '';
      for (var i = 0; i < a.length - 1; i++) {
        var p0 = a[i - 1] || a[i], p1 = a[i], p2 = a[i + 1], p3 = a[i + 2] || p2;
        d += 'C' + f([p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6]) + ' ' +
                   f([p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6]) + ' ' + f(p2);
      }
      return d;
    }
    return 'M' + f(R[0]) + sm(R) + 'L' + f(L[0]) + sm(L) + 'Z';
  }

  function defs(p) {
    return '<defs>' +
      '<linearGradient id="bd" x1="0" x2="1" y1="0" y2="0"><stop offset="0" stop-color="' + p.b3 + '"/><stop offset=".2" stop-color="' + p.b2 +
        '"/><stop offset=".38" stop-color="' + p.b1 + '"/><stop offset=".62" stop-color="' + p.b2 + '"/><stop offset="1" stop-color="' + p.b3 + '"/></linearGradient>' +
      '<radialGradient id="bs" cx=".35" cy=".3" r=".8"><stop offset="0" stop-color="' + p.b1 + '"/><stop offset=".45" stop-color="' + p.b2 +
        '"/><stop offset="1" stop-color="' + p.b3 + '"/></radialGradient>' +
      '<linearGradient id="kd" x1=".05" y1="0" x2=".95" y2="1"><stop offset="0" stop-color="' + p.b1 + '"/><stop offset=".4" stop-color="' + p.b2 +
        '"/><stop offset="1" stop-color="' + p.b3 + '"/></linearGradient>' +
      '<linearGradient id="gd" x1="0" x2="1" y1="0" y2="0"><stop offset="0" stop-color="#6b4607"/><stop offset=".2" stop-color="#e0a920"/>' +
        '<stop offset=".38" stop-color="#fff6bf"/><stop offset=".6" stop-color="#f8cd4a"/><stop offset=".85" stop-color="#b17a12"/><stop offset="1" stop-color="#6b4607"/></linearGradient>' +
      '<radialGradient id="jw" cx=".35" cy=".3" r=".75"><stop offset="0" stop-color="' + p.j1 + '"/><stop offset=".5" stop-color="' + p.j2 +
        '"/><stop offset="1" stop-color="' + p.j3 + '"/></radialGradient>' +
      '<radialGradient id="pl" cx=".35" cy=".3" r=".8"><stop offset="0" stop-color="#fff"/><stop offset=".55" stop-color="#f5e9d4"/><stop offset="1" stop-color="#a99578"/></radialGradient>' +
      '<filter id="bl" x="-20%" y="-60%" width="140%" height="220%"><feGaussianBlur stdDeviation="2.2"/></filter>' +
      '</defs>';
  }

  function svgFor(t, c) {
    var p = PAL[c], E = p.edge;

    function body(d) { return '<path d="' + d + '" fill="url(#bd)" stroke="' + E + '" stroke-width=".8" stroke-linejoin="round"/>'; }
    function gRect(x, y, w, h, r) {
      return '<rect x="' + x + '" y="' + y + '" width="' + w + '" height="' + h + '" rx="' + r + '" fill="url(#gd)" stroke="#6b4607" stroke-width=".7"/>';
    }
    function ring(cy, rx) {
      return '<ellipse cx="50" cy="' + cy + '" rx="' + rx + '" ry="3.3" fill="url(#gd)" stroke="#6b4607" stroke-width=".7"/>' +
             '<ellipse cx="50" cy="' + (cy - 1) + '" rx="' + (rx - 3) + '" ry="1" fill="#fff" opacity=".4"/>';
    }
    function jewel(x, y, r) {
      return '<circle cx="' + x + '" cy="' + y + '" r="' + (r + 1.6) + '" fill="url(#gd)" stroke="#6b4607" stroke-width=".6"/>' +
             '<circle cx="' + x + '" cy="' + y + '" r="' + r + '" fill="url(#jw)" stroke="' + p.j3 + '" stroke-width=".5"/>' +
             '<circle cx="' + (x - r * .32) + '" cy="' + (y - r * .36) + '" r="' + (r * .3) + '" fill="#fff" opacity=".9"/>';
    }
    function pearl(x, y, r) {
      return '<circle cx="' + x + '" cy="' + y + '" r="' + r + '" fill="url(#pl)" stroke="#8a7655" stroke-width=".5"/>';
    }
    function gloss(x1, y1, x2, y2, w) {
      return '<path d="M' + x1 + ',' + y1 + ' L' + x2 + ',' + y2 + '" stroke="#fff" stroke-opacity=".3" stroke-width="' + (w || 2) + '" stroke-linecap="round"/>';
    }

    var s = '';

    if (t === 'P') {
      s = body(lathe([[100, 5.5], [106, 6.5], [114, 9.5], [120, 16], [124, 22]])) +
          '<circle cx="50" cy="88" r="13.5" fill="url(#bs)" stroke="' + E + '" stroke-width=".8"/>' +
          '<ellipse cx="44.5" cy="82" rx="4.2" ry="2.6" fill="#fff" opacity=".45" transform="rotate(-35 44.5 82)"/>' +
          jewel(50, 90, 3.2) + ring(101.5, 12.5) + gloss(44, 108, 42, 118, 2);
    }

    if (t === 'R') {
      s = body(lathe([[70, 17], [74, 16], [84, 14.5], [100, 14.5], [112, 18.5], [124, 24]])) +
          body('M27,70 L27,47 H38 V54 H44.5 V47 H55.5 V54 H62 V47 H73 V70 Z') +
          gRect(25, 66, 50, 7, 3) + gRect(27, 47, 11, 3.2, 1) + gRect(44.5, 47, 11, 3.2, 1) + gRect(62, 47, 11, 3.2, 1) +
          jewel(50, 89, 5) + ring(108, 17) + gloss(40, 78, 39, 104, 2) + gloss(31, 52, 31, 63, 2);
    }

    if (t === 'B') {
      s = body(lathe([[84, 7], [92, 7.5], [104, 10.5], [114, 16], [124, 23]])) +
          body(lathe([[34, 1.5], [38, 6], [46, 11.5], [56, 14.5], [66, 13.5], [75, 10], [82, 8]])) +
          '<path d="M43,48 L58,66" stroke="' + E + '" stroke-width="3.4" stroke-linecap="round"/>' +
          '<path d="M44.6,46.4 L59.6,64.4" stroke="#f8cd4a" stroke-width="1.5" stroke-linecap="round"/>' +
          jewel(42, 62, 3.2) + '<circle cx="50" cy="29.5" r="5" fill="url(#gd)" stroke="#6b4607" stroke-width=".7"/>' +
          '<circle cx="48.4" cy="27.8" r="1.5" fill="#fff" opacity=".85"/>' +
          ring(82, 13) + ring(106, 14) + gloss(42, 44, 38, 62, 2) + gloss(44, 90, 43, 102, 1.6);
    }

    if (t === 'N') {
      var KN = 'M72,122 C73,104 76,88 70,72 C67,60 64,52 62,46 L60,31 L52,41 C46,40 40,46 35,53 C28,62 21,72 19,80 ' +
               'C18,86 22,89 27,88 C32,87 36,82 40,80 C42,86 40,92 40,98 C38,108 30,112 28,122 Z';
      var kn = '<path d="' + KN + '" fill="url(#kd)" stroke="' + E + '" stroke-width=".9" stroke-linejoin="round"/>' +
        '<path d="M60,40 L59,35 L55,41 Z" fill="' + E + '" opacity=".55"/>' +
        '<path d="M60,33 C66,47 70,58 72,70 C76,85 74,103 73,121 L63,121 C66,104 66,88 61.5,74 C59,64 57,54 53,44 Z" fill="url(#gd)" stroke="#6b4607" stroke-width=".8"/>' +
        '<path d="M61,40 L67,43 M64,52 L70,55 M67,62 L73,64 M70,72 L76,73 M72,84 L77,84 M72,96 L76,96" stroke="#6b4607" stroke-width="1" opacity=".6" fill="none"/>' +
        '<path d="M43,50 C41,62 41,72 40,80" stroke="url(#gd)" stroke-width="2.2" fill="none" stroke-linecap="round"/>' +
        '<path d="M26.5,71 L33,85" stroke="url(#gd)" stroke-width="3.4" fill="none" stroke-linecap="round"/>' +
        '<path d="M21,86 C27,86 33,83 38,80" stroke="' + E + '" stroke-width="1.1" fill="none" stroke-linecap="round"/>' +
        '<ellipse cx="23.5" cy="80" rx="1.6" ry="2.4" fill="' + E + '" transform="rotate(-20 23.5 80)"/>' +
        '<ellipse cx="43" cy="50" rx="3" ry="6" fill="#fff" opacity=".28" transform="rotate(35 43 50)"/>' +
        jewel(41, 58, 3) + jewel(50, 105, 4);
      s = (c === 'b' ? '<g transform="translate(100 0) scale(-1 1)">' + kn + '</g>' : kn) + ring(115, 22);
    }

    if (t === 'Q') {
      s = body(lathe([[66, 17], [72, 14], [82, 11], [98, 10], [110, 14], [124, 23]])) +
          '<path d="M30,68 L23,40 L29.75,54 L36.5,32 L43.25,52 L50,26 L56.75,52 L63.5,32 L70.25,54 L77,40 L70,68 Z" fill="url(#gd)" stroke="#6b4607" stroke-width=".8" stroke-linejoin="round"/>' +
          '<path d="M29.75,54 L32,64 M43.25,52 L44,64 M56.75,52 L56,64 M70.25,54 L68,64" stroke="#6b4607" stroke-opacity=".4" stroke-width=".9"/>' +
          gRect(28, 64, 44, 9, 3.5) + jewel(38, 68.5, 2.3) + jewel(50, 68.5, 2.7) + jewel(62, 68.5, 2.3) +
          pearl(23, 38.5, 3.3) + pearl(36.5, 30.5, 3.3) + pearl(63.5, 30.5, 3.3) + pearl(77, 38.5, 3.3) + jewel(50, 24, 3.5) +
          ring(80, 15) + ring(104, 13.5) + jewel(50, 92, 4.2) + gloss(40, 84, 39, 100, 2);
    }

    if (t === 'K') {
      s = body(lathe([[70, 18], [76, 15], [84, 12], [98, 10], [110, 14], [124, 23]])) +
          body('M29,60 C27,40 39,31 50,31 C61,31 73,40 71,60 Z') +
          '<path d="M30,59 C30,44 40,36 50,33 C60,36 70,44 70,59" stroke="url(#gd)" stroke-width="3.2" fill="none" stroke-linecap="round"/>' +
          '<path d="M40,59 C40,46 46,38 50,33 C54,38 60,46 60,59" stroke="url(#gd)" stroke-width="2" fill="none" stroke-linecap="round"/>' +
          gRect(27, 56, 46, 10, 4) + jewel(36, 61, 2.6) + jewel(50, 61, 3.2) + jewel(64, 61, 2.6) +
          '<circle cx="50" cy="29.5" r="4.6" fill="url(#gd)" stroke="#6b4607" stroke-width=".7"/>' +
          gRect(47.2, 4, 5.6, 24, 2.2) + gRect(39.5, 11.5, 21, 5.6, 2.2) + jewel(50, 14.3, 2) +
          ring(82, 14.5) + ring(106, 13.5) + jewel(50, 94, 4.4) + gloss(40, 86, 39, 102, 2) + gloss(35, 40, 38, 52, 2);
    }

    var base = '<ellipse cx="50" cy="143" rx="40" ry="5" fill="#000" opacity=".5" filter="url(#bl)"/>';
    var plinth = gRect(13, 130, 74, 11, 5.5) +
      '<rect x="16" y="132.2" width="68" height="2" rx="1" fill="#fff" opacity=".38"/>' +
      '<rect x="18" y="124" width="64" height="8" rx="4" fill="url(#bd)" stroke="' + E + '" stroke-width=".6"/>' +
      gRect(22, 119.5, 56, 6, 3);

    return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 150" width="200" height="300">' +
           defs(p) + base + s + plinth + '</svg>';
  }

  var URI = {};
  function uri(key) {
    if (!URI[key]) URI[key] = 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(svgFor(key.charAt(1), key.charAt(0)));
    return URI[key];
  }
  function pieceHTML(type, color) {
    var key = color + type;
    return '<img class="pc p' + color + '" data-key="' + key + '" alt="" draggable="false" src="' + uri(key) + '">';
  }

  /* ================================================================
     3.  FIND WHICH PIECE IS ON A SQUARE
     ================================================================ */
  var OUTLINE = { '\u2654': 'K', '\u2655': 'Q', '\u2656': 'R', '\u2657': 'B', '\u2658': 'N', '\u2659': 'P' };
  var SOLID   = { '\u265A': 'K', '\u265B': 'Q', '\u265C': 'R', '\u265D': 'B', '\u265E': 'N', '\u265F': 'P' };

  function pieceOf(el) {
    var d = el.dataset || {};
    var raw = d.piece || d.p || '';
    if (/^[wb][KQRBNPkqrbnp]$/.test(raw)) return { c: raw[0], t: raw[1].toUpperCase() };

    var txt = (el.textContent || '').replace(/[\s\uFE0E\uFE0F]/g, '');
    var ch = txt.charAt(0);
    if (OUTLINE[ch]) return { c: 'w', t: OUTLINE[ch] };
    if (SOLID[ch]) {
      var cls = el.className || '';
      var isW = /\bwhite\b|\bw-piece\b|piece-w/i.test(cls) || d.color === 'w' || d.color === 'white' || d.side === 'w' || d.side === 'white';
      return { c: isW ? 'w' : 'b', t: SOLID[ch] };
    }
    return null;
  }

  /* ================================================================
     4.  EFFECTS  (sparkle burst, confetti, floating gold dust)
     ================================================================ */
  var fx;
  function fxLayer() {
    if (!fx || !fx.isConnected) { fx = document.createElement('div'); fx.id = 'royal-fx'; document.body.appendChild(fx); }
    return fx;
  }
  function gone(n, ms) { setTimeout(function () { if (n.parentNode) n.parentNode.removeChild(n); }, ms); }

  function burst(sq) {
    if (reduce) return;
    var r = sq.getBoundingClientRect(), L = fxLayer();
    var cx = r.left + r.width / 2, cy = r.top + r.height * 0.6;
    for (var i = 0; i < 12; i++) {
      var s = document.createElement('i');
      var a = Math.PI * 2 * i / 12 + Math.random() * 0.5, d = r.width * (0.5 + Math.random() * 0.7);
      s.className = 'rspark';
      s.style.left = cx + 'px'; s.style.top = cy + 'px';
      s.style.setProperty('--dx', (Math.cos(a) * d).toFixed(1) + 'px');
      s.style.setProperty('--dy', (Math.sin(a) * d).toFixed(1) + 'px');
      L.appendChild(s); gone(s, 760);
    }
  }

  function confetti() {
    if (reduce) return;
    var L = fxLayer(), cols = ['#ffd75e', '#fff1a8', '#e11d48', '#8b5cf6', '#14b8a6', '#ffffff'];
    for (var i = 0; i < 90; i++) {
      var c = document.createElement('i');
      c.className = 'rconf';
      c.style.left = (Math.random() * 100) + 'vw';
      c.style.background = cols[i % cols.length];
      c.style.animationDelay = (Math.random() * 0.6).toFixed(2) + 's';
      c.style.setProperty('--dx', (Math.random() * 160 - 80).toFixed(0) + 'px');
      c.style.setProperty('--r', (Math.random() * 900 - 450).toFixed(0) + 'deg');
      c.style.setProperty('--t', (2.2 + Math.random() * 2).toFixed(2) + 's');
      L.appendChild(c); gone(c, 5400);
    }
  }

  function dust() {
    if (reduce || document.getElementById('royal-dust') || !document.body) return;
    var d = document.createElement('div');
    d.id = 'royal-dust';
    for (var i = 0; i < 26; i++) {
      var e = document.createElement('i');
      e.style.left = (Math.random() * 100).toFixed(1) + '%';
      e.style.setProperty('--s', (3 + Math.random() * 5).toFixed(1) + 'px');
      e.style.setProperty('--d', (9 + Math.random() * 10).toFixed(1) + 's');
      e.style.setProperty('--l', '-' + (Math.random() * 18).toFixed(1) + 's');
      e.style.setProperty('--x', (Math.random() * 120 - 60).toFixed(0) + 'px');
      d.appendChild(e);
    }
    document.body.appendChild(d);
  }

  /* confetti when the status line announces a finished game */
  var WIN = /checkmate|\bwins?\b|\bwon\b|victory/i, statusEl = null, lastStatus = '';
  function watchStatus() {
    var el = document.getElementById('status');
    if (!el || el === statusEl) return;
    statusEl = el; lastStatus = el.textContent;
    new MutationObserver(function () {
      var t = el.textContent;
      if (t !== lastStatus) { lastStatus = t; if (WIN.test(t)) confetti(); }
    }).observe(el, { childList: true, subtree: true, characterData: true });
  }

  /* ================================================================
     5.  PAINT THE BOARD
     ================================================================ */
  var board = null, obs = null, queued = false, prev = [], first = true;

  function paint() {
    queued = false;
    if (!board || !obs) return;
    obs.disconnect();
    try {
      var sqs = board.querySelectorAll('.sq'), now = [], bursts = [];
      for (var i = 0; i < sqs.length; i++) {
        var sq = sqs[i];
        var old = sq.querySelector(':scope > img.pc');
        var pc = pieceOf(sq), key = pc ? pc.c + pc.t : '';
        now[i] = key;
        if (!pc) { if (old) old.remove(); sq.classList.remove('has-royal'); continue; }
        if (old && old.getAttribute('data-key') === key) { sq.classList.add('has-royal'); continue; }
        if (old) old.remove();
        sq.insertAdjacentHTML('afterbegin', pieceHTML(pc.t, pc.c));
        sq.classList.add('has-royal');
        var img = sq.firstElementChild;
        if (first) {                                   /* opening parade: pieces drop in one after another */
          img.style.animationDelay = (i * 14) + 'ms';
          img.style.animationFillMode = 'backwards';
          img.addEventListener('animationend', function (e) {
            e.target.style.animationDelay = ''; e.target.style.animationFillMode = '';
          }, { once: true });
        } else if (prev[i] === key) {                  /* board was rebuilt, piece did not move: no replay */
          img.classList.add('still');
        } else {
          bursts.push(sq);                             /* piece arrived here: sparkle */
        }
      }
      if (sqs.length) { prev = now; first = false; }
      if (bursts.length && bursts.length <= 3) bursts.forEach(burst);
    } catch (err) { /* never break the game */ }
    watch();
  }
  function watch() {
    if (board && obs) obs.observe(board, { childList: true, subtree: true, characterData: true, attributes: true, attributeFilter: ['data-piece', 'class'] });
  }
  function schedule() { if (!queued) { queued = true; requestAnimationFrame(paint); } }

  var GAME_NAME = 'Reuben Soul World Peace Chess';
  function applyName() {
    document.title = GAME_NAME;
    var h = document.querySelector('main h1') || document.querySelector('h1');
    if (h && h.textContent !== GAME_NAME) h.textContent = GAME_NAME;
  }

  function attach(b) {
    if (obs) obs.disconnect();
    board = b; first = true; prev = [];
    obs = new MutationObserver(function (m) {
      for (var i = 0; i < m.length; i++) {
        var t = m[i].target;
        if (!(t.nodeType === 1 && t.closest && t.closest('img.pc'))) { schedule(); return; }
      }
    });
    watch();
    paint();
  }

  function start() {
    applyName();
    dust();
    watchStatus();
    var b = document.getElementById('board');
    if (b) attach(b);
    /* safety net: if the game builds or rebuilds #board later, hook it up again */
    setInterval(function () {
      var nb = document.getElementById('board');
      if (nb && nb !== board) attach(nb); else if (board) schedule();
      watchStatus();
    }, 1200);
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start);
  else start();
})();
