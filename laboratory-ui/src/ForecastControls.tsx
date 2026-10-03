import {useEffect,useState} from 'react';
type Data=Record<string,any>;
export const predictorLabels:Record<string,string>={persistence:'Persistencia',full_ridge:'Ridge completo',subspace_ridge:'Ridge subespacio',linear_trend:'Tendencia lineal',lagged_full_ridge:'Ridge completo con retardos',lagged_subspace_ridge:'Ridge subespacio con retardos',fixed_harmonics:'Armónicos declarados'};
export const defaultPredictors=['persistence','full_ridge','subspace_ridge'];
export function ForecastControls({settings,onChange,scope}:Data){
 const chosen=settings.predictors||defaultPredictors;
 const ratiosJSON=JSON.stringify(settings.harmonic_ratios||[1,2,3,4,5,6]);
 const [ratiosText,setRatiosText]=useState<string>((settings.harmonic_ratios||[1,2,3,4,5,6]).join(', '));
 useEffect(()=>setRatiosText(JSON.parse(ratiosJSON).join(', ')),[ratiosJSON]);
 return <fieldset><legend>Predictores {scope}</legend>
  {Object.entries(predictorLabels).map(([key,label])=><label key={key}><input type="checkbox" aria-label={`${label} ${scope}`} checked={chosen.includes(key)} onChange={e=>onChange({...settings,predictors:e.target.checked?[...chosen,key]:chosen.filter((k:string)=>k!==key)})}/>{label}</label>)}
  <label>Retardos autorregresivos {scope}<input type="number" min={1} max={12} step={1} value={settings.autoregressive_lags??3} onChange={e=>onChange({...settings,autoregressive_lags:+e.target.value})}/></label>
  <label>Fundamental de predicción (Hz) {scope}<input type="number" min={.001} max={20} step={.01} value={settings.harmonic_fundamental_hz??.35} onChange={e=>onChange({...settings,harmonic_fundamental_hz:+e.target.value})}/></label>
  <label>Ratios de predicción {scope}<input value={ratiosText} onChange={e=>setRatiosText(e.target.value)} onBlur={()=>onChange({...settings,harmonic_ratios:ratiosText.split(',').map(v=>+v.trim())})}/></label>
  <p>Ratios se aplican al salir del campo. Armónicos declarados: fit sin/cos + DC con ridge, sobre timestamps pasados. Estima el siguiente intervalo con la mediana del pasado; no usa valores ni reloj objetivo futuros. Ratios independientes de las seis voces del instrumento. Sin optimización de frecuencias usando los resultados. Unidades Hz del movimiento, no del audio.</p>
  <small>Retardos en muestras únicas; tendencia por índice de muestra. Todos se ajustan al pasado y se puntúan sobre soporte común. Sin selección automática usando resultados de evaluación.</small>
 </fieldset>;
}
