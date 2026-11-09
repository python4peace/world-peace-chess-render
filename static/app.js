"use strict";
const $=id=>document.getElementById(id);
let rid=location.pathname.startsWith('/room/')?location.pathname.split('/')[2]:null;
const watching=new URLSearchParams(location.search).has('watch');
if(watching)document.body.classList.add('clean');
let token='',invite='',state=null,game=null,selected=null,busy=false,polling=false,received=performance.now(),joinToken='';
const symbols={P:'♙',N:'♘',B:'♗',R:'♖',Q:'♕',K:'♔',p:'♟',n:'♞',b:'♝',r:'♜',q:'♛',k:'♚'};
function loadSeat(){if(!rid||watching)return;try{token=localStorage.getItem('wpc-seat-'+rid)||'';invite=localStorage.getItem('wpc-invite-'+rid)||'';}catch(e){}}
function saveSeat(){try{localStorage.setItem('wpc-seat-'+rid,token);if(invite)localStorage.setItem('wpc-invite-'+rid,invite);}catch(e){$('notice').textContent='Storage unavailable: do not refresh this player window.';}}
loadSeat();
const hash=new URLSearchParams(location.hash.slice(1));
if(!watching)joinToken=hash.get('join')||'';
// Preserve an unaccepted invitation across reloads without keeping it in the URL.
try{if(rid&&!watching){if(joinToken)sessionStorage.setItem('wpc-join-'+rid,joinToken);else joinToken=sessionStorage.getItem('wpc-join-'+rid)||'';}}catch(e){}
if(location.hash)history.replaceState(null,'',location.pathname+location.search);
async function api(path,method='GET',body){
 const response=await fetch(path,{method,headers:{'Content-Type':'application/json','X-Player-Token':token},body:body===undefined?undefined:JSON.stringify(body),cache:'no-store',signal:AbortSignal.timeout(15000)});
 let d;try{d=await response.json();}catch(e){throw Error('Service is starting or unavailable. Wait, then retry.');}
 if(!response.ok)throw Error(d.error||'Request failed');return d;
}
function buildLinks(){const box=$('links');box.innerHTML='';if(!rid||watching)return;const base=location.origin+'/room/'+rid,items=[];
 if(invite&&state&&state.role==='w')items.push(['Private opponent invitation — send only to your opponent',base+'#join='+invite]);
 items.push(['Public spectator link — safe for viewers',base+'?watch=1']);
 for(const [label,url] of items){const l=document.createElement('label');l.textContent=label;const input=document.createElement('input');input.readOnly=true;input.value=url;input.onclick=()=>input.select();const b=document.createElement('button');b.textContent='Copy link';b.onclick=async()=>{try{await navigator.clipboard.writeText(url);b.textContent='Copied';}catch(e){input.focus();input.select();$('notice').textContent='Select and copy the link manually.';}};box.append(l,input,b);}
}
function accept(s){
 const previous=state;
 const changed=!state||s.fen!==state.fen||s.role!==state.role;
 state=s;received=performance.now();
 if(previous && previous.boot_id===s.boot_id && previous._room===rid && s.moves.length>previous.moves.length && window.wpcMoveSound)window.wpcMoveSound();
 s._room=rid;
 if(changed){game.load(s.fen);selected=null;drawBoard();}
 $('status').textContent=s.message+(s.result!=='*'?' — '+s.result:'')+' · '+s.control+' · '+(s.role==='spectator'?'Spectator':s.mode==='selfplay'?'You are the self-play host':s.role==='w'?'You are White':'You are Black');
 $('resign').disabled=$('draw').disabled=s.phase!=='playing'||s.role==='spectator'||s.mode==='selfplay';
 $('start').hidden=watching||!(['ai','selfplay'].includes(s.mode)&&s.phase==='waiting'&&s.role==='w');
 $('stopSelfplay').hidden=watching||!(s.mode==='selfplay'&&s.phase==='playing'&&s.role==='w');
 $('start').textContent=s.mode==='selfplay'?'Start automatic self-play':'Start clock';
 $('cancel').hidden=watching||!(s.phase==='waiting'&&s.role==='w');
 $('join').hidden=watching||!(joinToken&&s.mode==='friend'&&s.role!=='w'&&s.role!=='b'&&s.phase!=='ended');
 $('spectate').disabled=false;$('pgn').hidden=false;$('pgn').href='/api/room/'+rid+'/pgn';
 const rows=[];for(let i=0;i<s.moves.length;i+=2)rows.push((i/2+1)+'. '+s.moves[i]+' '+(s.moves[i+1]||''));$('moves').textContent=rows.join('   ');
 // Do not rebuild invitation inputs on every clock update.
 const key=rid+'|'+s.role+'|'+invite;if($('links').dataset.key!==key){buildLinks();$('links').dataset.key=key;}
 clocks();
}
async function poll(){
 if(!rid||polling||busy)return;polling=true;const currentRid=rid;
 try{const s=await api('/api/room/'+currentRid);if(currentRid===rid&&!busy){accept(s);$('notice').textContent='';}}
 catch(e){if(currentRid===rid)$('notice').textContent=e.message+' Server clocks may still be running.';}
 finally{polling=false;}
}
async function act(action,extra={}){
 if(busy||!rid)return;busy=true;
 try{$('notice').textContent='';accept(await api('/api/room/'+rid+'/action','POST',{action,...extra}));}
 catch(e){$('notice').textContent=e.message;}
 finally{busy=false;}
}
function drawBoard(){
 const el=$('board');el.innerHTML='';const black=state&&state.role==='b';
 const ranks=black?[0,1,2,3,4,5,6,7]:[7,6,5,4,3,2,1,0],files=black?[7,6,5,4,3,2,1,0]:[0,1,2,3,4,5,6,7];
 const legal=selected?game.moves({square:selected,verbose:true}).map(m=>m.to):[];
 for(const r of ranks)for(const f of files){
  const sq=String.fromCharCode(97+f)+(r+1),p=game.get(sq),b=document.createElement('button');
  b.className='sq '+((r+f)%2?'light':'dark')+(selected===sq?' selected':'')+(legal.includes(sq)?' legal':'');
  b.setAttribute('aria-label',sq+(p?' '+p.color+p.type:''));
  if(p)b.append(document.createTextNode(symbols[p.color==='w'?p.type.toUpperCase():p.type]));
  const l=document.createElement('span');l.className='coord';l.textContent=sq;b.append(l);b.onclick=()=>clickSquare(sq);el.append(b);
 }
}
function clickSquare(sq){
 if(!state||busy||watching||state.phase!=='playing'||state.mode==='selfplay'||state.role!==state.turn)return;
 const p=game.get(sq);if(p&&p.color===state.role){selected=selected===sq?null:sq;drawBoard();return;}
 if(!selected)return;
 const choices=game.moves({square:selected,verbose:true}).filter(m=>m.to===sq);
 if(!choices.length){selected=null;drawBoard();return;}
 let promotion='';if(choices.some(m=>m.promotion)){promotion=(prompt('Promote to q, r, b, or n','q')||'').toLowerCase();if(!['q','r','b','n'].includes(promotion))return;}
 const move=selected+sq+promotion;selected=null;drawBoard();act('move',{move,revision:state.revision});
}
function fmt(s){const n=Math.ceil(Math.max(0,s)*10);return String(Math.floor(n/600)).padStart(2,'0')+':'+String(Math.floor(n/10)%60).padStart(2,'0')+'.'+n%10;}
function clocks(){if(!state)return;const reverse=state.role==='b';
 for(const [pos,side] of [['top',reverse?'w':'b'],['bottom',reverse?'b':'w']]){
  const running=state.phase==='playing'&&state.turn===side,key=side==='w'?'white':'black';
  const value=Math.max(0,state[key]-(running?(performance.now()-received)/1000:0));
  $(pos+'Time').textContent=fmt(value);$(pos+'Name').textContent=state.mode==='selfplay'?(side==='w'?'WHITE · Stockfish':'BLACK · Stockfish'):(side==='w'?'WHITE':state.mode==='ai'?'BLACK · Stockfish':'BLACK');
  $(pos+'Box').classList.toggle('running',running);$(pos+'Box').classList.toggle('low',value<30);
 }
}
$('create').onclick=async()=>{
 if(busy)return;
 if(state&&state.phase!=='ended'&&!confirm('The old game will remain open and its clock may continue. Create another game?'))return;
 busy=true;
 try{
  const d=await api('/api/new','POST',{host_code:$('hostCode').value,mode:$('mode').value,control:$('control').value});
  rid=d.room;token=d.token;invite=d.invite;joinToken='';state=null;saveSeat();history.pushState(null,'','/room/'+rid);
  $('hostCode').value='';accept(await api('/api/room/'+rid));$('notice').textContent='';
 }catch(e){$('notice').textContent=e.message;}finally{busy=false;}
};
$('join').onclick=async()=>{
 if(busy)return;busy=true;
 try{const d=await api('/api/room/'+rid+'/join','POST',{token:joinToken});token=joinToken;joinToken='';saveSeat();try{sessionStorage.removeItem('wpc-join-'+rid);}catch(e){}accept(d);}
 catch(e){$('notice').textContent=e.message;}finally{busy=false;}
};
$('stopSelfplay').onclick=()=>{if(confirm('Stop this automatic game?'))act('stop_selfplay');};
$('start').onclick=()=>act('start');$('cancel').onclick=()=>act('cancel');
$('resign').onclick=()=>{if(confirm('Resign this game?'))act('resign');};$('draw').onclick=()=>act('claim_draw');
$('spectate').onclick=()=>window.open('/room/'+rid+'?watch=1','_blank','noopener');
window.addEventListener('popstate',()=>location.reload());
if(typeof Chess==='undefined'){$('status').textContent='Chess library failed to load. Check your internet or browser blocker, then refresh.';$('create').disabled=true;}
else{game=new Chess();drawBoard();if(rid)poll();else{$('status').textContent='Enter your private host code, choose an opponent and create a game.';api('/api/status').then(s=>{if(!s.engine_ready)$('notice').textContent='Stockfish is unavailable; friend games still work. Check Render logs.';}).catch(e=>$('notice').textContent=e.message);}
 setInterval(poll,750);setInterval(clocks,100);
}
