import { useNavigate } from 'react-router-dom';
import OnboardingLayout from '../../components/OnboardingLayout';
import StepShell from '../../components/StepShell';
import Button from '../../components/Button';
import SplashParticles from '../../components/SplashParticles';
import { useOnboardingStore } from '../../store/onboarding';

export default function WelcomeStep() {
    const navigate = useNavigate();
    const set = useOnboardingStore((s) => s.set);

    return (
        <OnboardingLayout step="welcome" showProgress={false} onBack={() => navigate('/auth-choice')}>
            <div className="vs-welcome">
                <SplashParticles active />
                <div className="vs-welcome__hero">
                    <img
                        src="/assets/onboarding/welcome.svg"
                        alt=""
                        className="vs-welcome__art"
                        draggable={false}
                    />
                </div>
                <StepShell
                    eyebrow="VECTOR STRIKE · ONBOARDING"
                    title="Ready to make your mark?"
                    subtitle={
                        <>
                            Vector Strike is a whole galaxy of brain-training challenges, puzzles
                            and head-to-head competitions. It only takes a few minutes to set up
                            your arcade profile.
                        </>
                    }
                >
                    <div className="vs-step__actions">
                        <Button
                            size="xl"
                            onClick={() => {
                                set({ step: 'age' });
                                navigate('/onboarding/age');
                            }}
                        >
                            Let’s get started
                        </Button>
                        <Button
                            variant="ghost"
                            size="lg"
                            onClick={() => navigate('/login')}
                        >
                            I already have an account
                        </Button>
                    </div>
                </StepShell>
            </div>
        </OnboardingLayout>
    );
}