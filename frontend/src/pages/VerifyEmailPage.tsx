import { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import Logo from '../components/Logo';
import Button from '../components/Button';
import Icon from '../components/Icon';
import { verifyEmailRequest, ApiRequestError } from '../services/auth';

type VerifyState = 'verifying' | 'done' | 'failed';

export default function VerifyEmailPage() {
    const navigate = useNavigate();
    const [params] = useSearchParams();
    const token = params.get('token') ?? '';
    const [state, setState] = useState<VerifyState>('verifying');
    const [message, setMessage] = useState('Confirming your email address…');
    const [email, setEmail] = useState('');

    useEffect(() => {
        let cancelled = false;
        (async () => {
            if (!token) {
                setState('failed');
                setMessage('This verification link is missing its token. Please request a new one.');
                return;
            }
            try {
                const result = await verifyEmailRequest(token);
                if (cancelled) return;
                setEmail(result.email);
                setState('done');
            } catch (err) {
                if (cancelled) return;
                setState('failed');
                setMessage(
                    err instanceof ApiRequestError
                        ? err.message
                        : 'We couldn’t verify that link. Please request a new one.'
                );
            }
        })();
        return () => {
            cancelled = true;
        };
    }, [token]);

    return (
        <div className="vs-auth">
            <img src="/assets/backgrounds/onboarding-bg.svg" alt="" className="vs-auth__bg" aria-hidden />
            <div className="vs-auth__grid" aria-hidden />
            <div className="vs-auth__panel">
                <div className="vs-auth__logo">
                    <Logo size="md" />
                </div>

                <div className="vs-auth__modal">
                    {state === 'verifying' && (
                        <>
                            <span className="vs-auth__success-icon vs-auth__success-icon--spin">
                                <Icon name="refresh" size={34} />
                            </span>
                            <h1 className="vs-auth__title">Verifying…</h1>
                            <p className="vs-auth__sub">{message}</p>
                        </>
                    )}

                    {state === 'done' && (
                        <>
                            <span className="vs-auth__success-icon">
                                <Icon name="check" size={34} />
                            </span>
                            <h1 className="vs-auth__title">Email confirmed</h1>
                            <p className="vs-auth__sub">
                                {email ? <>We’ve verified <strong>{email}</strong>.</> : 'We’ve verified your email.'}{' '}
                                Your account is now fully set up.
                            </p>
                            <div className="vs-auth__foot">
                                <Button size="lg" fullWidth onClick={() => navigate('/login')}>
                                    Continue
                                </Button>
                            </div>
                        </>
                    )}

                    {state === 'failed' && (
                        <>
                            <span className="vs-auth__success-icon vs-auth__success-icon--error">
                                <Icon name="alert" size={34} />
                            </span>
                            <h1 className="vs-auth__title">That link didn’t work</h1>
                            <p className="vs-auth__sub">{message}</p>
                            <div className="vs-auth__foot">
                                <Button size="lg" fullWidth onClick={() => navigate('/login')}>
                                    Go to sign in
                                </Button>
                            </div>
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