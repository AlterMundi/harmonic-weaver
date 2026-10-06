type Data = Record<string, any>;
export function PerformanceControls({draft,presets,pending,change,applyPreset,applyMacro,save,exportPreset,name,setName,personId,personIds,selectionStatus,canConfirmPerson,choosePerson,mark,askCalibration=false,setAskCalibration}:{
 draft:Data;presets:Data[];pending:boolean;change:(key:string,value:any)=>void;
 applyPreset:(preset:Data)=>void;applyMacro:(id:string,value:number)=>unknown;
 askCalibration?:boolean;setAskCalibration?:(value:boolean)=>void;
 save:()=>void;exportPreset:()=>void;name:string;setName:(name:string)=>void;
 personId?:string;personIds:string[];selectionStatus?:string;canConfirmPerson?:boolean;choosePerson:(id:string)=>void;mark:()=>void;
}) {
 return <section aria-label="Controles de performance">
  <h2>Jugar con el movimiento</h2>
  <div className="fields performance-sliders">
   <label>Intensidad general · {draft.master.toFixed(2)}
    <input aria-label="Intensidad general" type="range" min="0" max="1" step=".01" value={draft.master}
     onChange={e=>change('master',Number(e.target.value))}/>
   </label>
   <label>Realce expresivo · {(draft.expression ?? 0).toFixed(2)}
    <input aria-label="Realce expresivo" type="range" min="-1" max="10" step=".01" value={draft.expression ?? 0}
     onChange={e=>change('expression',Number(e.target.value))}/>
    <small>− Selectivo · 0 Neutral · 10 Máximo contraste temporal</small>
   </label>
   <label>Articulación · {Math.round((draft.transient_mix ?? 0)*100)}% transientes
    <input aria-label="Articulación" type="range" min="0" max="1" step=".01" value={draft.transient_mix ?? 0}
     onChange={e=>change('transient_mix',Number(e.target.value))}/>
    <small>0 Sostenido · 100% Impulsos de subida</small>
   </label>
   {draft.macros.map((m:Data)=><label key={m.id}>{m.label}
    <input aria-label={m.label} type="range" min="0" max="1" step=".01" value={m.value} disabled={pending}
     onChange={e=>applyMacro(m.id,Number(e.target.value))}/>
   </label>)}
  </div>
  <div className="performance-voices" aria-label="Voces">
   {draft.voices.map((voice:Data)=><fieldset key={voice.id}><legend>{voice.label}</legend>
    {['muted','solo'].map(key=><label className="check" key={key}>
     <input type="checkbox" aria-label={`${key==='muted'?'Silenciar':'Solo'} ${voice.label}`} checked={!!voice[key]}
      onChange={e=>change('voices',draft.voices.map((v:Data)=>v.id===voice.id?{...v,[key]:e.target.checked}:v))}/>
     {key==='muted'?'Silenciar':'Solo'}
    </label>)}
   </fieldset>)}
  </div>
  <label>Persona en performance<select value={personId || ''} onChange={e=>choosePerson(e.target.value)}>
   <option value="" disabled>Elegir cuerpo…</option>{personIds.map(id=><option key={id}>{id}</option>)}
  </select></label>
  {canConfirmPerson && ['automatic','automatic_changed'].includes(selectionStatus || '') && <button disabled={pending || !personId}
    onClick={()=>personId && choosePerson(personId)}>Fijar esta persona</button>}
  <h3>Configuraciones guardadas</h3>
  {setAskCalibration && <label className="check"><input type="checkbox" checked={askCalibration}
    onChange={e=>setAskCalibration(e.target.checked)}/>Preguntar siempre por la calibración</label>}
  <div className="preset-list">{presets.map(p=><button key={p.id} disabled={pending} onClick={()=>applyPreset(p)}>{p.name}</button>)}</div>
  <label>Nombre para guardar<input value={name} onChange={e=>setName(e.target.value)} placeholder={draft.name}/></label>
  <div className="actions">
   <button disabled={pending} onClick={save}>Guardar configuración actual</button>
   <button onClick={exportPreset}>Exportar JSON</button>
   <button disabled={!personId} onClick={mark}>Marcar «se siente bien»</button>
  </div>
  <p className="muted">Guardar incluye la calibración activa; un nombre existente pide confirmar sobrescritura. La marca registra tu sensación al presionar; no mide intención ni corrige el tiempo de reacción.</p>
 </section>;
}
