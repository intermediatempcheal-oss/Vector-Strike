export default function SplashParticles({ active }: { active: boolean }) {
    const cells = [
        { l: 4, t: 16, d: 0, s: 3 },
        { l: 12, t: 42, d: 1.2, s: 2 },
        { l: 20, t: 60, d: 2.4, s: 2.4 },
        { l: 28, t: 22, d: 0.6, s: 3 },
        { l: 36, t: 70, d: 1.8, s: 2 },
        { l: 44, t: 34, d: 3, s: 2.6 },
        { l: 52, t: 8, d: 2.2, s: 3 },
        { l: 60, t: 64, d: 0.9, s: 2.2 },
        { l: 68, t: 24, d: 3.6, s: 2.8 },
        { l: 76, t: 48, d: 1.5, s: 2 },
        { l: 84, t: 12, d: 2.8, s: 3 },
        { l: 92, t: 40, d: 0.3, s: 2.4 },
        { l: 16, t: 80, d: 4, s: 2 },
        { l: 70, t: 84, d: 3.2, s: 2.4 },
        { l: 46, t: 88, d: 4.4, s: 2.2 },
        { l: 88, t: 78, d: 5, s: 2 },
    ];

    return (
        <div className="vs-particles" aria-hidden>
            {cells.map((p, i) => (
                <span
                    key={i}
                    className="vs-particles__cell"
                    style={{
                        left: `${p.l}%`,
                        top: `${p.t}%`,
                        animationDelay: `${p.d}s`,
                        animationDuration: `${p.s + 5}s`,
                    }}
                />
            ))}
            <span className="vs-particles__aura" data-active={active} />
        </div>
    );
}