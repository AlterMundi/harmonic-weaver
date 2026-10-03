export function portableCSVMapping(value:any){
 if(!value||typeof value!=='object'||Array.isArray(value))throw Error('Mapeo CSV debe ser un objeto');
 const copy={...value};if(copy.time_units==='iso8601')delete copy.time_origin;
 return copy;
}
export function CSVTimeControls({text,onChange,disabled,scope}:{text:string,onChange:(text:string)=>void,disabled:boolean,scope:string}){
 let mapping:any=null;try{mapping=JSON.parse(text);if(!mapping||Array.isArray(mapping)||typeof mapping!=='object')mapping=null}catch{}
 const edit=(fields:Record<string,unknown>)=>{const next={...mapping,...fields};if(next.time_units!=='iso8601'){delete next.schema_version;delete next.time_origin}onChange(JSON.stringify(next,null,2))};
 return <fieldset><legend>Tiempo CSV {scope}</legend>
 <label>Formato temporal CSV {scope}<select disabled={disabled||!mapping} value={mapping?.time_units||'seconds'} onChange={e=>edit(e.target.value==='iso8601'?{schema_version:2,time_units:'iso8601',time_origin:mapping?.time_origin||''}:{time_units:e.target.value})}><option value="seconds">Segundos numéricos</option><option value="milliseconds">Milisegundos numéricos</option><option value="microseconds">Microsegundos numéricos</option><option value="iso8601">ISO 8601 con zona horaria</option></select></label>
 {mapping?.time_units==='iso8601'&&<><label>Origen ISO CSV {scope}<input disabled={disabled} value={mapping.time_origin||''} placeholder="2026-10-03T12:00:00Z" onChange={e=>edit({time_origin:e.target.value})}/></label><p>Zona Z u offset obligatorio en cada timestamp y origen. Hasta seis decimales; no asume zona local ni detecta fechas automáticamente. Primero resta este origen; después aplica offset/rate del reloj declarado a esos segundos relativos. Revisar ese reloj para no restar el origen dos veces. No demuestra sincronización física.</p></>}
 {!mapping&&<p>Corregir el JSON del mapeo para usar estos controles.</p>}
 </fieldset>;
}
