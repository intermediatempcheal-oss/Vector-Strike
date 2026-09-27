import { FormEvent, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import Logo from '../components/Logo';
import Button from '../components/Button';
import TextField from '../components/TextField';
import Icon from '../components/Icon';
import { resetPasswordRequest, ApiRequestError } from '../services/auth';

export default function ResetPasswordPage() {
    const navigate = useNavigate();
    const [params] = useSearchParams();
    const token = params.get('token') ?? '';

    const [password, setPassword] = useState('');
    const [confirm, setConfirm] = useState('');
    const [showPass, setShowPass] = useState(false);
    const [done, setDone] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [submitting, setSubmitting] = useState(false);

    const submit = async (e: FormEvent) => {
        e.preventDefault();
        if (!token) {
            setError('This reset link is missing its token. Request a new one.');
            return;
        }
        if (password.length < 8) {
            setError('Choose a password of at least 8 characters.');
            return;
        }
        if (password !== confirm) {
            setError('Those passwords don’t match.');
            return;
        }
        setSubmitting(true);
        setError(null);
        try {
            await resetPasswordRequest(token, password);
            setDone(true);
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
                    {done ? (
                        <>
                            <span className="vs-auth__success-icon">
                                <Icon name="check" size={34} />
                            </span>
                            <h1 className="vs-auth__title">Password updated</h1>
                            <p className="vs-auth__sub">
                                Your password has been changed. Sign in below with your new one.
                            </p>
                            <div className="vs-auth__foot">
                                <Button size="lg" fullWidth onClick={() => navigate('/login')}>
                                    Sign in
                                </Button>
                            </div>
                        </>
                    ) : (
                        <>
                            <h1 className="vs-auth__title">Choose a new password</h1>
                            <p className="vs-auth__sub">
                                Pick something strong — your old password won’t work after this.
                            </p>
                            <form className="vs-form" onSubmit={submit} noValidate>
                                <TextField
                                    label="New password"
                                    type={showPass ? 'text' : 'password'}
                                    autoComplete="new-password"
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    icon="lock"
                                    trailing={
                                        <button
                                            type="button"
                                            className="vs-field__eye"
                                            onClick={() => setShowPass((v) => !v)}
                                            aria-label={showPass ? 'Hide password' : 'Show password'}
                                        >
                                            <Icon name={showPass ? 'eye-off' : 'eye'} size={16} />
                                        </button>
                                    }
                                />
                                <TextField
                                    label="Confirm new password"
                                    type={showPass ? 'text' : 'password'}
                                    autoComplete="new-password"
                                    value={confirm}
                                    onChange={(e) => setConfirm(e.target.value)}
                                    icon="check"
                                />
                                {error && <div className="vs-alert vs-alert--error">{error}</div>}
                                <div className="vs-auth__foot">
                                    <Button size="lg" type="submit" fullWidth loading={submitting}>
                                        Update password
                                    </Button>
                                    <p className="vs-auth__switch">
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