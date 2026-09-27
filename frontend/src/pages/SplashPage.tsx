import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Button from '../components/Button';
import { SplashLogo } from '../components/Logo';
import SplashParticles from '../components/SplashParticles';
import SplashPreviews from '../components/SplashPreviews';
import { useAuthStore } from '../store/auth';

export default function SplashPage() {
    const navigate = useNavigate();
    const init = useAuthStore((s) => s.init);
    const authenticated = useAuthStore((s) => s.authenticated);
    const onboardingComplete = useAuthStore((s) => s.onboarding_complete);
    const initialized = useAuthStore((s) => s.initialized);
    const [showContinue, setShowContinue] = useState(false);

    useEffect(() => {
        if (initialized) {
            if (authenticated) {
                decide(authenticated, onboardingComplete);
            } else {
                setShowContinue(true);
            }
            return;
        }

        let done = false;
        const boot = async () => {
            try {
                await init();
            } catch {
                // Backend unreachable — never trap the user on the splash.
            }
            if (done) return;
            const { authenticated: bootedAuthenticated, onboarding_complete } = useAuthStore.getState();
            if (bootedAuthenticated) {
                decide(bootedAuthenticated, onboarding_complete);
            } else {
                setShowContinue(true);
            }
        };
        void boot();
        return () => {
            done = true;
        };
    }, [authenticated, onboardingComplete, initialized, init, navigate]);

    const decide = (authenticated: boolean, onboardingComplete: boolean) => {
        if (authenticated && onboardingComplete) {
            navigate('/home', { replace: true });
            return;
        }
        if (authenticated && !onboardingComplete) {
            navigate('/onboarding/welcome', { replace: true });
            return;
        }
        navigate('/auth-choice', { replace: true });
    };

    const handleDone = () => {
        setShowContinue(true);
    };

    return (
        <div className={`vs-splash${showContinue ? ' has-cta' : ''}`} data-fade={false}>
            <div className="vs-splash__bg" aria-hidden />
            <video
                className="vs-splash__video"
                autoPlay
                muted
                loop
                playsInline
                preload="auto"
                disablePictureInPicture
                aria-hidden
            >
                <source src="/assets/video/splash.webm" type="video/webm" />
                <source src="/assets/video/splash.mp4" type="video/mp4" />
            </video>
            <div className="vs-splash__scrim" aria-hidden />
            <header className="vs-splash__brand">
                <img
                    src="/assets/branding/logo-mark.svg"
                    alt=""
                    aria-hidden
                    width={26}
                    height={26}
                    className="vs-splash__brandmark"
                />
                <span className="vs-splash__brandword">VECTOR STRIKE</span>
                <span className="vs-splash__brandtag">PLAY · RANK · EVOLVE</span>
            </header>
            <SplashParticles active />
            <div className="vs-splash__center">
                <SplashLogo onDone={handleDone} />
                <div className="vs-splash__tagline">
                    The Vector Strike arcade — play mini-games, rack up XP, climb the global ranks.
                </div>
                {showContinue && (
                    <div className="vs-splash__actions">
                        <Button size="xl" onClick={() => decide(false, false)}>
                            Continue
                        </Button>
                    </div>
                )}
            </div>
            <SplashPreviews />
        </div>
    );
}