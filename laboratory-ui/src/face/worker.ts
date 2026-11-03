import {FaceLandmarker,FilesetResolver} from '@mediapipe/tasks-vision';
let model:FaceLandmarker|undefined;
self.onmessage=async(event:MessageEvent)=>{
 const {type,base,bitmap,time,id}=event.data;
 try{
  if(type==='init'){
   const files=await FilesetResolver.forVisionTasks(base+'face-assets/wasm');
   model=await FaceLandmarker.createFromOptions(files,{baseOptions:{modelAssetPath:base+'face-assets/face_landmarker.task',delegate:'CPU'},runningMode:'VIDEO',numFaces:2,minFaceDetectionConfidence:.6,minFacePresenceConfidence:.6,minTrackingConfidence:.6,outputFaceBlendshapes:false});
   self.postMessage({type:'ready'});
  }else if(type==='frame'&&model){
   try{const result=model.detectForVideo(bitmap,time);self.postMessage({type:'frame',id,time,faces:result.faceLandmarks,width:bitmap.width,height:bitmap.height});}
   finally{bitmap.close();}
  }
 }catch(error){bitmap?.close();self.postMessage({type:'error',id,message:String(error)});}
};
