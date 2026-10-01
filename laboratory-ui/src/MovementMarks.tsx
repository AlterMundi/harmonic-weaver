import {useState} from "react";
export function MovementMarks({api,run}:{api:(path:string,body:unknown)=>Promise<unknown>;run:(action:()=>Promise<void>)=>unknown}){
 const [mark,setMark]=useState("");
 const [markCategory,setMarkCategory]=useState("note");
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
 </>;
}
