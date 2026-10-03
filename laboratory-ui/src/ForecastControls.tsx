type Data=Record<string,any>;
export const predictorLabels:Record<string,string>={persistence:'Persistencia',full_ridge:'Ridge completo',subspace_ridge:'Ridge subespacio',linear_trend:'Tendencia lineal',lagged_full_ridge:'Ridge completo con retardos',lagged_subspace_ridge:'Ridge subespacio con retardos'};
export const defaultPredictors=['persistence','full_ridge','subspace_ridge'];
export function ForecastControls({settings,onChange,scope}:Data){
 const chosen=settings.predictors||defaultPredictors;
 return <fieldset><legend>Predictores {scope}</legend>
  {Object.entries(predictorLabels).map(([key,label])=><label key={key}><input type="checkbox" aria-label={`${label} ${scope}`} checked={chosen.includes(key)} onChange={e=>onChange({...settings,predictors:e.target.checked?[...chosen,key]:chosen.filter((k:string)=>k!==key)})}/>{label}</label>)}
  <label>Retardos autorregresivos {scope}<input type="number" min={1} max={12} step={1} value={settings.autoregressive_lags??3} onChange={e=>onChange({...settings,autoregressive_lags:+e.target.value})}/></label>
  <small>Retardos en muestras únicas; tendencia por índice de muestra. Todos se ajustan al pasado y se puntúan sobre soporte común. Sin selección automática usando resultados de evaluación.</small>
 </fieldset>;
}
