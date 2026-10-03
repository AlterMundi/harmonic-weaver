// A trailing window of actual PCM samples; no sample later than the media clock.
export function pastWindow(position:number,sr:number,total:number,points:number,stride:number){
 if(!Number.isFinite(position) || position<0 || !Number.isInteger(sr) || sr<=0 || !Number.isInteger(total) || total<=0 || !Number.isInteger(points) || points<2 || points>4096 || !Number.isInteger(stride) || stride<1 || stride>32)throw Error('Reloj o ventana de proyección inválidos');
 const end=Math.min(total,Math.floor(position*sr));
 const count=Math.min(points,Math.floor((end-1)/stride)+1);
 if(count<2)return null;
 return {start_sample:end-1-(count-1)*stride,points:count};
}
