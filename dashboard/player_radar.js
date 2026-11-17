const PLAYER_METRICS=[
  {key:'acs',label:'ACS',hint:'Điểm chiến đấu / round',digits:0},
  {key:'adr',label:'ADR',hint:'Sát thương / round',digits:0},
  {key:'kd',label:'K/D',hint:'Kills / deaths',digits:2},
  {key:'assists_pr',label:'Hỗ trợ',hint:'Assists / round',digits:2},
  {key:'first_kills_pr',label:'Mở giao tranh',hint:'First kills / round',digits:2},
  {key:'kast',label:'KAST',hint:'Kill / Assist / Survive / Trade',digits:1,percent:true}
];
let playerSeason=2026,playerId=null;
const playerNumber=(value,digits=1)=>Number(value).toLocaleString('vi-VN',{minimumFractionDigits:digits,maximumFractionDigits:digits});
function valueText(profile,metric){return metric.percent?playerNumber(profile[metric.key]*100,metric.digits)+'%':playerNumber(profile[metric.key],metric.digits)}
function radarSvg(profile){
  const cx=205,cy=160,r=105,angles=PLAYER_METRICS.map((_,i)=>-Math.PI/2+i*Math.PI/3);
  const point=(i,scale)=>[cx+Math.cos(angles[i])*r*scale,cy+Math.sin(angles[i])*r*scale];
  const polygon=scale=>angles.map((_,i)=>point(i,scale).map(v=>v.toFixed(1)).join(',')).join(' ');
  const rings=[.2,.4,.6,.8,1].map(v=>`<polygon class="radar-ring" points="${polygon(v)}"/>`).join('');
  const axes=angles.map((_,i)=>{const [x,y]=point(i,1);return `<line class="radar-axis" x1="${cx}" y1="${cy}" x2="${x.toFixed(1)}" y2="${y.toFixed(1)}"/>`}).join('');
  const labels=PLAYER_METRICS.map((metric,i)=>{let [x,y]=point(i,1.30);let anchor=x<cx-12?'end':x>cx+12?'start':'middle';return `<text class="radar-label" x="${x.toFixed(1)}" y="${(y+4).toFixed(1)}" text-anchor="${anchor}">${metric.label}</text>`}).join('');
  const values=PLAYER_METRICS.map((metric,i)=>point(i,profile['pct_'+metric.key])).map(([x,y])=>`${x.toFixed(1)},${y.toFixed(1)}`).join(' ');
  const dots=PLAYER_METRICS.map((metric,i)=>{const [x,y]=point(i,profile['pct_'+metric.key]);return `<circle class="radar-dot" cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="3.5"/>`}).join('');
  return `<svg class="radar-svg" viewBox="0 0 410 325" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">${rings}${axes}<polygon class="radar-shape" points="${values}"/>${dots}${labels}<text class="radar-scale" x="${cx}" y="${cy-110}" text-anchor="middle">100</text></svg>`;
}
function currentProfiles(){return DATA.players.filter(p=>p.season===playerSeason)}
function renderPlayer(){
  const profile=currentProfiles().find(p=>p.player_id===playerId);
  if(!profile){$('#playerName').textContent='Không có tuyển thủ';$('#radarChart').innerHTML='';$('#playerRaw').innerHTML='';$('#playerMetrics').innerHTML='';return}
  $('#playerName').textContent=profile.player_name;
  $('#radarChart').innerHTML=radarSvg(profile);
  $('#radarChart').setAttribute('aria-label',`Biểu đồ phân vị của ${profile.player_name}, mùa ${profile.season}`);
  $('#playerRaw').innerHTML=PLAYER_METRICS.map(metric=>`<span><b>${valueText(profile,metric)}</b>${metric.label}</span>`).join('');
  $('#playerMetrics').innerHTML=PLAYER_METRICS.map(metric=>{let rank=profile['pct_'+metric.key];return `<div class="player-metric"><div class="player-metric-name"><b>${metric.label}</b><small>${metric.hint}</small></div><div class="player-metric-bar"><i style="width:${Math.round(rank*100)}%"></i></div><div class="player-metric-value"><b>${valueText(profile,metric)}</b><small>Phân vị ${Math.round(rank*100)}</small></div></div>`}).join('');
}
function renderPlayerList(){
  const query=$('#playerSearch').value.trim().toLocaleLowerCase('vi-VN');
  let profiles=currentProfiles().filter(p=>p.player_name.toLocaleLowerCase('vi-VN').includes(query));
  profiles.sort((a,b)=>b.games-a.games||a.player_name.localeCompare(b.player_name));
  if(!profiles.some(p=>p.player_id===playerId))playerId=profiles[0]?.player_id??null;
  $('#playerSelect').innerHTML=profiles.length?profiles.map(p=>`<option value="${p.player_id}" ${p.player_id===playerId?'selected':''}>${esc(p.player_name)}</option>`).join(''):'<option value="">Không có tuyển thủ</option>';
  renderPlayer();
}
function resetPlayerList(){
  playerId=null;$('#playerSearch').value='';renderPlayerList();
}
if(DATA.players?.length){
  const seasons=[...new Set(DATA.players.map(p=>p.season))].sort((a,b)=>b-a);
  playerSeason=seasons[0];$('#playerSeason').innerHTML=seasons.map(y=>`<option value="${y}">${y}</option>`).join('');
  $('#playerSeason').addEventListener('change',e=>{playerSeason=Number(e.target.value);resetPlayerList()});
  $('#playerSearch').addEventListener('input',renderPlayerList);
  $('#playerSelect').addEventListener('change',e=>{playerId=Number(e.target.value);renderPlayer()});
  resetPlayerList();
}
