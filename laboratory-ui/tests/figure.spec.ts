import {test,expect} from '@playwright/test';
import {phasorPoints,ribbon} from '../src/figure';

for(const count of [1,6,32])test(`sum all ${count} effective voices, without a two-channel shortcut`,()=>{
  const voices=Array.from({length:count},(_,i)=>({frequency_hz:40*(i+1),gain:.1/(i+1),phase_rad:i*.13,harmonic_n:i+1}));
  const points=phasorPoints(voices,512,.05,.8);
  for(const i of [0,103,511]){
    const t=i/511*.05;
    expect(points[2*i]).toBeCloseTo(voices.reduce((sum,v)=>sum+v.gain*Math.cos(v.phase_rad+2*Math.PI*v.frequency_hz*t)*.8,0),6);
    expect(points[2*i+1]).toBeCloseTo(voices.reduce((sum,v)=>sum+v.gain*Math.sin(v.phase_rad+2*Math.PI*v.frequency_hz*t)*.8,0),6);
  }
});

test('line width uses geometry even when WebGL supports only 1px lines',()=>{
  const points=new Float32Array([-.5,0,.5,0]);
  const vertices=ribbon(points,1000,500,.5,1,4);
  expect(vertices[1]-vertices[3]).toBeCloseTo(8/500);
});
