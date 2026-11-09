"use strict";
(() => {
 let ctx=null, enabled=false;
 const button=document.getElementById('moveSoundToggle');
 const status=document.getElementById('soundStatus');
 function play(){
  if(!enabled||!ctx||ctx.state!=='running')return;
  const t=ctx.currentTime,osc=ctx.createOscillator(),gain=ctx.createGain();
  osc.type='triangle';osc.frequency.setValueAtTime(650,t);
  osc.frequency.exponentialRampToValueAtTime(190,t+.065);
  gain.gain.setValueAtTime(.0001,t);gain.gain.exponentialRampToValueAtTime(.12,t+.003);
  gain.gain.exponentialRampToValueAtTime(.0001,t+.09);
  osc.connect(gain);gain.connect(ctx.destination);osc.start(t);osc.stop(t+.10);
  osc.onended=()=>{osc.disconnect();gain.disconnect();};
 }
 window.wpcMoveSound=play;
 button.onclick=async()=>{
  try{
   if(!enabled){
    const Audio=window.AudioContext||window.webkitAudioContext;
    if(!Audio)throw Error('Browser audio is unavailable.');
    if(!ctx)ctx=new Audio();await ctx.resume();
    if(ctx.state!=='running')throw Error('Browser blocked audio. Try clicking again.');
    enabled=true;button.textContent='Move sounds: ON — click to mute';
    button.setAttribute('aria-pressed','true');status.textContent='';play();
   }else{enabled=false;button.textContent='Enable move sounds';button.setAttribute('aria-pressed','false');}
  }catch(e){status.textContent=e.message;}
 };
 document.addEventListener('visibilitychange',()=>{
  if(!document.hidden&&enabled&&ctx&&ctx.state==='suspended')ctx.resume().catch(()=>{});
 });
})();
