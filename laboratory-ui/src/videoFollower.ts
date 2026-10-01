export type Playback = { position: number; playing: boolean; epoch: number };

// Follow the causal server clock without repeatedly interrupting decoder seeks.
export class VideoFollower {
  private pending = false;
  private disposed = false;
  private epoch: number | null = null;
  private lastCorrection = -Infinity;
  constructor(private el: HTMLVideoElement, private state: () => Playback,
    private error: (message: string) => void,
    private now: () => number = () => performance.now()) {
    el.addEventListener("loadedmetadata", this.sync);
    el.addEventListener("canplay", this.sync);
    el.addEventListener("seeked", this.sync);
  }
  sync = () => {
    if (this.disposed) return;
    const target = this.state();
    if (!target.playing && !this.el.paused) this.el.pause();
    if (this.el.readyState < 1) return;
    const discontinuity = this.epoch !== target.epoch;
    const offset = target.position - this.el.currentTime;
    const drift = Math.abs(offset);
    // Small clock differences must not repeatedly flush the video decoder.
    this.el.playbackRate = target.playing && !discontinuity && drift < 2
      ? Math.max(.9, Math.min(1.1, 1 + offset * .2)) : 1;
    if (!this.pending && !this.el.seeking && drift > (target.playing && !discontinuity ? 2 : .04) &&
      (discontinuity || !target.playing || this.now() - this.lastCorrection > 1000)) {
      this.el.currentTime = target.position;
      this.lastCorrection = this.now();
      // The decoder applies this seek asynchronously. Consume the epoch now,
      // so seeked follows the advancing clock instead of seeking again.
      this.epoch = target.epoch;
    }
    if (!this.el.seeking && !this.pending) this.epoch = target.epoch;
    if (target.playing && this.el.paused && !this.pending) {
      this.pending = true;
      void this.el.play().catch(e => {
        if (!this.disposed && e?.name !== "AbortError") this.error(String(e));
      }).finally(() => { this.pending = false;
        if (!this.disposed && !this.state().playing) this.el.pause();
      });
    }
  };
  dispose() {
    this.disposed = true;
    this.el.removeEventListener("loadedmetadata", this.sync);
    this.el.removeEventListener("canplay", this.sync);
    this.el.removeEventListener("seeked", this.sync);
  }
}
