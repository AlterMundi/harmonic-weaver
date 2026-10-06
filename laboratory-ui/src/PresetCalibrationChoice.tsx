import {useEffect, useRef} from 'react';
type Data = Record<string,any>;

export function PresetCalibrationChoice({preset,current,sameCapture,choose,cancel}:{
  preset:Data;current:Data|null;sameCapture:boolean;
  choose:(policy:'saved'|'current')=>void;cancel:()=>void;
}) {
  const dialog=useRef<HTMLDialogElement>(null);
  useEffect(()=>{const el=dialog.current!;el.showModal();return()=>el.close();},[]);
  return <dialog ref={dialog} className="preset-calibration-choice" aria-labelledby="preset-calibration-title" onCancel={cancel}>
    <h2 id="preset-calibration-title">Calibración de «{preset.name}»</h2>
    <p>{sameCapture ? 'La guardada corresponde a esta captura y persona.' : 'La guardada corresponde a otra fuente, persona o generación de tracking.'}</p>
    <p>Escala guardada: <strong>{preset.calibration.torso_scale.toFixed(6)}</strong>.
      {' '}Actual: <strong>{current ? current.torso_scale.toFixed(6) : 'sin calibración'}</strong>.</p>
    <div className="actions">
      <button onClick={()=>choose('saved')}>Traer la calibración guardada</button>
      <button onClick={()=>choose('current')}>{current ? 'Conservar la calibración actual' : 'Aplicar sin calibración'}</button>
      <button onClick={cancel}>Cancelar</button>
    </div>
  </dialog>;
}
