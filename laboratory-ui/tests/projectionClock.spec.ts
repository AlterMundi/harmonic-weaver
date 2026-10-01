import {test,expect} from '@playwright/test';
import {pastWindow} from '../src/projectionClock';
test('past window never displays PCM samples beyond playback, including start/end and seeks',()=>{
 expect(pastWindow(0,8000,14400,512,1)).toBeNull();
 for(const time of [.0001,.01,.05,.5,1.799,1.8,2])for(const stride of [1,3,32]){
  const window=pastWindow(time,8000,14400,512,stride);
  if(!window)continue;
  expect(window.start_sample).toBeGreaterThanOrEqual(0);
  const last=window.start_sample+(window.points-1)*stride;
  expect(last).toBeLessThan(14400);
  expect((last+1)/8000).toBeLessThanOrEqual(time);
 }
 expect(pastWindow(.5,8000,14400,512,1)).toEqual({start_sample:3488,points:512});
 expect(pastWindow(.1,8000,14400,512,1)).toEqual({start_sample:288,points:512});
});
test('invalid display clocks/windows are rejected',()=>{
 for(const args of [[NaN,8000,14400,512,1],[.1,0,14400,512,1],[.1,8000,14400,1,1],[.1,8000,14400,512,33]]){
  expect(()=>pastWindow(...args as [number,number,number,number,number])).toThrow();
 }
});
