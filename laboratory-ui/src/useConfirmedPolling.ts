import {useEffect,useState} from 'react';

/** Retain confirmed reads, expose failures immediately and never overlap batches. */
export function useConfirmedPolling(api:any,paths:readonly string[],initial:any[],periodMs=500){
 const [data,setData]=useState(initial),[error,setError]=useState(''),[ready,setReady]=useState(false);
 const pathKey=JSON.stringify(paths);
 useEffect(()=>{let live=true,inFlight=false;
  const selectedPaths:string[]=JSON.parse(pathKey);
  const poll=async()=>{
   if(inFlight)return;inFlight=true;
   try{
    const results=await Promise.allSettled(selectedPaths.map(async path=>{
     try{return await api(path)}catch(e){if(live)setError(String(e));throw e}
    }));
    const values=results.map(result=>{if(result.status==='rejected')throw result.reason;return result.value});
    if(live){setData(values);setError('');setReady(true)}
   }catch(e){if(live)setError(String(e))}
   finally{inFlight=false}
  };
  void poll();const timer=setInterval(()=>void poll(),periodMs);return()=>{live=false;clearInterval(timer)};
 },[api,pathKey,periodMs]);
 return {data,error,ready,setData};
}
