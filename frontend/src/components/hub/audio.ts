// Tiny WebAudio synth for gameplay feedback — no asset downloads.
// Mute preference is a UI setting (not game data), so it lives in localStorage.

export type Sfx = 'hit' | 'combo' | 'miss' | 'start' | 'win' | 'lose' | 'click';

const MUTE_KEY = 'vs:sfx-muted';
let ctx: AudioContext | null = null;
let muted = typeof window !== 'undefined' && window.localStorage?.getItem(MUTE_KEY) === '1';
const listeners = new Set<(muted: boolean) => void>();

export function isMuted() {
    return muted;
}

export function setMuted(next: boolean) {
    muted = next;
    try {
        window.localStorage.setItem(MUTE_KEY, next ? '1' : '0');
    } catch {
        /* storage unavailable — keep in-memory value */
    }
    listeners.forEach((fn) => fn(next));
}

export function subscribeMuted(fn: (muted: boolean) => void) {
    listeners.add(fn);
    return () => {
        listeners.delete(fn);
    };
}

const TONES: Record<Sfx, Array<[freq: number, ms: number]>> = {
    hit: [[660, 70]],
    combo: [[660, 60], [990, 90]],
    miss: [[180, 140]],
    start: [[440, 80], [660, 80], [880, 120]],
    win: [[523, 110], [659, 110], [784, 110], [1046, 220]],
    lose: [[392, 160], [262, 260]],
    click: [[520, 35]],
};

export function sfx(name: Sfx) {
    if (muted || typeof window === 'undefined') return;
    try {
        const Ctor = window.AudioContext || (window as unknown as { webkitAudioContext?: typeof AudioContext }).webkitAudioContext;
        if (!Ctor) return;
        ctx = ctx ?? new Ctor();
        if (ctx.state === 'suspended') void ctx.resume();
        let t = ctx.currentTime;
        for (const [freq, ms] of TONES[name]) {
            const osc = ctx.createOscillator();
            const gain = ctx.createGain();
            osc.type = name === 'miss' || name === 'lose' ? 'sawtooth' : 'triangle';
            osc.frequency.setValueAtTime(freq, t);
            gain.gain.setValueAtTime(0.0001, t);
            gain.gain.exponentialRampToValueAtTime(0.08, t + 0.01);
            gain.gain.exponentialRampToValueAtTime(0.0001, t + ms / 1000);
            osc.connect(gain).connect(ctx.destination);
            osc.start(t);
            osc.stop(t + ms / 1000 + 0.02);
            t += ms / 1000;
        }
    } catch {
        /* audio is best-effort */
    }
}
