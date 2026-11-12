
/* Reuben World Peace Unity Chess: appearance only. */
(function () {
"use strict";
let serial = 0;

function artwork(side, type) {
  const white = side === "w";
  const id = "uprightRoyal" + (++serial);
  const body = "url(#" + id + "body)";
  const gold = "url(#" + id + "gold)";
  const edge = white ? "#796846" : "#aab5c4";
  const jewel = white ? "#07885d" : "#38d7e8";

  const defs = `<defs>
    <linearGradient id="${id}body">
      <stop stop-color="${white ? "#b9aa8b" : "#020408"}"/>
      <stop offset=".32" stop-color="${white ? "#ffffff" : "#596779"}"/>
      <stop offset=".55" stop-color="${white ? "#fffdf4" : "#1c2736"}"/>
      <stop offset="1" stop-color="${white ? "#bbae92" : "#020408"}"/>
    </linearGradient>
    <linearGradient id="${id}gold">
      <stop stop-color="#78521c"/>
      <stop offset=".38" stop-color="#fff0b0"/>
      <stop offset=".62" stop-color="#ddb454"/>
      <stop offset="1" stop-color="#79521d"/>
    </linearGradient>
  </defs>`;

  const pedestal = `
    <ellipse cx="50" cy="94" rx="29" ry="3" fill="#0005"/>
    <path d="M27 88h46l5 7H22Z"
      fill="${gold}" stroke="#71501f" stroke-width="1.3"/>
    <path d="M30 83h40l3 5H27Z"
      fill="${body}" stroke="${edge}" stroke-width="1.2"/>
  `;

  const stem = `
    <path d="M42 43h16q0 21 10 39H32q10-18 10-39Z"
      fill="${body}" stroke="${edge}" stroke-width="1.4"/>
    <path d="M43 49q-1 18-6 29"
      fill="none" stroke="${white ? "#fff" : "#8e9eaf"}"
      stroke-opacity=".65" stroke-width="2"/>
    <ellipse cx="50" cy="46" rx="17" ry="4"
      fill="${gold}" stroke="#71501f"/>
  `;

  let top = "";

  if (type === "K") {
    top = `
      <path d="M35 41l-3-18 11 7 7-13 7 13 11-7-3 18Z"
        fill="${body}" stroke="${edge}" stroke-width="1.5"/>
      <path d="M34 39h32v5H34Z"
        fill="${gold}" stroke="#71501f"/>
      <path d="M47 4h6v15h-6Z M41 9h18v5H41Z"
        fill="${gold}" stroke="#71501f"/>
      <circle cx="50" cy="33" r="3.5"
        fill="${jewel}" stroke="#8b6a2a"/>
    `;
  } else if (type === "Q") {
    top = `
      <path d="M34 41l-7-20 13 10 4-17 6 15 6-15 4 17
               13-10-7 20Z"
        fill="${body}" stroke="${edge}" stroke-width="1.5"/>
      <path d="M33 39h34v5H33Z"
        fill="${gold}" stroke="#71501f"/>
      <g fill="${gold}" stroke="#71501f">
        <circle cx="27" cy="18" r="3"/>
        <circle cx="44" cy="11" r="3"/>
        <circle cx="56" cy="11" r="3"/>
        <circle cx="73" cy="18" r="3"/>
      </g>
      <circle cx="50" cy="35" r="3" fill="${jewel}"/>
    `;
  } else if (type === "B") {
    top = `
      <path d="M50 9q22 20 12 31l-7 5H45l-7-5Q28 29 50 9Z"
        fill="${body}" stroke="${edge}" stroke-width="1.5"/>
      <path d="M48 27l10-10"
        stroke="${gold}" stroke-width="4"/>
      <circle cx="50" cy="7" r="4"
        fill="${gold}" stroke="#71501f"/>
      <circle cx="50" cy="37" r="3" fill="${jewel}"/>
    `;
  } else if (type === "N") {
    top = `
      <path d="M34 45q-6-10 2-20l9-10-1-9 9 6
               q22-2 20 29l-4 39H34q0-18 14-32l-9 6-9-4Z"
        fill="${body}" stroke="${edge}" stroke-width="1.5"
        stroke-linejoin="round"/>
      <path d="M57 14q14 15 10 43l-3 22"
        fill="none" stroke="${gold}" stroke-width="4"/>
      <path d="M43 26l-8 17" stroke="${gold}" stroke-width="2.5"/>
      <circle cx="47" cy="25" r="2.5"
        fill="${white ? "#17202a" : "#f6e2a4"}"/>
      <path d="M33 46l8 1" stroke="${edge}" stroke-width="1.5"/>
    `;
  } else if (type === "R") {
    top = `
      <path d="M35 81l4-40h22l4 40Z"
        fill="${body}" stroke="${edge}" stroke-width="1.5"/>
      <path d="M33 40V17h8v8h6v-8h7v8h6v-8h8v23Z"
        fill="${body}" stroke="${edge}" stroke-width="1.5"/>
      <path d="M32 39h37v5H32Z"
        fill="${gold}" stroke="#71501f"/>
      <path d="M45 81V67q5-9 10 0v14Z"
        fill="${white ? "#776a54" : "#020408"}"
        stroke="${gold}"/>
      <path d="M39 54h22M37 65h8m10 0h8"
        stroke="${edge}" opacity=".5"/>
    `;
  } else {
    top = `
      <circle cx="50" cy="31" r="13"
        fill="${body}" stroke="${edge}" stroke-width="1.5"/>
      <path d="M42 24q3-4 8-4"
        stroke="${white ? "#fff" : "#a2b1c5"}"
        stroke-width="2" fill="none" opacity=".8"/>
      <ellipse cx="50" cy="45" rx="16" ry="4"
        fill="${gold}" stroke="#71501f"/>
      <circle cx="50" cy="31" r="3" fill="${jewel}"/>
    `;
  }

  return defs + pedestal
    + (type === "N" || type === "R" ? "" : stem)
    + top;
}

const css = `
main{max-width:900px}
#board{
  display:grid;grid-template-columns:repeat(8,minmax(0,1fr));
  position:relative;isolation:isolate;transform:none;perspective:none;
  overflow:hidden;margin-top:18px;margin-bottom:24px;
  border:8px solid #bc9544;border-radius:4px;background:#000;
  box-shadow:0 0 0 2px #513c19,0 8px 0 #382914,0 17px 27px #0008
}
#board .sq{
  position:relative;min-width:0;min-height:0;aspect-ratio:1;
  overflow:hidden;padding:0;border:0;border-radius:0;
  transform:none;isolation:isolate
}
#board .sq.light{background:#fff}
#board .sq.dark{background:#000}
#board .sq:hover:not(:disabled){
  transform:none;box-shadow:inset 0 0 0 3px #d7b35d
}
#board .sq.selected{
  box-shadow:inset 0 0 0 4px #ffd46b!important
}
#board .sq svg.pc,#board .sq:hover svg.pc{
  position:absolute;left:50%;right:auto;top:auto;bottom:2%;
  width:82%;height:95%;max-width:82%;max-height:95%;
  margin:0;overflow:hidden;z-index:1;pointer-events:none;
  transform:translateX(-50%);transition:none;
  filter:drop-shadow(0 1px 1px #0007)
}
#board .sq svg.pc *{pointer-events:none}
#board .sq .coord{
  z-index:3;color:#333;opacity:1;pointer-events:none;
  font:10px Arial,sans-serif
}
#board .sq.dark .coord{color:#fff}
#board .sq.legal:after{
  z-index:4;pointer-events:none;background:#24d999;
  border:1px solid #fff;box-shadow:0 0 0 1px #17533d
}
#board .sq:focus-visible{
  outline:3px solid #25ffc1;outline-offset:-4px
}
@media(max-width:520px){
  #board{border-width:5px}
  #board .sq .coord{font-size:8px}
}
`;

function start() {
  const board = document.getElementById("board");
  if (!board) return;

  let style = document.getElementById("unity-royal-polish");
  if (!style) {
    style = document.createElement("style");
    style.id = "unity-royal-polish";
    document.head.appendChild(style);
  }
  style.textContent = css;

  let queued = false;
  const observer = new MutationObserver(function () {
    if (!queued) {
      queued = true;
      requestAnimationFrame(paint);
    }
  });

  function watch() {
    observer.observe(board, {
      childList:true,
      subtree:true,
      attributes:true,
      attributeFilter:["data-key"]
    });
  }

  function paint() {
    queued = false;
    observer.disconnect();
    try {
      for (const svg of board.querySelectorAll("svg.pc")) {
        const key = svg.getAttribute("data-key") || "";
        if (!/^[wb][KQRBNP]$/.test(key)) continue;
        if (svg.getAttribute("data-standing-key") === key) continue;
        svg.setAttribute("viewBox", "16 0 68 100");
        svg.setAttribute("preserveAspectRatio", "xMidYMax meet");
        svg.innerHTML = artwork(key[0], key[1]);
        svg.setAttribute("data-standing-key", key);
      }
    } catch (error) {
      console.warn("Royal artwork update:", error);
    } finally {
      watch();
    }
  }

  paint();
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", start, {once:true});
} else {
  start();
}
})();
