import {readFileSync,writeFileSync} from 'node:fs';
import {dirname,resolve} from 'node:path';
import {fileURLToPath} from 'node:url';
const root=dirname(fileURLToPath(import.meta.url));
const target=process.argv[2];if(!target)throw Error('Pass the final standalone HTML path.');
const geometry=readFileSync(resolve(root,'geometry.mjs'),'utf8').replace(/^export /gm,'');
writeFileSync(target,readFileSync(resolve(root,'demo.template.html'),'utf8').replace('/* GEOMETRY_MODULE */',geometry));
