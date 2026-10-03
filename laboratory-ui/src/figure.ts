export type Voice = {
  frequency_hz: number;
  gain: number;
  phase_rad: number;
  harmonic_n: number;
};
export function phasorPoints(
  voices: Voice[],
  samples: number,
  seconds: number,
  scale: number,
): Float32Array {
  const points = new Float32Array(samples * 2);
  for (let i = 0; i < samples; i++) {
    const t = (i / (samples - 1)) * seconds;
    for (const voice of voices) {
      const phase = voice.phase_rad + 2 * Math.PI * voice.frequency_hz * t;
      points[2 * i] += voice.gain * Math.cos(phase) * scale;
      points[2 * i + 1] += voice.gain * Math.sin(phase) * scale;
    }
  }
  return points;
}

export function ribbon(
  points: Float32Array,
  width: number,
  height: number,
  ax: number,
  ay: number,
  pixels: number,
): Float32Array {
  const result = new Float32Array(points.length * 2),
    n = points.length / 2;
  for (let i = 0; i < n; i++) {
    const before = Math.max(0, i - 1),
      after = Math.min(n - 1, i + 1);
    const dx = (points[after * 2] - points[before * 2]) * ax * width,
      dy = (points[after * 2 + 1] - points[before * 2 + 1]) * ay * height;
    const length = Math.max(Math.hypot(dx, dy), 1e-12),
      ox = ((-dy / length) * pixels) / width / ax,
      oy = ((dx / length) * pixels) / height / ay;
    result.set(
      [
        points[i * 2] + ox,
        points[i * 2 + 1] + oy,
        points[i * 2] - ox,
        points[i * 2 + 1] - oy,
      ],
      i * 4,
    );
  }
  return result;
}

export class Figure {
  gl: WebGLRenderingContext;
  program: WebGLProgram;
  buffer: WebGLBuffer;
  constructor(public canvas: HTMLCanvasElement) {
    const gl = canvas.getContext("webgl", {
      alpha: false,
      antialias: true,
      preserveDrawingBuffer: true,
    });
    if (!gl) throw new Error("Este navegador no ofrece WebGL para la figura.");
    this.gl = gl;
    const shader = (kind: number, source: string) => {
      const s = gl.createShader(kind)!;
      gl.shaderSource(s, source);
      gl.compileShader(s);
      if (!gl.getShaderParameter(s, gl.COMPILE_STATUS))
        throw new Error(gl.getShaderInfoLog(s) || "shader");
      return s;
    };
    const vs = shader(
      gl.VERTEX_SHADER,
      "attribute vec2 point; uniform vec2 aspect; void main(){gl_Position=vec4(point*aspect,0.,1.);}",
    );
    const fs = shader(
      gl.FRAGMENT_SHADER,
      "precision mediump float; uniform vec4 color; void main(){gl_FragColor=color;}",
    );
    this.program = gl.createProgram()!;
    gl.attachShader(this.program, vs);
    gl.attachShader(this.program, fs);
    gl.linkProgram(this.program);
    if (!gl.getProgramParameter(this.program, gl.LINK_STATUS))
      throw new Error("No se pudo preparar la figura WebGL.");
    gl.deleteShader(vs);
    gl.deleteShader(fs);
    this.buffer = gl.createBuffer()!;
    gl.useProgram(this.program);
    gl.bindBuffer(gl.ARRAY_BUFFER, this.buffer);
    const loc = gl.getAttribLocation(this.program, "point");
    gl.enableVertexAttribArray(loc);
    gl.vertexAttribPointer(loc, 2, gl.FLOAT, false, 0, 0);
    gl.enable(gl.BLEND);
    gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA);
    this.clear();
  }
  clear() {
    this.gl.clearColor(0.015, 0.025, 0.045, 1);
    this.gl.clear(this.gl.COLOR_BUFFER_BIT);
  }
  draw(voices: Voice[], visual: any, fundamental: number) {
    const gl = this.gl,
      w = Math.round(this.canvas.clientWidth * devicePixelRatio),
      h = Math.round(this.canvas.clientHeight * devicePixelRatio);
    if (this.canvas.width !== w || this.canvas.height !== h) {
      this.canvas.width = w;
      this.canvas.height = h;
      this.clear();
    }
    gl.viewport(0, 0, w, h);
    gl.useProgram(this.program);
    gl.bindBuffer(gl.ARRAY_BUFFER, this.buffer);
    const color = gl.getUniformLocation(this.program, "color"),
      aspect = gl.getUniformLocation(this.program, "aspect");
    gl.uniform2f(aspect, 1, 1);
    gl.uniform4f(color, 0.015, 0.025, 0.045, 1 - visual.persistence);
    gl.bufferData(
      gl.ARRAY_BUFFER,
      new Float32Array([-1, -1, 1, -1, -1, 1, 1, 1]),
      gl.DYNAMIC_DRAW,
    );
    gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
    const ax = Math.min(1, h / w),
      ay = Math.min(1, w / h);
    gl.uniform2f(aspect, ax, ay);
    const sum = voices.reduce((n, v) => n + v.gain, 0),
      scale =
        (0.85 * visual.scale) / (visual.auto_scale ? Math.max(sum, 0.02) : 1);
    const palette: Record<string, number[]> = {
      ice: [0.3, 0.85, 1],
      gold: [1, 0.7, 0.27],
      violet: [0.76, 0.5, 1],
    };
    const rgb = palette[visual.color] || palette.ice;
    const line = (vs: Voice[], alpha: number) => {
      const points = phasorPoints(
        vs,
        visual.samples,
        visual.window_periods / fundamental,
        scale,
      );
      gl.bufferData(
        gl.ARRAY_BUFFER,
        ribbon(points, w, h, ax, ay, visual.line_width * devicePixelRatio),
        gl.DYNAMIC_DRAW,
      );
      gl.uniform4f(
        color,
        rgb[0],
        rgb[1],
        rgb[2],
        Math.min(1, alpha * visual.brightness),
      );
      gl.drawArrays(gl.TRIANGLE_STRIP, 0, visual.samples * 2);
    };
    if (visual.components) voices.forEach((v) => line([v], 0.15));
    line(voices, 0.9);
  }
  dispose() {
    this.gl.deleteBuffer(this.buffer);
    this.gl.deleteProgram(this.program);
  }
}
