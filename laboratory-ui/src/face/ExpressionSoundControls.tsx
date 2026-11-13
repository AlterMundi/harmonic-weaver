import {DEFAULT_EXPRESSION_SOUND,expressionAxis,validExpressionSound,type ExpressionSoundSettings} from './expressionSound';
import type {MappingSettings} from './contourSound';
import type {RegionalReading,RegionalReference} from './regions';

export function ExpressionSoundControls({mapping,reading,reference,sensitivity,f0,recording,showDrive,onChange}:{mapping:MappingSettings;reading:RegionalReading;reference?:RegionalReference;sensitivity:number;f0:number;recording:boolean;showDrive:boolean;onChange:(value:MappingSettings)=>void}){
 const s=mapping.expression??DEFAULT_EXPRESSION_SOUND,axis=expressionAxis(reading.delta,reference,s,sensitivity);
 const update=(patch:Partial<ExpressionSoundSettings>)=>{const next={...s,...patch};if(validExpressionSound(next))onChange({...mapping,expression:next});};
 const hint=(v:number|null|undefined)=>v==null?'Sin medida':Math.round(v*100)+'%';
 return <div className="face-expression-sound" aria-label="Configuración del eje expresivo">
  <p>La voz se mueve según los indicios de sonrisa y frunce. Es una elección musical: no demuestra qué emoción sentís.</p>
  <div className="face-harmonic-targets">
   <label>Alegría · destino H<input aria-label="Armónico de alegría" type="number" min="1" max="16" step="1" value={s.joyH} disabled={recording} onChange={e=>update({joyH:Number(e.target.value)})}/><span>{(f0*s.joyH).toLocaleString('es',{maximumFractionDigits:1})} Hz</span></label>
   <label>Enojo · destino H<input aria-label="Armónico de enojo" type="number" min="1" max="16" step="1" value={s.angerH} disabled={recording} onChange={e=>update({angerH:Number(e.target.value)})}/><span>{(f0*s.angerH).toLocaleString('es',{maximumFractionDigits:1})} Hz</span></label>
  </div>
  <label>Movimiento de la voz<select aria-label="Movimiento del eje expresivo" value={s.motion} disabled={recording} onChange={e=>update({motion:e.target.value as ExpressionSoundSettings['motion']})}><option value="continuous">Deslizar entre armónicos</option><option value="steps">Elegir armónicos exactos</option></select></label>
  <label>Respuesta expresiva · {Math.round(s.depth*100)}%<input aria-label="Respuesta expresiva" type="range" min="0" max="1" step=".05" value={s.depth} disabled={recording} onChange={e=>update({depth:Number(e.target.value)})}/></label>
  <p className="face-small">f₀ sigue fijo. H1 = f₀; H11 = 11 × f₀. Sin indicios, la posición es la media de los destinos; los gestos mixtos se combinan. Tristeza y sorpresa no tienen un destino propio en este eje. Al deslizar, las posiciones intermedias pueden ser fraccionarias.</p>
  {showDrive?<div className="face-drive" aria-label="Respuesta del eje expresivo"><span>Indicio de sonrisa <strong>{hint(axis?.joy)}</strong></span><span>Indicio de frunce <strong>{hint(axis?.anger)}</strong></span><span>Posición objetivo <strong data-expression-ratio={axis?.ratio}>{axis?axis.ratio.toLocaleString('es',{maximumFractionDigits:2})+' × f₀':'—'}</strong></span><span>Voz móvil <strong>{axis?(f0*axis.ratio).toLocaleString('es',{maximumFractionDigits:1})+' Hz':'—'}</strong></span></div>:<p className="face-small">Indicadores ocultos. El sonido sigue el mapeo elegido; escucharlo también puede orientar tu respuesta.</p>}
  <p className="face-small">Los porcentajes son escalas de control, no probabilidades. La referencia f₀ queda suave bajo la voz móvil; cerca de H1, esa voz se desvanece para dejar sólo la raíz.</p>
 </div>;
}
