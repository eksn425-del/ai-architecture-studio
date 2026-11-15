import React from 'react';
import {AbsoluteFill,Audio,Img,OffthreadVideo,Sequence,Easing,interpolate,staticFile,useCurrentFrame} from 'remotion';
import cfg from '../public/job-config.json';
const C={dark:'#091c17',green:'#173f34',paper:'#f3f2eb',mint:'#caf5a4',gold:'#cda46d'};
const ease=Easing.bezier(.16,1,.3,1);
const r=(f:number,a:number,b:number,x=0,y=1)=>interpolate(f,[a,b],[x,y],{easing:ease,extrapolateLeft:'clamp',extrapolateRight:'clamp'});
const P=({src,style={}}:any)=><Img src={staticFile(src)} style={{width:'100%',height:'100%',objectFit:'cover',...style}}/>;
const V=({src,start=0,rate=1,style={}}:any)=>{const c=(cfg.clips as any)[`${src}:${start}`]||{start,rate};return <OffthreadVideo src={staticFile(src)} startFrom={Math.round(c.start*30)} playbackRate={c.rate} muted style={{width:'100%',height:'100%',objectFit:'cover',...style}}/>;};

function Field(){const f=useCurrentFrame();return <AbsoluteFill style={{overflow:'hidden'}}><AbsoluteFill style={{backgroundImage:'linear-gradient(#88b5980b 1px,transparent 1px),linear-gradient(90deg,#88b5980b 1px,transparent 1px)',backgroundSize:'90px 90px'}}/>{Array.from({length:42},(_,i)=><i key={i} style={{position:'absolute',left:(i*137.129+f*.12)%1920,top:(i*83.91-f*.3+2160)%1080,width:i%3+1,height:i%3+1,background:C.mint,opacity:.15+(i%3)*.08,borderRadius:'100%'}}/>)}<div style={{position:'absolute',left:(f*5)%3700-1300,top:-600,width:500,height:2400,transform:'rotate(32deg)',background:'linear-gradient(90deg,transparent,#a0daaf10,transparent)',filter:'blur(35px)'}}/></AbsoluteFill>}
function Brand({label='',dark=false}:any){return <div style={{position:'absolute',left:65,right:65,top:34,display:'flex',justifyContent:'space-between',alignItems:'center',color:dark?C.green:C.paper,fontSize:36,letterSpacing:2}}><b style={{fontFamily:'Georgia,serif',fontSize:36}}>K <span style={{fontSize:24,fontWeight:400}}>STUDIO</span></b><span>{label}</span></div>}
function Chip({children,dark=false}:any){return <span style={{display:'inline-block',padding:'10px 18px',background:dark?'#173f34f2':'#f3f2ebf2',color:dark?C.paper:C.green,fontSize:36,letterSpacing:1,borderRadius:4}}>{children}</span>}
function Words({text,size=106,color=C.paper,delay=0}:any){const f=useCurrentFrame();return <div style={{fontSize:size,color,fontWeight:750,letterSpacing:-3,lineHeight:1.18}}>{text.split('|').map((w:string,i:number)=><div key={i} style={{overflow:'hidden'}}><div style={{transform:`translateY(${r(f,delay+i*5,delay+i*5+18,115,0)}%)`,opacity:r(f,delay+i*5,delay+i*5+10)}}>{w}</div></div>)}</div>}

export {C,r,P,V,Field,Brand,Chip,Words};
