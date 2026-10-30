import {useEffect, useRef, useState} from "react";
type Data = Record<string, any>;

export function OutputLevel({draft, state, change}: {draft:Data;state:Data;change:(key:string,value:any)=>void}) {
  const gain = Number(draft.output_gain ?? 1), lastLevel = useRef(gain || 1);
  const [notice, setNotice] = useState("");
  useEffect(()=>{if(gain>0)lastLevel.current=gain;},[gain]);
  const settings={enabled:false,mode:"scale",closed_ratio:1,open_ratio:3,smoothing_s:.15,...draft.body_volume};
  const body=state.runtime?.body_volume || {}, ratio=body.state==='observed' ? body.ratio : null;
  const update=(values:Data)=>{setNotice("");change('body_volume',{...settings,...values});};
  const capture=(open:boolean)=>{
    if(typeof ratio!=='number')return;
    if(ratio>10){setNotice("Revisá el encuadre del torso antes de guardar una postura.");return;}
    if(open ? ratio<=settings.closed_ratio : ratio>=settings.open_ratio){
      setNotice(open ? "Separá más las manos que en la postura cerrada." : "La postura cerrada debe tener menos separación que la abierta.");return;
    }
    update(open ? {open_ratio:ratio} : {closed_ratio:ratio});
  };
  return <section className="output-level" aria-label="Volumen del instrumento" tabIndex={0}>
    <div className="output-level-main">
      <label><span>Volumen · ×{gain.toFixed(2)}</span>
        <input aria-label="Nivel de escucha" type="range" min="0" max="4" step=".05" value={gain}
          onChange={e=>change('output_gain',Number(e.target.value))}/></label>
      <button aria-label={gain>0 ? "Silenciar instrumento" : "Reactivar sonido"} onClick={()=>change('output_gain',gain>0 ? 0 : lastLevel.current)}>{gain>0 ? "Silenciar" : "Reactivar"}</button>

    </div>
    <details className="body-volume-settings"><summary>Apertura de brazos y respuesta</summary>
            <label className="check"><input aria-label="Controlar volumen con apertura" type="checkbox" checked={settings.enabled}
        onChange={e=>update({enabled:e.target.checked})}/>Controlar volumen con apertura</label>
      <p>×1 conserva el nivel de escucha de referencia.</p>
      <div className="fields">
        <label>Cómo responde<select aria-label="Respuesta a la apertura" value={settings.mode}
          onChange={e=>update({mode:e.target.value})}>
          <option value="scale">Ajusta el sonido del movimiento</option><option value="pose">Sostiene sonido al abrir</option>
        </select></label>
        <label>Apertura observada · {body.state==='observed' ? `${Math.round((body.level || 0)*100)}%` : "sin puntos suficientes"}
          <meter aria-label="Apertura corporal observada" min={0} max={1} value={body.state==='observed' ? body.level || 0 : 0}/></label>
      </div>
      <div className="actions"><button disabled={typeof ratio!=='number'} onClick={()=>capture(false)}>Guardar postura cerrada</button>
        <button disabled={typeof ratio!=='number'} onClick={()=>capture(true)}>Guardar postura abierta</button></div>
      <p>De frente a la cámara, juntá las manos y guardá la postura cerrada; después abrí los brazos y guardá la abierta.
        Medimos separación visible de muñecas respecto del torso. Si faltan muñecas, hombros o caderas, esta respuesta se silencia.</p>
      <p>{settings.mode==='pose' ? "En modo postura, la apertura aporta el sonido sostenido de las voces disponibles, respetando Solo y Silenciar."
        : "La apertura ajusta el nivel del sonido que produce el movimiento; una postura quieta puede quedar en silencio."}</p>
      {notice && <p role="alert">{notice}</p>}
    </details>
  </section>;
}
