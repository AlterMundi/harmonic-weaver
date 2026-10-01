import {test,expect} from '@playwright/test';
import {poseAt} from '../src/poseOverlay';
const row={time_s:1,person_present:true,coordinate_frame:'camera_isotropic',unit:'frame_height',dimensions:2,width:640,height:480,joints:[]};
test('overlay selects only past observations and refuses missing, stale and world rows',()=>{
 const rows=[row,{...row,time_s:2,person_present:false},{...row,time_s:3,coordinate_frame:'world'}];
 expect(poseAt(rows,.9,.1).row).toBeNull();
 expect(poseAt(rows,1.05,.1).row).toBe(row);
 expect(poseAt(rows,1.2,.1).reason).toContain('Gap');
 expect(poseAt(rows,2,.1).reason).toContain('ausente');
 expect(poseAt(rows,3,.1).reason).toContain('no proyectables');
 expect(poseAt(rows,1,.1).row).toBe(row); // backward seek
 expect(poseAt(rows,NaN,.1).row).toBeNull();
});
