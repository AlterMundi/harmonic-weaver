export function portableCSVMapping(value:any){
 if(!value||typeof value!=='object'||Array.isArray(value))throw Error('Mapeo CSV debe ser un objeto');
 const copy={...value};if(copy.time_units==='iso8601')delete copy.time_origin;
 return copy;
}
export function CSVTimeControls({text,onChange,disabled,scope}:{text:string,onChange:(text:string)=>void,disabled:boolean,scope:string}){
 let mapping:any=null;try{mapping=JSON.parse(text);if(!mapping||Array.isArray(mapping)||typeof mapping!=='object')mapping=null}catch{}
 const edit=(fields:Record<string,unknown>)=>{const next={...mapping,...fields};if(next.index_mode==='row_ordinal'){next.schema_version=3;next.index_column=null}else{delete next.index_mode;if(next.time_units==='iso8601')next.schema_version=2;else delete next.schema_version}if(next.time_units!=='iso8601')delete next.time_origin;onChange(JSON.stringify(next,null,2))};
 return <fieldset><legend>Tiempo CSV {scope}</legend>
 <label>Índice CSV {scope}<select disabled={disabled||!mapping} value={mapping?.index_mode==='row_ordinal'?'row_ordinal':'column'} onChange={e=>edit(e.target.value==='row_ordinal'?{index_mode:'row_ordinal',index_column:null}:{index_mode:undefined,index_column:'index'})}><option value="column">Columna del archivo</option><option value="row_ordinal">Numerar filas desde cero</option></select></label>
 {mapping?.index_mode==='row_ordinal'?<p>Índices generados por fila, sin descartar registros. No son contadores del dispositivo: no detectan muestras perdidas. Timestamps, gaps temporales y faltantes siguen viniendo del archivo; no genera tiempos ni rellena datos.</p>:<label>Columna de índice CSV {scope}<input disabled={disabled||!mapping} value={mapping?.index_column||''} onChange={e=>edit({index_column:e.target.value})}/></label>}
 <label>Formato temporal CSV {scope}<select disabled={disabled||!mapping} value={mapping?.time_units||'seconds'} onChange={e=>edit(e.target.value==='iso8601'?{schema_version:2,time_units:'iso8601',time_origin:mapping?.time_origin||''}:{time_units:e.target.value})}><option value="seconds">Segundos numéricos</option><option value="milliseconds">Milisegundos numéricos</option><option value="microseconds">Microsegundos numéricos</option><option value="iso8601">ISO 8601 con zona horaria</option></select></label>
 {mapping?.time_units==='iso8601'&&<><label>Origen ISO CSV {scope}<input disabled={disabled} value={mapping.time_origin||''} placeholder="2026-10-03T12:00:00Z" onChange={e=>edit({time_origin:e.target.value})}/></label><p>Zona Z u offset obligatorio en cada timestamp y origen. Hasta seis decimales; no asume zona local ni detecta fechas automáticamente. Primero resta este origen; después aplica offset/rate del reloj declarado a esos segundos relativos. Revisar ese reloj para no restar el origen dos veces. No demuestra sincronización física.</p></>}
 {!mapping&&<p>Corregir el JSON del mapeo para usar estos controles.</p>}
 </fieldset>;
}
