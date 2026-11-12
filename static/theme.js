/* Reuben World Peace Unity Chess — upright, spaced, high-contrast revision.
   Load after royal-theme.js. Replaces only the earlier theme.js add-on.
   Existing SVG artwork and all game controls remain unchanged. */
(function(){'use strict';
var css=`
/* Wider on desktop, still responsive on phones. No tilted or rotated board. */
main{max-width:880px}
#board{--piece-h:94%;position:relative;isolation:isolate;transform:none;perspective:none;display:grid;grid-template-columns:repeat(8,minmax(0,1fr));margin-top:18px;margin-bottom:22px;overflow:hidden;border:8px solid transparent;border-radius:6px;background:linear-gradient(#1b2027,#1b2027) padding-box,linear-gradient(135deg,#fff1b5,#b88b35 30%,#efce79 55%,#6e501c 80%,#ffe7a1) border-box;box-shadow:0 0 0 1px #644c27,0 8px 0 #382a19,0 15px 25px #0008}
#board .sq{position:relative;min-width:0;min-height:0;aspect-ratio:1;overflow:hidden;transform:none;perspective:none;padding:0;border:0;border-radius:0;isolation:isolate}
/* Neutral squares distinguish both white and black armies. */
#board .sq.light{background:linear-gradient(140deg,#eee9df,#d9d3c7)}
#board .sq.dark{background:linear-gradient(140deg,#78909d,#526b7a)}
#board .sq:hover:not(:disabled){transform:none;box-shadow:inset 0 0 0 3px #e8ba51}
#board .sq.selected{box-shadow:inset 0 0 0 4px #ffda72!important}
/* Fit the entire standing SVG within the square, with a narrow footprint.
   Width and height are bounded; the SVG retains its own aspect ratio. */
#board .sq svg.pc{position:absolute;left:50%;right:auto;top:auto;bottom:3%;margin:0;width:74%;height:94%;max-width:74%;max-height:94%;z-index:1;overflow:hidden;pointer-events:none;transform:translateX(-50%);transform-origin:50% 100%;filter:drop-shadow(0 2px 1px #0008);transition:none}
#board .sq:hover svg.pc{transform:translateX(-50%);filter:drop-shadow(0 2px 1px #0008)}
#board .sq svg.pc *{pointer-events:none}
/* Recolor the ORIGINAL piece bodies without editing their SVG paths. */
#board svg.pc[data-key^="w"] [fill="url(#rg-red)"]{fill:#fff8e9;stroke:#695a43}
#board svg.pc[data-key^="b"] [fill="url(#rg-night)"]{fill:#111820;stroke:#a7b2bd}
/* Retain gold regalia; give the two armies different gold intensity. */
#board svg.pc[data-key^="w"] [fill="url(#rg-gold)"]{fill:#edcf85;stroke:#79602f}
#board svg.pc[data-key^="b"] [fill="url(#rg-gold)"]{fill:#a7843c;stroke:#e0c179}
#board svg.pc[data-key^="w"] [fill="url(#rg-pearl)"]{fill:#ffffff;stroke:#79602f}
#board svg.pc[data-key^="b"] [fill="url(#rg-pearl)"]{fill:#202a36;stroke:#d1b475}
#board svg.pc[data-key^="w"] [stroke="rgba(255,255,255,.25)"],
#board svg.pc[data-key^="w"] [stroke="rgba(255,255,255,.3)"],
#board svg.pc[data-key^="w"] [stroke="rgba(255,255,255,.35)"]{stroke:#b4a58c}
#board .sq .coord{position:absolute;left:3px;bottom:2px;z-index:3;font:10px Arial,sans-serif;color:#273444;opacity:1;pointer-events:none}
#board .sq.dark .coord{color:#fff9e9;text-shadow:0 1px 1px #263543}
#board .sq.legal:after{z-index:4;pointer-events:none;background:#36d692;border:1px solid #103e2d;box-shadow:0 0 0 2px #ffffff80}
#board .sq:focus-visible{outline:3px solid #10e5a3;outline-offset:-4px}
@media(max-width:520px){#board{border-width:5px}#board .sq .coord{font-size:8px}}
`;
function apply(){if(!document.getElementById('board'))return;var style=document.getElementById('unity-royal-polish');if(!style){style=document.createElement('style');style.id='unity-royal-polish';document.head.appendChild(style);}style.textContent=css;}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',apply,{once:true});else apply();
})();
