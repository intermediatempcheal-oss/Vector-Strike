import { FormEvent, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Logo from '../components/Logo';
import Button from '../components/Button';
import TextField from '../components/TextField';
import Icon from '../components/Icon';
import { useAuthStore } from '../store/auth';
import { ApiRequestError } from '../services/auth';

export default function LoginPage() {
    const navigate = useNavigate();
    const { authenticated, onboarding_complete } = useAuthStore();
    const login = useAuthStore((s) => s.login);

    const [identifier, setIdentifier] = useState('');
    const [password, setPassword] = useState('');
    const [showPass, setShowPass] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [submitting, setSubmitting] = useState(false);

    useEffect(() => {
        if (authenticated) {
            navigate(onboarding_complete ? '/home' : '/onboarding/welcome', { replace: true });
        }
    }, [authenticated, onboarding_complete, navigate]);

    const submit = async (e: FormEvent) => {
        e.preventDefault();
        if (!identifier.trim() || !password) {
            setError('Enter both your username/email and password.');
            return;
        }
        setSubmitting(true);
        setError(null);
        try {
            await login(identifier.trim(), password);
        } catch (err) {
            setError(
                err instanceof ApiRequestError && err.status !== 401
                    ? err.message
                    : "We couldn't sign you in with those details."
            );
        } finally {
            setSubmitting(false);
        }
    };

    return (
        <div className="vs-auth">
            <img
                src="/assets/backgrounds/onboarding-bg.svg"
                alt=""
                className="vs-auth__bg"
                aria-hidden
            />
            <div className="vs-auth__grid" aria-hidden />
            <div className="vs-auth__panel">
                <div className="vs-auth__logo">
                    <Logo size="md" />
                </div>

                <div className="vs-auth__modal">
                    <div className="vs-auth__topbar">
                        <button type="button" className="vs-back-link" onClick={() => navigate('/auth-choice')}>
                            <Icon name="chevron-left" size={15} />
                            Back
                        </button>
                    </div>

                    <h1 className="vs-auth__title">Welcome back</h1>
                    <p className="vs-auth__sub">
                        Sign in with your username or email to get back into the arcade.
                    </p>

                    <form className="vs-form" onSubmit={submit} noValidate>
                        <TextField
                            label="Username or email"
                            placeholder="Nova_Runner"
                            autoComplete="username"
                            value={identifier}
                            onChange={(e) => setIdentifier(e.target.value)}
                            icon="user"
                        />
                        <TextField
                            label="Password"
                            type={showPass ? 'text' : 'password'}
                            autoComplete="current-password"
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
                        {error && <div className="vs-alert vs-alert--error">{error}</div>}

                        <div className="vs-auth__forgot">
                            <button
                                type="button"
                                className="vs-link"
                                onClick={() => navigate('/forgot-password')}
                            >
                                Forgot password?
                            </button>
                        </div>

                        <div className="vs-auth__foot">
                            <Button size="lg" type="submit" fullWidth loading={submitting}>
                                Sign in
                            </Button>
                            <p className="vs-auth__switch">
                                New here?{' '}
                                <button
                                    type="button"
                                    className="vs-link"
                                    onClick={() => navigate('/onboarding/welcome')}
                                >
                                    Create an account
                                </button>
                            </p>
                        </div>
                    </form>
                </div>

                <p className="vs-auth__legal">
                    By signing in you agree to Vector Strike’s Terms & Privacy Policy.
                </p>
            </div>
        </div>
    );
}