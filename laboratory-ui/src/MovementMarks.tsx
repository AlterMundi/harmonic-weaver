import {useState} from "react";
export function MovementMarks({api,run,sourceId,personId,currentSessionId,observedEpoch}:{currentSessionId?:string;observedEpoch?:number|null;sourceId?:string;personId?:string;api:(path:string,body:unknown)=>Promise<unknown>;run:(action:()=>Promise<void>)=>unknown}){
 const [mark,setMark]=useState("");
 const [markCategory,setMarkCategory]=useState("note");
 const [start,setStart]=useState("");const [end,setEnd]=useState("");
 const [filterCategory,setFilterCategory]=useState("");
 const [sessionFilter,setSessionFilter]=useState("");const [epochFilter,setEpochFilter]=useState("");
 const validEpoch=epochFilter==="" || !!sessionFilter && Number.isInteger(+epochFilter) && +epochFilter>=0;
 const valid=validEpoch && (start==="" || Number.isFinite(+start) && +start>=0) && (end==="" || Number.isFinite(+end) && +end>=0) && (start==="" || end==="" || +start<+end);
 const query=new URLSearchParams({source_id:sourceId || "",person_id:personId || ""});
 if(sessionFilter)query.set("session_id",sessionFilter);if(epochFilter!=="")query.set("observed_epoch",epochFilter);
 if(start!=="")query.set("start_s",start);if(end!=="")query.set("end_s",end);if(filterCategory)query.set("category",filterCategory);
 return <>
          <label>Tipo de marca<select value={markCategory} onChange={e=>setMarkCategory(e.target.value)}>
            <option value="note">Nota libre</option><option value="preparation">Preparación percibida</option>
            <option value="deployment">Despliegue percibido</option><option value="release">Liberación percibida</option>
            <option value="experience">Experiencia / sensación</option>
          </select></label>
          <small>Marca al presionar: no corrige tu tiempo de reacción ni confirma intención o causalidad.</small>
          <label>
            Marcar un momento
            <input
              value={mark}
              onChange={(e) => setMark(e.target.value)}
              placeholder="Esto se sintió bien…"
            />
          </label>
          <button
            disabled={!mark}
            onClick={() =>
              run(async () => {
                await api("marks", { text: mark, category: markCategory });
                setMark("");
              })
            }
          >
            Guardar marca
          </button>
 <a href="/api/marks/snapshot" download>Descargar marcas congeladas</a>
 <button disabled={!currentSessionId || observedEpoch==null || observedEpoch<0} onClick={()=>{setSessionFilter(currentSessionId!);setEpochFilter(String(observedEpoch));}}>Usar sesión y época observadas actuales</button>
 <label>Sesión de las marcas (opcional)<input value={sessionFilter} onChange={e=>setSessionFilter(e.target.value)}/></label>
 <label>Época observada (requiere sesión)<input type="number" min="0" step="1" value={epochFilter} onChange={e=>setEpochFilter(e.target.value)}/></label>
 <label>Inicio de selección de marcas (s)<input type="number" min="0" step=".01" value={start} onChange={e=>setStart(e.target.value)}/></label>
 <label>Fin de selección de marcas (s, excluido)<input type="number" min="0" step=".01" value={end} onChange={e=>setEnd(e.target.value)}/></label>
 <label>Categoría de descarga<select value={filterCategory} onChange={e=>setFilterCategory(e.target.value)}><option value="">Todas</option><option value="note">Nota libre</option><option value="preparation">Preparación</option><option value="deployment">Despliegue</option><option value="release">Liberación</option><option value="experience">Experiencia</option></select></label>
 {!valid && <p role="alert">Usá tiempos válidos; una época requiere sesión explícita.</p>}
 {sourceId && personId && valid && <a href={'/api/marks/snapshot?'+query} download>Descargar marcas de esta fuente y persona</a>}
 </>;
}
