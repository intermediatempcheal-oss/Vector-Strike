import { useNavigate } from 'react-router-dom';
import Logo from '../components/Logo';
import Button from '../components/Button';

export default function AuthChoicePage() {
    const navigate = useNavigate();

    return (
        <div className="vs-auth">
            <img src="/assets/backgrounds/onboarding-bg.svg" alt="" className="vs-auth__bg" aria-hidden />
            <div className="vs-auth__grid" aria-hidden />
            <div className="vs-auth__panel">
                <div className="vs-auth__logo">
                    <Logo size="md" />
                </div>

                <div className="vs-auth__modal vs-auth__modal--choice">
                    <h1 className="vs-auth__title">Welcome to Vector Strike</h1>
                    <p className="vs-auth__sub">
                        Sign in to pick up where you left off, or create a brand-new arcade profile.
                    </p>

                    <Button size="xl" fullWidth icon="play" onClick={() => navigate('/login')}>
                        Sign in
                    </Button>
                    <Button size="lg" variant="outline" fullWidth icon="rocket" onClick={() => navigate('/onboarding/welcome')}>
                        Create an account
                    </Button>
                </div>

                <p className="vs-auth__legal">
                    By continuing you agree to Vector Strike’s Terms & Privacy Policy.
                </p>
            </div>
        </div>
    );
}
