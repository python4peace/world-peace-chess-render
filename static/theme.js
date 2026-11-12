/* Reuben World Peace Unity Chess. Load after royal-theme.js. */
(function(){'use strict';
const css=`
#board{--piece-h:158.6%;position:relative;isolation:isolate;grid-template-columns:repeat(8,minmax(0,1fr));margin-top:38px;margin-bottom:26px;overflow:visible;border:10px solid transparent;border-radius:7px;background:linear-gradient(#101b2c,#101b2c) padding-box,linear-gradient(135deg,#fff6c8,#d6ab49 15%,#8c601b 30%,#ffedab 45%,#c99b32 62%,#775018 80%,#ffe9a1) border-box;box-shadow:0 0 0 1px #ffe7a7,0 0 0 3px #54370d,0 8px 0 #4a3014,0 11px 0 #24180c,0 20px 32px #0009}
#board .sq{min-width:0;position:relative;overflow:visible;transform:none}
#board .sq.light{background:radial-gradient(ellipse at 25% 20%,#ffffff80,transparent 65%),linear-gradient(145deg,#fff5d9,#ead5a8 65%,#d6bc89)}
#board .sq.dark{background:radial-gradient(ellipse at 25% 20%,#e9828938,transparent 70%),linear-gradient(145deg,#963a49,#682031 65%,#471323)}
#board .sq:hover:not(:disabled){transform:none;box-shadow:inset 0 0 0 3px #ffe08bb8}
#board .sq.selected{box-shadow:inset 0 0 0 5px #ffe29a,inset 0 0 22px #ffde88a6!important}
#board .sq svg.pc{position:absolute;left:50%;right:auto;bottom:-5%;margin:0;height:var(--piece-h);width:auto;max-width:none;max-height:none;z-index:2;overflow:visible;pointer-events:none;transform:translateX(-50%);transform-origin:50% 90%;filter:drop-shadow(0 5px 3px #000a) drop-shadow(0 -1px 0 #ffedb33d);transition:filter .15s ease}
#board .sq:hover svg.pc{transform:translateX(-50%);filter:drop-shadow(0 5px 3px #000a) drop-shadow(0 0 3px #ffde8280)}
#board .sq svg.pc *{pointer-events:none}#board .sq .coord{z-index:4;pointer-events:none;opacity:.95}#board .sq.dark .coord{color:#fff0bd;text-shadow:0 1px 2px #310812}
#board .sq.legal:after{z-index:5;pointer-events:none;background:radial-gradient(circle at 35% 30%,#fffbe0,#e4b842 60%,#8e6418);box-shadow:0 0 0 1px #654611,0 0 8px #ffe18fa6}
#board .sq:focus-visible{outline:3px solid #8fffd1;outline-offset:-4px}
@media(prefers-reduced-motion:reduce){#board .sq svg.pc{transition:none}}
`;
function apply(){if(!document.getElementById('board'))return;let s=document.getElementById('unity-royal-polish');if(!s){s=document.createElement('style');s.id='unity-royal-polish';document.head.append(s);}s.textContent=css;}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',apply,{once:true});else apply();
})();
