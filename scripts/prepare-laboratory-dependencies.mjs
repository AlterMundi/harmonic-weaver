import {createHash} from 'node:crypto';
import {readFileSync,writeFileSync,existsSync} from 'node:fs';
import {dirname,resolve,join} from 'node:path';
import {fileURLToPath} from 'node:url';
import {spawnSync} from 'node:child_process';

// Reconcile installed UI packages after a source update, before starting audio.
const ui=resolve(dirname(fileURLToPath(import.meta.url)),'../laboratory-ui');
const marker=join(ui,'node_modules','.weaver-dependencies.sha256');
const hash=createHash('sha256');
for(const name of ['package.json','package-lock.json'])hash.update(name+'\0').update(readFileSync(join(ui,name)));
hash.update(JSON.stringify([process.platform,process.arch,process.versions.modules]));
const fingerprint=hash.digest('hex');
let installed='';try{installed=readFileSync(marker,'utf8').trim();}catch{}
if(!existsSync(join(ui,'node_modules'))||installed!==fingerprint){
 console.log('Updating laboratory UI dependencies from the committed lockfile…');
 const result=spawnSync(process.platform==='win32'?'npm.cmd':'npm',['ci','--no-audit','--no-fund'],{cwd:ui,stdio:'inherit',shell:process.platform==='win32'});
 if(result.error){console.error(result.error.message);process.exit(1);}
 if(result.status!==0)process.exit(result.status||1);
 writeFileSync(marker,fingerprint+'\n');
}
