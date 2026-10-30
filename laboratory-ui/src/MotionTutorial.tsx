import {useEffect, useState} from "react";
import "./MotionTutorial.css";

type Data = Record<string, any>;
type Point = [number, number];
const steps = [
  {title: "Dibujá círculos con las manos", detail: "Con los codos cómodos, mové las manos en círculos pequeños. Hacé una vuelta lenta y otra un poco más rápida.",
    voices: [4, 6], joints: [7, 8, 9, 10], cue: "Mirá las voces de codos y muñecas. Girar los dedos sin desplazar la muñeca no mueve ese punto del seguimiento."},
  {title: "Balanceá hombros y caderas", detail: "Con los pies apoyados, desplazá suavemente el torso de un lado al otro. Volvé al centro y descansá unos segundos.",
    voices: [1, 2], joints: [5, 6, 11, 12], cue: "Mirá caderas y hombros. Un mismo gesto puede activar varias voces: estamos explorando, no aislando músculos."},
  {title: "Alterná pequeños pasos", detail: "Levantá y apoyá un pie, después el otro, a tu ritmo. Dejá rodillas y pies completos dentro de la imagen.",
    voices: [3, 5], joints: [13, 14, 15, 16], cue: "Mirá rodillas y tobillos. Si esos puntos no se observan, ajustá el encuadre antes de interpretar el sonido."},
];
const edges = [[5,6],[5,7],[7,9],[6,8],[8,10],[5,11],[6,12],[11,12],[11,13],[13,15],[12,14],[14,16]];

/** A deliberately synthetic demonstration, never an observed or scored pose. */
export function demonstrationPose(step: number, phase: number): Point[] {
  const a = phase * 2 * Math.PI, s = Math.sin(a);
  const points: Point[] = [[160,54],[150,50],[170,50],[141,57],[179,57],
    [123,105],[197,105],[100,167],[220,167],[92,222],[228,222],
    [140,226],[180,226],[137,300],[183,300],[132,377],[188,377]];
  if (step === 0) {
    points[9] = [92 + 23 * s, 204 + 20 * Math.cos(a)];
    points[10] = [228 - 23 * s, 204 - 20 * Math.cos(a)];
    points[7] = [105 + 6 * s, 157]; points[8] = [215 - 6 * s, 157];
  } else if (step === 1) {
    for (let i = 0; i < 11; i++) points[i][0] += 19 * s;
    points[5][1] += 7 * s; points[6][1] -= 7 * s;
    points[11][0] -= 9 * s; points[12][0] -= 9 * s;
  } else {
    const left = Math.max(0, s), right = Math.max(0, -s);
    points[13][1] -= 28 * left; points[15][1] -= 28 * left;
    points[14][1] -= 28 * right; points[16][1] -= 28 * right;
  }
  return points;
}

export function MotionTutorial({state, onClose}: {state: Data; onClose: () => void}) {
  const [step, setStep] = useState(0), [done, setDone] = useState(false);
  const [playing, setPlaying] = useState(() => !window.matchMedia("(prefers-reduced-motion: reduce)").matches);
  const [phase, setPhase] = useState(0), [visible, setVisible] = useState(!document.hidden);
  useEffect(() => {
    const preference = window.matchMedia("(prefers-reduced-motion: reduce)");
    const reduce = () => {if (preference.matches) setPlaying(false);};
    const visibility = () => setVisible(!document.hidden);
    preference.addEventListener("change", reduce); document.addEventListener("visibilitychange", visibility);
    return () => {preference.removeEventListener("change", reduce); document.removeEventListener("visibilitychange", visibility);};
  }, []);
  useEffect(() => {
    if (!playing || !visible || done) return;
    let frame = 0, last = 0;
    const animate = (now: number) => {
      if (!last) last = now;
      if (now - last >= 33) {
        setPhase(value => (value + Math.min(now - last, 100) / 4000) % 1); last = now;
      }
      frame = requestAnimationFrame(animate);
    };
    frame = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(frame);
  }, [playing, visible, done]);
  const current = steps[step], points = demonstrationPose(step, phase);
  const person = state.motion_frame?.persons?.find((p: Data) => p.person_id === state.session?.person_id);
  const observed = current.joints.filter(index => person?.joints?.some((j: Data) => j.index === index && j.state === "observed" && j.position));
  const routing = state.runtime?.routing?.voices || {};
  const changeStep = (next: number) => {setStep(next); setPhase(0); setDone(false);};
  return <section className="motion-tutorial" id="movement-tutorial" aria-label="Tutorial de movimiento">
    <div className="stage-label">Tu primer instrumento <span>3 movimientos · sin cambiar tus ajustes</span></div>
    <div className="tutorial-content">
      <div className="tutorial-heading"><h2>{done ? "Listo para explorar" : `Paso ${step + 1} de 3`}</h2>
        <button onClick={onClose}>Cerrar tutorial</button></div>
      {done ? <>
        <p>Ya recorriste manos, torso y piernas. Volvé a Performance para escuchar una voz en Solo o cambiar un parámetro por vez.</p>
        <p>Tu experiencia vale: anotá qué escuchaste y qué sentiste. Completar esta guía no certifica el seguimiento ni mide emociones.</p>
        <button onClick={() => changeStep(0)}>Volver a empezar</button>
      </> : <>
        <nav className="tutorial-steps" aria-label="Pasos del tutorial">
          {steps.map((item, index) => <button key={item.title} aria-current={step === index ? "step" : undefined}
            onClick={() => changeStep(index)}>{index + 1}. {index === 0 ? "Manos" : index === 1 ? "Torso" : "Pasos"}</button>)}
        </nav>
        <h3>{current.title}</h3><p>{current.detail}</p>
        <div className="tutorial-demo">
          <svg viewBox="0 0 320 410" role="img" aria-label={`Ejemplo animado: ${current.title}`} data-phase={phase.toFixed(4)}>
            <line x1="64" x2="256" y1="389" y2="389" className="tutorial-ground"/>
            <circle cx={points[0][0]} cy={points[0][1]} r="25" className="tutorial-head"/>
            {edges.map(([a,b]) => <line key={`${a}-${b}`} x1={points[a][0]} y1={points[a][1]} x2={points[b][0]} y2={points[b][1]}/>)}
            {points.slice(5).map((point, index) => <circle key={index} cx={point[0]} cy={point[1]}
              r={current.joints.includes(index + 5) ? 7 : 4} className={current.joints.includes(index + 5) ? "tutorial-highlight" : ""}/>) }
          </svg>
          <p>Figura azul de ejemplo · copiá el recorrido a tu ritmo.</p>
          <div className="actions"><button aria-pressed={!playing} onClick={() => setPlaying(value => !value)}>
            {playing ? "Pausar ejemplo" : "Reproducir ejemplo"}</button>
            <button disabled={playing} onClick={() => setPhase(value => (value + .25) % 1)}>Siguiente posición</button></div>
        </div>
        <p className="tutorial-feedback" role="status">{!state.source?.kind ? "Encendé la cámara para ver tu seguimiento; el ejemplo ya se puede explorar."
          : state.source.kind !== "camera" ? "Estás viendo un video: las barras pertenecen a esa fuente. Elegí la cámara para probar tu movimiento."
          : !person ? "Esperando a la persona seleccionada en la imagen."
          : `${observed.length} de ${current.joints.length} puntos de este gesto observados en tu cuerpo.`}</p>
        <div className="tutorial-voices" aria-label="Respuesta real de las voces">
          {current.voices.map(id => {
            const voice = state.preset?.voices?.find((v: Data) => v.id === id), status = routing[String(id)];
            const gain = person && state.session?.status === "playing" && status?.state === "active" && Number.isFinite(status.target_gain)
              ? Math.max(0, Math.min(1, status.target_gain)) : 0;
            return <label key={id}>{voice?.label || `Voz ${id}`} · ratio {voice?.ratio ?? id}
              <meter min={0} max={1} value={gain} aria-label={`Señal de ${voice?.label || `voz ${id}`}`}/>
              <small>{gain > 0 ? "Movimiento enviado al sonido" : status?.state === "muted" ? "Voz en silencio por Solo o Silenciar" : "Sin ganancia enviada ahora"}</small>
            </label>;
          })}
        </div>
        <p className="tutorial-cue">{current.cue}</p>
        <p className="tutorial-note">Las barras muestran ganancia enviada al motor. La figura no califica tu gesto ni representa tus puntos reales. La guía no cambia presets ni inicia grabaciones.</p>
        <div className="tutorial-next"><button disabled={step === 0} onClick={() => changeStep(step - 1)}>Anterior</button>
          <button onClick={() => step < 2 ? changeStep(step + 1) : setDone(true)}>{step < 2 ? "Ya lo probé · siguiente" : "Terminar tutorial"}</button></div>
      </>}
    </div>
  </section>;
}
