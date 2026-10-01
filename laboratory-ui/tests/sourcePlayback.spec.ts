import {test,expect} from '@playwright/test';
import {sourcePlayback} from '../src/sourcePlayback';
test('source crop follows audio, pauses in tail and returns on backward seek',()=>{
 expect(sourcePlayback(.5,true,33,34,2)).toEqual({position:33.5,playing:true,epoch:2});
 expect(sourcePlayback(1.5,true,33,34,2)).toEqual({position:34,playing:false,epoch:2});
 expect(sourcePlayback(.1,false,33,34,3)).toEqual({position:33.1,playing:false,epoch:3});
 expect(sourcePlayback(0,true,33,34,4)).toEqual({position:33,playing:true,epoch:4});
 for(const t of [NaN,Infinity,-1])expect(()=>sourcePlayback(t,true,33,34,0)).toThrow();
});
