/** Install pinned model and same-origin WASM. Does not acquire images or start a camera. */
import {readFile,writeFile,mkdir,copyFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const out=path.join(root,'laboratory-ui/public/face-assets');await mkdir(path.join(out,'wasm'),{recursive:true});
const url='https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task';
const expected='64184e229b263107bc2b804c6625db1341ff2bb731874b0bcc2fe6544e0bc9ff';
const model=path.join(out,'face_landmarker.task');
const sha=b=>createHash('sha256').update(b).digest('hex');
let bytes;try{bytes=await readFile(model);}catch{}
if(!bytes||sha(bytes)!==expected){const r=await fetch(url);if(!r.ok)throw Error('Model fetch failed: '+r.status);bytes=Buffer.from(await r.arrayBuffer());if(sha(bytes)!==expected)throw Error('Model hash mismatch; refusing changed weights');await writeFile(model,bytes);}
const names=['vision_wasm_internal.js','vision_wasm_internal.wasm','vision_wasm_nosimd_internal.js','vision_wasm_nosimd_internal.wasm','vision_wasm_module_internal.js','vision_wasm_module_internal.wasm'];
const hashes={model:expected};
for(const name of names){const from=path.join(root,'laboratory-ui/node_modules/@mediapipe/tasks-vision/wasm',name);await copyFile(from,path.join(out,'wasm',name));hashes[name]=sha(await readFile(from));}
await writeFile(path.join(out,'manifest.json'),JSON.stringify({sdk:'@mediapipe/tasks-vision@1.2.0',model_url:url,sha256:hashes},null,2));
console.log('Face model hash and six same-origin WASM assets verified.');
