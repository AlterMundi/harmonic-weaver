type Data = Record<string, any>;

export function CalibrationReuse({calibrations,sourceId,personId,pending,reuse,matchingOnly=false}:{
 calibrations:Data[];sourceId?:string;personId?:string;pending:boolean;
 reuse:(id:string)=>void;matchingOnly?:boolean;
}) {
 const matching=calibrations.filter(c=>c.source_id===sourceId && c.person_id===personId);
 const other=calibrations.filter(c=>c.source_id!==sourceId || c.person_id!==personId);
 const options=(items:Data[])=>items.map(c=><option key={c.id} value={c.id}>
  {c.measured_at} · fuente {c.source_id.slice(0,8)} · {c.person_id} · escala {c.torso_scale.toFixed(4)}{c.policy==='reuse_explicit'?' · reutilizada':''}
 </option>);
 if(matchingOnly && !matching.length)return null;
 return <details>
  <summary>{matchingOnly?'Recuperar escala guardada de esta fuente y persona':'Reutilizar calibración explícitamente'}</summary>
  <label>{matchingOnly?'Calibración de esta fuente y persona':'Calibración guardada'}
   <select aria-label={matchingOnly?'Calibración de esta fuente y persona':'Calibración guardada'}
    value="" disabled={pending || !sourceId || !personId} onChange={e=>e.target.value && reuse(e.target.value)}>
    <option value="">Seleccionar…</option>
    {matching.length>0 && <optgroup label="Esta fuente y persona">{options(matching)}</optgroup>}
    {!matchingOnly && other.length>0 && <optgroup label="Otra fuente o persona · reutilización explícita">{options(other)}</optgroup>}
   </select>
  </label>
 </details>;
}
