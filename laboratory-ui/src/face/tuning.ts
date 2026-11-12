/** Shared facial instrument tuning; independent from native body/Shaper state. */
export const FACE_FUNDAMENTAL=40.4;
export const FACE_MIN_HZ=40.4;
export const FACE_MAX_HZ=220;
export const validFundamental=(value:number)=>Number.isFinite(value)&&value>=FACE_MIN_HZ&&value<=FACE_MAX_HZ;
