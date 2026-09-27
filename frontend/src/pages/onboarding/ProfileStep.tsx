import { useEffect, useMemo, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import OnboardingLayout from '../../components/OnboardingLayout';
import StepShell from '../../components/StepShell';
import TextField from '../../components/TextField';
import PhoneInput from '../../components/PhoneInput';
import Button from '../../components/Button';
import Icon from '../../components/Icon';
import { useOnboardingStore } from '../../store/onboarding';
import { OnboardingService } from '../../services/onboarding';
import { ApiRequestError } from '../../services/auth';
import { ageFromBirthdate, dateMax2026Plus, isFutureDate, validateEmail, validateUsername } from '../../utils/validators';

type FieldErrors = Record<string, string>;

export default function ProfileStep() {
    const navigate = useNavigate();
    const store = useOnboardingStore((s) => s);
    const { fullName, username, email, phone, dob, region } = store;

    const [e164Phone, setE164Phone] = useState<string | null>(null);
    const [useRegion, setUseRegion] = useState(false);
    const [errors, setErrors] = useState<FieldErrors>({});
    const [usernameStatus, setUsernameStatus] = useState<'idle' | 'checking' | 'available' | 'taken' | 'error'>('idle');
    const [usernameNote, setUsernameNote] = useState<string | null>(null);
    const [submitting, setSubmitting] = useState(false);
    const [serverError, setServerError] = useState<string | null>(null);
    const checkTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

    const maxDate = dateMax2026Plus();

    const sync = (patch: Partial<typeof store>) => store.set(patch);

    useEffect(() => {
        return () => {
            if (checkTimer.current) clearTimeout(checkTimer.current);
        };
    }, []);

    const validClient = useMemo(() => {
        const u = validateUsername(username);
        const e = validateEmail(email);
        return {
            name: fullName.trim().length >= 2,
            username: u.valid,
            usernameReason: u.reason,
            email: e,
            phone: !phone || !!e164Phone,
            dob: !!dob && !isFutureDate(dob),
            age: dob ? ageFromBirthdate(dob) : -1,
        };
    }, [fullName, username, email, phone, e164Phone, dob]);

    const runUsernameCheck = (value: string) => {
        if (checkTimer.current) clearTimeout(checkTimer.current);
        const v = value.trim();
        if (validateUsername(v).valid && v.length >= 3) {
            setUsernameStatus('checking');
            checkTimer.current = setTimeout(async () => {
                try {
                    const result = await OnboardingService.checkUsername(v);
                    if (result.available) {
                        setUsernameStatus('available');
                        setUsernameNote(result.message);
                    } else {
                        setUsernameStatus('taken');
                        setUsernameNote(result.message ?? 'That username is already taken.');
                        setErrors((prev) => ({ ...prev, username: 'Pick a different username.' }));
                    }
                } catch (err) {
                    setUsernameStatus('error');
                    setUsernameNote(err instanceof ApiRequestError ? err.message : 'Couldn’t check that right now.');
                }
            }, 420);
        }
    };

    const validate = (): boolean => {
        const next: FieldErrors = {};
        if (validClient.name) {}
        else next.full_name = 'Please use your real full name (at least 2 characters).';

        const u = validateUsername(username);
        if (!u.valid && username) next.username = u.reason ?? 'That username isn’t available in this form.';
        else if (!username) next.username = 'Choose a username.';
        else if (usernameStatus === 'taken') next.username = 'Pick a different username.';

        if (!email || !validClient.email) next.email = 'Enter a valid email address.';
        if (phone && !e164Phone) next.phone = 'Enter a valid phone number or remove it.';
        if (!dob) next.dob = 'Pick your date of birth.';
        else if (isFutureDate(dob)) next.dob = "That date hasn't happened yet!";
        else if (ageFromBirthdate(dob) < 5) next.dob = 'That seems too young — please have a parent/guardian check the details.';

        setErrors(next);
        return Object.keys(next).length === 0;
    };

    const age = validClient.age;

    const handleContinue = async () => {
        setServerError(null);
        if (!validate()) return;
        if (usernameStatus === 'checking') return;

        setSubmitting(true);
        try {
            const branch = await OnboardingService.checkAge(dob, useRegion ? region : '');
            store.setBranchInfo(branch);
            if (branch.branch === 'guardian') {
                navigate('/onboarding/guardian');
            } else if (branch.branch === 'verification') {
                navigate('/onboarding/verification');
            } else {
                navigate('/onboarding/terms');
            }
        } catch (err) {
            setServerError(err instanceof ApiRequestError ? err.message : 'We couldn’t verify your age right now.');
        } finally {
            setSubmitting(false);
        }
    };

    return (
        <OnboardingLayout step="profile">
            <StepShell
                eyebrow="STEP 5 · THE OFFICIAL STUFF"
                title="Create your arcade profile"
                subtitle="Your Vector ID is generated automatically — you just give us your details, and they stay private. You’ll set your password on the final consent step."
                wide
            >
                <form
                    onSubmit={(e) => {
                        e.preventDefault();
                        handleContinue();
                    }}
                    className="vs-form"
                    noValidate
                >
                    <div className="vs-form__grid">
                        <TextField
                            label="Full name"
                            placeholder="Your real name"
                            autoComplete="name"
                            value={fullName}
                            onChange={(e) => sync({ fullName: e.target.value })}
                            error={errors.full_name ?? null}
                            icon="user"
                        />
                        <TextField
                            label="Username"
                            placeholder="e.g. Nova_Runner"
                            autoComplete="username"
                            value={username}
                            onChange={(e) => {
                                sync({ username: e.target.value });
                                setUsernameStatus('idle');
                                setUsernameNote(null);
                                setErrors((prev) => {
                                    const n = { ...prev };
                                    delete n.username;
                                    return n;
                                });
                                runUsernameCheck(e.target.value);
                            }}
                            error={errors.username ?? null}
                            icon="target"
                            trailing={
                                usernameStatus === 'checking' ? (
                                    <span className="vs-field__trail vs-field__trail--checking">Checking…</span>
                                ) : usernameStatus === 'available' ? (
<span className="vs-field__trail vs-field__trail--ok">
                                            <Icon name="check" size={14} /> Available
                                        </span>
                                    ) : null
                            }
                            hint={
                                usernameStatus === 'available'
                                    ? usernameNote ?? 'This one is all yours.'
                                    : usernameStatus === 'taken' || usernameStatus === 'error'
                                    ? usernameNote
                                    : '3–30 characters, letters, numbers, “.” and “_”.'
                            }
                        />
                        <TextField
                            label="Email address"
                            type="email"
                            placeholder="you@example.com"
                            autoComplete="email"
                            value={email}
                            onChange={(e) => sync({ email: e.target.value })}
                            error={errors.email ?? null}
                            icon="globe"
                        />
                        <div className="vs-form__phone">
                            <PhoneInput
                                label="Phone (optional)"
                                value={phone}
                                onChange={(raw, e164, _country) => {
                                    sync({ phone: raw });
                                    setE164Phone(e164);
                                    setErrors((prev) => {
                                        const n = { ...prev };
                                        delete n.phone;
                                        return n;
                                    });
                                }}
                                error={errors.phone ?? null}
                            />
                        </div>
                        <TextField
                            label="Date of birth"
                            type="date"
                            max={maxDate}
                            value={dob}
                            onChange={(e) => sync({ dob: e.target.value })}
                            error={errors.dob ?? null}
                            icon="calendar"
                        />
                    </div>

                    <div className="vs-profile-note">
                        {age >= 0 ? (
                            <>
                                <Icon name="info" size={15} />
                                {age >= 18
                                    ? 'All good — you’re treated as an adult account at this age.'
                                    : `That makes you about ${age}. ${
                                          age >= 13
                                              ? 'You may need a parent/guardian blessing for full access.'
                                              : 'A parent or guardian will need to confirm your access.'
                                      }`}
                            </>
                        ) : (
                            <>
                                <Icon name="lock" size={15} />
                                Your details are used only to enforce age gates. They’re never shown on your public profile.
                            </>
                        )}
                    </div>

                    <div className="vs-check-row">
                        <label className="vs-check">
                            <input
                                type="checkbox"
                                checked={useRegion}
                                onChange={(e) => setUseRegion(e.target.checked)}
                            />
                            <span>My country has stricter rules I should mention</span>
                        </label>
                        {useRegion && (
                            <TextField
                                label="Country / region code"
                                placeholder="e.g. DE, FR, GB"
                                maxLength={2}
                                className="vs-profile-region"
                                value={region}
                                onChange={(e) => sync({ region: e.target.value.toUpperCase() })}
                            />
                        )}
                    </div>

                    {serverError && <div className="vs-alert vs-alert--error">{serverError}</div>}

                    <div className="vs-step__actions">
                        <Button
                            size="xl"
                            type="submit"
                            loading={submitting}
                            disabled={usernameStatus === 'checking'}
                        >
                            Continue
                        </Button>
                    </div>
                </form>
            </StepShell>
        </OnboardingLayout>
    );
}