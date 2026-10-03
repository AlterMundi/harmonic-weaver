// Explicit save attempts only. IndexedDB supports inputs larger than sessionStorage.
export async function multiviewPending(value?:unknown):Promise<any>{
 const db=await new Promise<IDBDatabase>((resolve,reject)=>{
  const request=indexedDB.open('weaver-r09-multiview',1);
  request.onupgradeneeded=()=>request.result.createObjectStore('pending');
  request.onsuccess=()=>resolve(request.result);request.onerror=()=>reject(request.error);
 });
 return new Promise((resolve,reject)=>{
  const tx=db.transaction('pending',value===undefined?'readonly':'readwrite'),store=tx.objectStore('pending');
  const request=value===undefined?store.get('start'):value===null?store.delete('start'):store.put(value,'start');
  tx.oncomplete=()=>{const result=request.result;db.close();resolve(result)};
  tx.onerror=()=>{db.close();reject(tx.error)};tx.onabort=()=>{db.close();reject(tx.error)};
 });
}
