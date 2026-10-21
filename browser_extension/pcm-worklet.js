class Pcm16CaptureProcessor extends AudioWorkletProcessor {
  constructor() {
    super();
    this.chunkFrames = 640;
    this.offset = 0;
    this.chunk = new Float32Array(this.chunkFrames);
  }

  process(inputs) {
    const channels = inputs[0];
    if (!channels || channels.length === 0) return true;
    const frameCount = Math.min(...channels.map((channel) => channel.length));
    for (let frame = 0; frame < frameCount; frame += 1) {
      let sample = 0;
      for (const channel of channels) sample += channel[frame];
      this.chunk[this.offset] = sample / channels.length;
      this.offset += 1;
      if (this.offset === this.chunkFrames) {
        const pcm = new Int16Array(this.chunkFrames);
        for (let index = 0; index < this.chunkFrames; index += 1) {
          const value = Math.max(-1, Math.min(1, this.chunk[index]));
          pcm[index] = value < 0 ? value * 32768 : value * 32767;
        }
        this.port.postMessage(pcm.buffer, [pcm.buffer]);
        this.chunk = new Float32Array(this.chunkFrames);
        this.offset = 0;
      }
    }
    return true;
  }
}

registerProcessor('pcm16-capture', Pcm16CaptureProcessor);
