import {useEffect,useRef} from 'react';
import type {ReactNode} from 'react';
import './SourcesDialog.css';

/** Source configuration stays accessible above the stage, in either workbench view. */
export function SourcesDialog({open,onClose,children}:{open:boolean;onClose:()=>void;children:ReactNode}){
 const dialog=useRef<HTMLDialogElement>(null),previousFocus=useRef<HTMLElement|null>(null);
 useEffect(()=>{
  if(open){previousFocus.current=document.activeElement as HTMLElement;if(!dialog.current?.open)dialog.current?.showModal();}
  else if(dialog.current?.open){dialog.current.close();previousFocus.current?.focus();}
 },[open]);
 return <dialog ref={dialog} className="sources-dialog" aria-labelledby="sources-title" onCancel={event=>{event.preventDefault();onClose();}}>
  <div className="sources-heading"><h2 id="sources-title">Fuentes</h2><button aria-label="Cerrar fuentes" onClick={onClose}>Volver al instrumento</button></div>
  {open&&children}
 </dialog>;
}
