const $=s=>document.querySelector(s);
const esc=s=>String(s??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const H={"Content-Type":"application/json","X-Guardian":"1"};
async function post(p,b){const r=await fetch(p,{method:"POST",headers:H,body:JSON.stringify(b||{})});if(!r.ok)throw new Error("HTTP "+r.status);return r.json();}
let FINDINGS=[],FILTER="all";
function render(){
  const order={critical:0,warning:1,review:2,limited:3,info:4};
  $("#results").innerHTML=FINDINGS.filter(f=>FILTER==="all"||f.level===FILTER||(FILTER==="review"&&f.level==="critical")).sort((a,b)=>order[a.level]-order[b.level])
   .map(f=>`<article class="finding"><span class="tag ${esc(f.level)}">${esc(f.level.toUpperCase())} · ${esc(f.category||"")}</span><h3>${esc(f.title)}</h3><p>${esc(f.detail)}</p>${f.action?`<p><b>Next step:</b> ${esc(f.action)}</p>`:""}</article>`).join("");
}
document.querySelectorAll(".chip").forEach(b=>b.addEventListener("click",()=>{document.querySelectorAll(".chip").forEach(x=>x.classList.remove("on"));b.classList.add("on");FILTER=b.dataset.l;render();}));
async function loadHist(){try{const h=await (await fetch("/api/history")).json();if(h.length){$("#hist").hidden=false;$("#histbody").innerHTML=h.slice().reverse().map(x=>`<p>${esc(x.when.slice(0,16).replace("T"," "))} — <b>${esc(x.score)}/100</b> ${esc(x.grade)}</p>`).join("");}}catch(e){}}
$("#scan").addEventListener("click",async()=>{
  $("#scan").disabled=true;$("#status").textContent="Scanning… this can take up to a minute.";$("#results").innerHTML="";
  try{const d=await post("/api/scan",{offline:$("#offline").checked});FINDINGS=d.findings;
    $("#score").hidden=false;$("#filters").hidden=false;$("#dl").hidden=false;
    $("#score").innerHTML=`<div class="big ${d.score<65?"bad":""}">${d.score}/100</div><h2>${esc(d.grade)}</h2><p>${Object.entries(d.counts).map(([k,v])=>`${v} ${esc(k)}`).join(" · ")}</p><p>Heuristic score: it only counts what this device let the scanner see.</p>`;
    render();$("#status").textContent="Scan complete. Saved: "+d.report_path;loadHist();
  }catch(e){$("#status").textContent="Scan could not run: "+e;}finally{$("#scan").disabled=false;}});
$("#clean").addEventListener("click",async()=>{
  if(!confirm("Remove only temporary files made by this Guardian app? Photos, downloads, messages and system caches are never touched."))return;
  try{const d=await post("/api/clean");$("#status").textContent=`Cleanup complete: ${d.files_removed} Guardian temp files removed.`;}catch(e){$("#status").textContent="Cleanup failed: "+e;}});
function showCheck(d){const lab={no_flags:"No simple red flags",low_flags:"Low caution",medium_risk:"MEDIUM RISK",high_risk:"HIGH RISK",not_checked:"Nothing to check",review:"Review"}[d.verdict]||d.verdict;
  $("#chkout").textContent=lab+" (score "+d.score+")\n- "+d.reasons.join("\n- ")+"\n\nThis does not prove safety. The link was never opened.";}
$("#urlbtn").addEventListener("click",async()=>{try{showCheck(await post("/api/check-url",{url:$("#url").value}));}catch(e){$("#chkout").textContent="Could not check: "+e;}});
$("#txtbtn").addEventListener("click",async()=>{try{showCheck(await post("/api/check-text",{text:$("#txt").value}));}catch(e){$("#chkout").textContent="Could not check: "+e;}});
$("#ads").addEventListener("click",async()=>{$("#adout").textContent="Testing 20 well-known ad and tracker names…";
  try{const d=await post("/api/adblock");const lab={strong:"STRONG — ads/trackers are being blocked",partial:"PARTIAL blocking",none:"NO blocking detected",inconclusive:"Inconclusive (no connection)"}[d.status];
   $("#adout").textContent=lab+"\n"+d.blocked+" of "+d.total+" test domains blocked ("+d.percent+"%)\n\n"+d.note+"\n\nNot blocked: "+d.details.filter(x=>x.state==="reached").map(x=>x.domain).join(", ");}
  catch(e){$("#adout").textContent="Test failed: "+e;}});
loadHist();
if("serviceWorker" in navigator)navigator.serviceWorker.register("/sw.js").catch(()=>{});
