import type {ExpressionReading,ExpressionFeature} from './expression';

const names:Record<ExpressionFeature,string>={browHeightL:'Altura ceja izq.',browHeightR:'Altura ceja der.',innerSlopeL:'Pendiente interna izq.',innerSlopeR:'Pendiente interna der.',cornerHeightL:'Altura comisura izq.',cornerHeightR:'Altura comisura der.',cornerLiftL:'Arco comisura izq.',cornerLiftR:'Arco comisura der.',eyeL:'Apertura ojo izq.',eyeR:'Apertura ojo der.',mouth:'Apertura boca'};
export function ExpressionPanel({reading,enabled,recording,onChange}:{reading:ExpressionReading;enabled:boolean;recording:boolean;onChange:(value:boolean)=>void}){
 return <section className="face-expression-panel" aria-label="Identificador de expresión">
  <p className="face-step">QUÉ PUEDE TRANSMITIR TU GESTO</p>
  <label className="face-check"><input type="checkbox" checked={enabled} disabled={recording} onChange={e=>onChange(e.target.checked)}/>Mostrar lectura orientativa</label>
  {enabled&&!recording?<>
   <h2 className="face-expression-label" data-expression={reading.id}>{reading.label}</h2>
   <p>{reading.detail}</p>
   {reading.evidence.length>0&&<details><summary>Ver puntos y medidas</summary><ul className="face-expression-evidence">{reading.evidence.map(e=><li key={e.description}><strong>{e.description}</strong><span>Puntos {e.points.join(' · ')}</span><span>{e.features.map(k=>`${names[k]}: ${reading.delta![k]>=0?'+':''}${reading.delta![k].toFixed(3)}`).join(' / ')}</span></li>)}</ul><p className="face-small">Diferencias respecto del reposo: alturas y pendientes en anchos entre ojos; aperturas en anchos de cada ojo o de la boca.</p></details>}
   <p className="face-small">Lectura experimental de la expresión visible. El sonido sigue los contornos, sin usar esta etiqueta.</p>
  </>:<p>{recording?'Lectura oculta durante el ensayo.':'Lectura oculta. Respondé las preguntas antes de volver a mostrarla.'}</p>}
 </section>;
}
