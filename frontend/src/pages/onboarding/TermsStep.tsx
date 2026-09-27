import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import OnboardingLayout from '../../components/OnboardingLayout';
import StepShell from '../../components/StepShell';
import Button from '../../components/Button';
import TextField from '../../components/TextField';
import Icon from '../../components/Icon';
import { cn } from '../../utils/cn';
import { useOnboardingStore } from '../../store/onboarding';
import { OnboardingService } from '../../services/onboarding';
import { ApiRequestError } from '../../services/auth';
import { RegistrationPayload } from '../../types/onboarding';
import { parseToE164 } from '../../utils/phone';

const STRENGTH_TESTS: Array<[RegExp, string]> = [
    [/^.{8,}$/, 'min length'],
    [/[a-z]/, 'lowercase letter'],
    [/[A-Z]/, 'uppercase letter'],
    [/[0-9]/, 'number'],
];

export default function TermsStep() {
    const navigate = useNavigate();
    const state = useOnboardingStore.getState();
    const [agree, setAgree] = useState(state.termsAccepted);
    const [password, setPassword] = useState('');
    const [confirm, setConfirm] = useState('');
    const [showPass, setShowPass] = useState(false);
    const [errors, setErrors] = useState<Record<string, string>>({});
    const [submitting, setSubmitting] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const missingChecks = STRENGTH_TESTS.filter(([re]) => !re.test(password)).length;
    const passwordValid = missingChecks === 0;
    const strength = password.length === 0 ? 0 : Math.max(1, 5 - missingChecks);

    const validate = (): boolean => {
        const errs: Record<string, string> = {};
        if (password.length < 8) errs.password = 'Use at least 8 characters.';
        else if (!passwordValid) errs.password = 'Add an uppercase letter, a lowercase letter and a number.';
        if (confirm !== password || !confirm) errs.confirm = 'Type the same password again.';
        if (!agree) errs.agree = 'You must accept the terms to create an account.';
        setErrors(errs);
        return Object.keys(errs).length === 0;
    };

    const submit = async () => {
        if (!validate()) return;
        useOnboardingStore.getState().acceptTerms();
        setSubmitting(true);
        setError(null);

        try {
            const current = useOnboardingStore.getState();
            const phoneE164 = parseToE164(current.phone, '');
            const payload: RegistrationPayload = {
                full_name: current.fullName,
                username: current.username,
                email: current.email,
                phone: phoneE164 ?? '',
                date_of_birth: current.dob,
                password,
                interests: current.interests,
                play_styles: current.playStyles,
                terms_accepted: true,
                region: current.region || undefined,
                age_group: current.ageRange ?? undefined,
                guardian_email: current.guardianEmail || undefined,
                guardian_name: current.guardianName || undefined,
                guardian_phone: parseToE164(current.guardianPhone, '') || undefined,
                verification_token: current.verificationToken || undefined,
            };

            const result = await OnboardingService.register(payload);
            useOnboardingStore.getState().setRegisterResult(result);
            useOnboardingStore.getState().completeStep('terms');
            navigate('/onboarding/creating', { replace: true });
        } catch (err) {
            setError(
                err instanceof ApiRequestError
                    ? err.message
                    : 'Something went wrong during registration. Check your details and try again.'
            );
            setSubmitting(false);
        }
    };

    return (
        <OnboardingLayout step="terms">
            <StepShell
                eyebrow="LAST STEP · PASSWORD WITH YOUR CONSENT"
                title="Keep it yours"
                subtitle={
                    <>
                        Create the password you’ll use to sign in to Vector Strike later.
                        Together with the checklist below, this unlocks your new account.
                    </>
                }
            >
                <form
                    className="vs-form"
                    onSubmit={(e) => {
                        e.preventDefault();
                        submit();
                    }}
                    noValidate
                >
                    <TextField
                        label="Password"
                        type={showPass ? 'text' : 'password'}
                        autoComplete="new-password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        error={errors.password ?? null}
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
                    <div className="vs-strength">
                        <div className="vs-strength__track">
                            {Array.from({ length: 5 }).map((_, i) => (
                                <span
                                    key={i}
                                    className="vs-strength__seg"
                                    data-on={i < strength}
                                    data-color={strength >= 4 ? 'strong' : strength >= 3 ? 'ok' : 'weak'}
                                />
                            ))}
                        </div>
                        <span className="vs-strength__label">
                            {password.length === 0
                                ? 'At least 8 characters'
                                : passwordValid
                                ? 'Nice — that’s solid.'
                                : `Add ${missingChecks} more: ${
                                      ['length', 'lowercase', 'uppercase', 'number']
                                          .filter((_, i) => !STRENGTH_TESTS[i][0].test(password))
                                          .join(', ')
                                  }`}
                        </span>
                    </div>
                    <div className="vs-passchecks" aria-label="Password requirements">
                        {STRENGTH_TESTS.map(([re, label]) => {
                            const ok = re.test(password);
                            return (
                                <span key={label} className={cn('vs-passcheck', ok && 'vs-passcheck--ok')}>
                                    {ok ? <Icon name="check" size={14} /> : <span className="vs-passcheck__dot" aria-hidden />}
                                    {label}
                                </span>
                            );
                        })}
                    </div>
                    <TextField
                        label="Confirm password"
                        type={showPass ? 'text' : 'password'}
                        autoComplete="new-password"
                        value={confirm}
                        onChange={(e) => setConfirm(e.target.value)}
                        error={errors.confirm ?? null}
                        icon="lock"
                    />

                    <ul className="vs-terms-list">
                        <li>
                            <Icon name="check" size={18} /> You must be old enough in your country
                            to create this type of account, or have a guardian authorising your use.
                        </li>
                        <li>
                            <Icon name="check" size={18} /> Your Vector ID will represent you in
                            leaderboards — never use real-name identifiers publicly.
                        </li>
                        <li>
                            <Icon name="check" size={18} /> You can delete your account and all data
                            at any time from the settings page.
                        </li>
                    </ul>

                    <label className="vs-check">
                        <input
                            type="checkbox"
                            checked={agree}
                            onChange={(e) => setAgree(e.target.checked)}
                        />
                        <span>
                            I have read and accept the <b>Terms of Service</b>, <b>Privacy Policy</b> and <b>Community Guidelines</b>.
                        </span>
                    </label>
                    {errors.agree && <div className="vs-field__error">{errors.agree}</div>}

                    {error && <div className="vs-alert vs-alert--error">{error}</div>}

                    <div className="vs-step__actions">
                        <Button
                            size="xl"
                            type="submit"
                            disabled={!agree}
                            loading={submitting}
                        >
                            Create my Vector Strike account
                        </Button>
                    </div>
                </form>
            </StepShell>
        </OnboardingLayout>
    );
}