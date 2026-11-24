"use strict";
(()=>{
 const kid=['/beginner','/kids'].includes(location.pathname)||new URLSearchParams(location.search).has('beginner')||new URLSearchParams(location.search).has('kids');
 const mode=document.getElementById('mode'),level=document.getElementById('difficulty');
 function update(){level.disabled=mode.value!=='ai';}
 mode.addEventListener('change',update);
 if(kid){
   document.title='World Peace Chess — Beginner Play';
   document.querySelector('h1').textContent='Beginner Play';
   document.querySelector('h1+p').textContent='Enter your play code, choose a level, and press Play chess.';
   const accessHelp=document.getElementById('accessHelp');
   if(accessHelp)accessHelp.textContent='One code entry allows four new computer games at the four easier levels. Refreshing does not use another game. Enter the code again after four games or if access resets.';
   document.querySelectorAll('a[href="/lesson"]').forEach(link=>{link.hidden=true;});
   mode.value='ai';
   for(const option of mode.options)if(option.value!=='ai')option.remove();
   mode.hidden=true;
   const color=document.getElementById('hostColor');color.disabled=true;color.hidden=true;
   const control=document.getElementById('control');control.value='10+5';
   const code=document.getElementById('hostCode');
   code.placeholder='Your play code — enter again after four games';
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
