import type {ExpressionReading,ExpressionFeature} from './expression';
import type {RegionalReading} from './regions';
const names:Record<ExpressionFeature,string>={browHeightL:'Altura ceja izq.',browHeightR:'Altura ceja der.',innerSlopeL:'Pendiente interna izq.',innerSlopeR:'Pendiente interna der.',cornerHeightL:'Altura comisura izq.',cornerHeightR:'Altura comisura der.',cornerLiftL:'Arco comisura izq.',cornerLiftR:'Arco comisura der.',eyeL:'Apertura ojo izq.',eyeR:'Apertura ojo der.',mouth:'Apertura boca'};
const number=(v:number|null|undefined)=>v==null||!Number.isFinite(v)?'—':(v>=0?'+':'')+v.toLocaleString('es',{minimumFractionDigits:3,maximumFractionDigits:3});
export function ExpressionPanel({reading,regional,enabled,recording,onChange}:{reading:ExpressionReading;regional?:RegionalReading;enabled:boolean;recording:boolean;onChange:(value:boolean)=>void}){
 return <section className="face-expression-panel" aria-label="Identificador de expresión">
  <p className="face-step">GESTO COMPUESTO · BOCA + OJOS + CEJAS</p>
  <label className="face-check"><input type="checkbox" checked={enabled} disabled={recording} onChange={e=>onChange(e.target.checked)}/>Mostrar lectura orientativa</label>
  {enabled&&!recording?<>
   <h2 className="face-expression-label" data-expression={reading.id}>{reading.label}</h2><p>{reading.detail}</p>
   {regional?.referenceReady&&<div className="face-region-list" aria-label="Lecturas independientes por zona">{regional.regions.map(r=><article key={r.id} data-face-region={r.id} className="face-region-card">
    <header><h3>{r.name}</h3><span>{r.coverage==='full'?'Con medidas':r.coverage==='partial'?'Parcial':'Sin lectura'}</span></header>
    <strong>{r.label}</strong>{r.pending&&<p className="face-region-pending">Esta zona está cambiando…</p>}{r.detail&&<p>{r.detail}</p>}
    {r.arcs.map(a=><div className="face-region-curve" key={a.label}><span>{a.label}</span><span>Arco {number(a.bend)}{a.bend==null?'':a.bend>=0?' · hacia referencia':' · hacia afuera'}</span><span>Δ {number(a.change)} · giro {number(a.turn)} rad</span></div>)}
    <details><summary>Medidas y puntos · {r.name}</summary><dl>{r.metrics.map(m=><div key={m.label}><dt>{m.label}</dt><dd>{number(m.value)}</dd></div>)}</dl><p className="face-small">Arcos: {r.arcs.map(a=>a.points.join(' · ')).join(' / ')}</p></details>
   </article>)}</div>}
   {regional?.referenceReady&&<p className="face-small">Arco = desvío respecto de su cuerda, dividido por su ancho. + hacia la referencia; − hacia afuera. El giro es la curvatura acumulada orientada. La forma aporta indicios; no decide una emoción por sí sola.</p>}
   {reading.evidence.length>0&&<details><summary>Ver puntos y medidas</summary><ul className="face-expression-evidence">{reading.evidence.map(e=><li key={e.description}><strong>{e.description}</strong><span>Puntos {e.points.join(' · ')}</span><span>{e.features.map(k=>`${names[k]}: ${number(regional?.delta?.[k]??reading.delta?.[k])}`).join(' / ')}</span></li>)}</ul><p className="face-small">Cambios respecto del reposo: alturas y pendientes en anchos entre ojos; aperturas en anchos de cada ojo o de la boca.</p></details>}
   <p className="face-small">Lectura experimental de la expresión visible. El sonido responde al mapeo elegido, sin usar el texto de esta etiqueta.</p>
  </>:<p>{recording?'Lectura oculta durante el ensayo.':'Lectura oculta. Respondé las preguntas antes de volver a mostrarla.'}</p>}
 </section>;
}
