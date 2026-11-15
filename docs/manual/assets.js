const sharp=require('sharp');
const W=1600,H=900;
// 회로 패턴 워터마크 (오른쪽 아래)
let p=[];const rnd=(()=>{let s=7;return()=>{s=(s*16807)%2147483647;return s/2147483647}})();
for(let i=0;i<46;i++){let x=W-40-rnd()*700,y=H-30-rnd()*520;let d=`M${x.toFixed(0)} ${y.toFixed(0)}`;
 for(let k=0;k<3;k++){const h=rnd()<.5; const L=40+rnd()*160; if(h)x+= (rnd()<.5?-1:1)*L; else y+=(rnd()<.5?-1:1)*L; d+=` L${x.toFixed(0)} ${y.toFixed(0)}`;}
 p.push(`<path d="${d}" fill="none" stroke="#0B5CAD" stroke-width="2"/><circle cx="${x.toFixed(0)}" cy="${y.toFixed(0)}" r="5" fill="none" stroke="#0B5CAD" stroke-width="2"/>`);}
// 칩
const chip=`<g transform="translate(${W-330},${H-330})"><rect x="0" y="0" width="170" height="170" rx="14" fill="none" stroke="#0B5CAD" stroke-width="3"/><rect x="40" y="40" width="90" height="90" rx="6" fill="none" stroke="#0B5CAD" stroke-width="2"/>${[...Array(6)].map((_,i)=>`<line x1="${20+i*26}" y1="0" x2="${20+i*26}" y2="-26" stroke="#0B5CAD" stroke-width="3"/><line x1="${20+i*26}" y1="170" x2="${20+i*26}" y2="196" stroke="#0B5CAD" stroke-width="3"/><line x1="0" y1="${20+i*26}" x2="-26" y2="${20+i*26}" stroke="#0B5CAD" stroke-width="3"/><line x1="170" y1="${20+i*26}" x2="196" y2="${20+i*26}" stroke="#0B5CAD" stroke-width="3"/>`).join('')}</g>`;
const svg=`<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}"><g opacity="0.06">${p.join('')}${chip}</g></svg>`;
// 표지: 차량 실루엣 라인 + 회로
const car=`<g fill="none" stroke="#0B5CAD" stroke-width="5" stroke-linecap="round" stroke-linejoin="round">
<path d="M180 560 L240 470 Q290 400 380 390 L620 380 Q700 380 760 430 L860 500 L1040 520 Q1110 530 1120 580 L1120 620 L180 620 Z"/>
<path d="M300 470 L360 410 L560 404 L560 470 Z"/><path d="M590 404 L690 410 L780 470 L590 470 Z"/>
<circle cx="340" cy="625" r="62"/><circle cx="340" cy="625" r="28"/><circle cx="930" cy="625" r="62"/><circle cx="930" cy="625" r="28"/>
<path d="M1150 420 q60 60 0 120"/><path d="M1180 390 q90 90 0 180"/><path d="M1210 360 q120 120 0 240"/></g>`;
const cover=`<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}"><g opacity="0.07" transform="translate(180,40)">${car}</g><g opacity="0.05">${p.join('')}</g></svg>`;
(async()=>{await sharp(Buffer.from(svg)).png().toFile('img/wm.png');await sharp(Buffer.from(cover)).png().toFile('img/wm_cover.png');console.log('ok')})();
