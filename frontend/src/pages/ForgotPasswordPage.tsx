import { FormEvent, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Logo from '../components/Logo';
import Button from '../components/Button';
import TextField from '../components/TextField';
import Icon from '../components/Icon';
import { forgotPasswordRequest, ApiRequestError } from '../services/auth';

export default function ForgotPasswordPage() {
    const navigate = useNavigate();
    const [identifier, setIdentifier] = useState('');
    const [sent, setSent] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [submitting, setSubmitting] = useState(false);

    const submit = async (e: FormEvent) => {
        e.preventDefault();
        if (!identifier.trim()) {
            setError('Enter your username, email or Vector ID.');
            return;
        }
        setSubmitting(true);
        setError(null);
        try {
            await forgotPasswordRequest(identifier.trim());
            setSent(true);
        } catch (err) {
            setError(
                err instanceof ApiRequestError ? err.message : 'Something went wrong. Please try again.'
            );
        } finally {
            setSubmitting(false);
        }
    };

    return (
        <div className="vs-auth">
            <img src="/assets/backgrounds/onboarding-bg.svg" alt="" className="vs-auth__bg" aria-hidden />
            <div className="vs-auth__grid" aria-hidden />
            <div className="vs-auth__panel">
                <div className="vs-auth__logo">
                    <Logo size="md" />
                </div>

                <div className="vs-auth__topbar">
                    <button type="button" className="vs-back-link" onClick={() => navigate('/login')}>
                        <Icon name="chevron-left" size={15} /> Back
                    </button>
                </div>

                <div className="vs-auth__modal">
                    {sent ? (
                        <>
                            <h1 className="vs-auth__title">Check your inbox</h1>
                            <p className="vs-auth__sub">
                                If that account exists, we’ve sent a reset link. The link is single-use
                                and expires after a few hours.
                            </p>
                            <div className="vs-auth__foot">
                                <Button size="lg" fullWidth onClick={() => navigate('/login')}>
                                    Back to sign in
                                </Button>
                            </div>
                        </>
                    ) : (
                        <>
                            <h1 className="vs-auth__title">Reset your password</h1>
                            <p className="vs-auth__sub">
                                Tell us your username, email or Vector ID and we’ll send you a recovery link.
                            </p>
                            <form className="vs-form" onSubmit={submit} noValidate>
                                <TextField
                                    label="Username, email or Vector ID"
                                    placeholder="Nova_Runner"
                                    autoComplete="username"
                                    value={identifier}
                                    onChange={(e) => setIdentifier(e.target.value)}
                                    icon="user"
                                />
                                {error && <div className="vs-alert vs-alert--error">{error}</div>}
                                <div className="vs-auth__foot">
                                    <Button size="lg" type="submit" fullWidth loading={submitting}>
                                        Send reset link
                                    </Button>
                                    <p className="vs-auth__switch">
                                        Changed your mind?{' '}
                                        <button type="button" className="vs-link" onClick={() => navigate('/login')}>
                                            Back to sign in
                                        </button>
                                    </p>
                                </div>
                            </form>
                        </>
                    )}
                </div>

                <p className="vs-auth__legal">
                    By signing in you agree to Vector Strike’s Terms & Privacy Policy.
                </p>
            </div>
        </div>
    );
}