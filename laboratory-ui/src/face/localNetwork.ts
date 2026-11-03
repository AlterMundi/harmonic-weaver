/** The pinned face SDK may emit diagnostic XHRs. Keep every worker request local. */
export function installLocalNetwork(origin:string){
 const allowed=(value:string|URL)=>new URL(String(value),self.location.href).origin===origin;
 const nativeFetch=globalThis.fetch.bind(globalThis);
 globalThis.fetch=(input:RequestInfo|URL,init?:RequestInit)=>{
  const url=input instanceof Request?input.url:input;
  return allowed(url)?nativeFetch(input,init):Promise.reject(new DOMException('Face worker only permits same-origin resources.','SecurityError'));
 };
 const open=XMLHttpRequest.prototype.open;
 XMLHttpRequest.prototype.open=function(method:string,url:string|URL,async:boolean=true,user?:string|null,password?:string|null){
  if(!allowed(url))throw new DOMException('Face worker only permits same-origin resources.','SecurityError');
  return open.call(this,method,String(url),async,user,password);
 };
}
