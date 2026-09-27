import { useNavigate } from 'react-router-dom';
import Button from '../components/Button';
import Logo from '../components/Logo';

export default function LandingPage() {
    const navigate = useNavigate();

    return (
        <main className="vs-app vs-landing">
            <div className="vs-landing__shell vs-glass">
                <div className="vs-landing__brand">
                    <Logo size="lg" />
                </div>

                <div className="vs-landing__content">
                    <p className="vs-landing__eyebrow">PLAY · LEARN · COMPETE</p>
                    <h1>Welcome to Vector Strike</h1>
                    <p className="vs-landing__subtitle">
                        Choose your next move and jump into a world of games, skills, and
                        progression.
                    </p>

                    <div className="vs-landing__actions">
                        <Button size="xl" onClick={() => navigate('/onboarding/welcome')}>
                            Create account
                        </Button>
                        <Button variant="outline" size="lg" onClick={() => navigate('/login')}>
                            Sign in
                        </Button>
                        <Button variant="ghost" size="lg" onClick={() => navigate('/home')}>
                            Explore demo
                        </Button>
                    </div>
                </div>
            </div>
        </main>
    );
}
