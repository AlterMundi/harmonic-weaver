type Row={time_s:number;person_present:boolean;coordinate_frame:string;unit:string;dimensions:number;width:number;height:number;joints:any[]};
export function poseAt(rows:Row[],time:number,maxAge:number):{row:Row|null;reason:string}{
 if(!Number.isFinite(time) || !Number.isFinite(maxAge) || maxAge<=0)return {row:null,reason:'Reloj o antigüedad inválidos'};
 let lo=0,hi=rows.length;
 while(lo<hi){const mid=(lo+hi)>>>1;if(rows[mid].time_s<=time)lo=mid+1;else hi=mid;}
 const row=rows[lo-1];
 if(!row)return {row:null,reason:'Sin observación anterior'};
 if(time-row.time_s>maxAge)return {row:null,reason:'Gap: observación demasiado antigua'};
 if(!row.person_present)return {row:null,reason:'Cuerpo seleccionado ausente'};
 if(row.coordinate_frame!=='camera_isotropic' || row.unit!=='frame_height' || row.dimensions!==2)
  return {row:null,reason:'Coordenadas no proyectables sobre este video'};
 return {row,reason:'Observación congelada'};
}
export const poseLinks=[[5,6],[5,7],[7,9],[6,8],[8,10],[5,11],[6,12],[11,12],[11,13],[13,15],[12,14],[14,16]];
