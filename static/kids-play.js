"use strict";
(()=>{
 const kid=location.pathname==='/kids'||new URLSearchParams(location.search).has('kids');
 const mode=document.getElementById('mode'),level=document.getElementById('difficulty');
 function update(){level.disabled=mode.value!=='ai';}
 mode.addEventListener('change',update);
 if(kid){
   document.title='World Peace Chess — Let’s Play';
   document.querySelector('h1').textContent='Let’s Play Chess';
   document.querySelector('h1+p').textContent='Enter your play code, pick an easy level, and press Play chess.';
   mode.value='ai';
   for(const option of mode.options)if(option.value!=='ai')option.remove();
   mode.hidden=true;
   const color=document.getElementById('hostColor');color.disabled=true;color.hidden=true;
   const control=document.getElementById('control');control.value='10+5';
   const code=document.getElementById('hostCode');
   code.placeholder='Your play code — leave blank after your first game';
   document.querySelector('label[for="hostCode"]').textContent='Your play code';
   const strong=level.querySelector('option[value="strong"]');if(strong)strong.remove();
   level.value='first_steps';
   document.getElementById('create').textContent='Play chess';
   const notes=document.getElementById('notes');if(notes)notes.hidden=true;
   const teaching=document.querySelector('a[href="/lesson"]');if(teaching)teaching.hidden=true;
   const status=document.getElementById('status');
   if(!location.pathname.startsWith('/room/'))status.textContent='Pick a level and press Play chess. Then press Start game.';
   const start=document.getElementById('start');
   new MutationObserver(()=>{if(start.textContent==='Start clock')start.textContent='Start game';}).observe(start,{childList:true});
   if(start.textContent==='Start clock')start.textContent='Start game';
   const helper=document.getElementById('childHelp');
   if(helper)helper.textContent='White goes first. Click a piece, then its destination. Your play code allows four new computer games. Finish, resign, or cancel your previous game before creating another.';
 }
 update();
})();
