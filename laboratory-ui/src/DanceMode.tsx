import {useCallback,useEffect,useRef,useState} from 'react';

/** Presentation-only fullscreen lifecycle around the already mounted instrument. */
export function useDanceMode(stage:{current:HTMLElement|null}){
 const [active,setActive]=useState(false),[hint,setHint]=useState('');
 const wanted=useRef(false),owned=useRef(false),focusBefore=useRef<HTMLElement|null>(null),focusFrame=useRef<number|null>(null);
 const restoreFocus=useCallback(()=>{
  if(focusFrame.current!==null)cancelAnimationFrame(focusFrame.current);
  focusFrame.current=requestAnimationFrame(()=>{focusFrame.current=null;focusBefore.current?.focus({preventScroll:true});});
 },[]);
 const exit=useCallback(async()=>{
  wanted.current=false;setActive(false);setHint('');
  if(stage.current&&document.fullscreenElement===stage.current&&document.exitFullscreen){
   try{await document.exitFullscreen();}
   catch{if(document.fullscreenElement===stage.current){wanted.current=true;setActive(true);setHint('Usá Esc para volver al set.');return;}}
  }
  owned.current=false;restoreFocus();
 },[stage,restoreFocus]);
 const enter=useCallback(async()=>{
  const element=stage.current;if(!element||wanted.current)return;
  wanted.current=true;focusBefore.current=document.activeElement as HTMLElement;setActive(true);setHint('');
  element.focus({preventScroll:true});
  if(!element.requestFullscreen||document.fullscreenElement&&document.fullscreenElement!==element){setHint('Modo baile en esta pestaña.');return;}
  try{await element.requestFullscreen();if(!wanted.current&&document.fullscreenElement===element)await document.exitFullscreen();}
  catch{if(wanted.current)setHint('Modo baile en esta pestaña.');}
 },[stage]);
 useEffect(()=>{
  const changed=()=>{
   if(stage.current&&document.fullscreenElement===stage.current){owned.current=true;if(!wanted.current)void document.exitFullscreen().catch(()=>{});}
   else if(owned.current){owned.current=false;wanted.current=false;setActive(false);setHint('');restoreFocus();}
  };
  const key=(event:KeyboardEvent)=>{
   if(event.key==='Escape'&&wanted.current){event.preventDefault();void exit();}
  };
  document.addEventListener('fullscreenchange',changed);document.addEventListener('keydown',key);
  return()=>{document.removeEventListener('fullscreenchange',changed);document.removeEventListener('keydown',key);if(focusFrame.current!==null)cancelAnimationFrame(focusFrame.current);};
 },[stage,exit,restoreFocus]);
 return {active,enter,exit,hint};
}

export function DanceControls({active,exit,hint,problem}:{active:boolean;exit:()=>Promise<void>;hint:string;problem?:string|null}){
 return <div className="dance-controls" hidden={!active}>
  <button className="dance-exit" aria-label="Salir del modo baile" onClick={()=>void exit()}>Volver al set <span>· Esc</span></button>
  {(problem||hint)&&<p className="dance-status" role="status">{problem||hint}</p>}
 </div>;
}
