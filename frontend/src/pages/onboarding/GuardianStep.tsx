import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import OnboardingLayout from '../../components/OnboardingLayout';
import StepShell from '../../components/StepShell';
import TextField from '../../components/TextField';
import PhoneInput from '../../components/PhoneInput';
import Button from '../../components/Button';
import Icon from '../../components/Icon';
import { useOnboardingStore } from '../../store/onboarding';
import { validateEmail } from '../../utils/validators';

export default function GuardianStep() {
    const navigate = useNavigate();
    const store = useOnboardingStore((s) => s);
    const bucket = useOnboardingStore((s) => s.branchInfo);
    const [guardianName, setGuardianName] = useState(store.guardianName ?? '');
    const [guardianEmail, setGuardianEmail] = useState(store.guardianEmail ?? '');
    const [guardianPhone, setGuardianPhone] = useState(store.guardianPhone ?? '');
    const [e164Phone, setE164Phone] = useState<string | null>(null);
    const [errors, setErrors] = useState<Record<string, string>>({});

    const threshold = bucket?.guardian_threshold ?? 17;

    const next = () => {
        const errs: Record<string, string> = {};
        if (!guardianName.trim()) errs.name = 'Tell us their name so we can address them properly.';
        if (!validateEmail(guardianEmail)) errs.email = 'A valid email is the fastest way to reach them.';
        if (guardianPhone && !e164Phone) errs.phone = 'That phone number doesn’t look valid.';
        setErrors(errs);
        if (Object.keys(errs).length) return;

        store.set({
            guardianName: guardianName.trim(),
            guardianEmail: guardianEmail.trim().toLowerCase(),
            guardianPhone: guardianPhone.trim(),
        });
        navigate('/onboarding/terms');
    };

    return (
        <OnboardingLayout step="guardian">
            <StepShell
                eyebrow="PARENT / GUARDIAN GATE"
                title="Quick heads-up for your grown-up"
                subtitle={`Because your profile says you’re under ${threshold}, a parent or guardian needs to be there for your account. They don’t pay for anything — we just need their consent contact.`}
            >
                <div className="vs-note vs-note--info">
                    <Icon name="user" size={16} />
                    <p>
                        We typically reach consent by email first, then follow your region’s rules.
                        This person can manage permissions on your account anytime.
                    </p>
                </div>

                <form
                    className="vs-form"
                    onSubmit={(e) => {
                        e.preventDefault();
                        next();
                    }}
                    noValidate
                >
                    <TextField
                        label="Parent / guardian name"
                        placeholder="Their full name"
                        autoComplete="name"
                        value={guardianName}
                        onChange={(e) => setGuardianName(e.target.value)}
                        error={errors.name ?? null}
                        icon="user"
                    />
                    <TextField
                        label="Their email"
                        type="email"
                        placeholder="parent@example.com"
                        autoComplete="email"
                        value={guardianEmail}
                        onChange={(e) => setGuardianEmail(e.target.value)}
                        error={errors.email ?? null}
                        icon="globe"
                    />
                    <PhoneInput
                        label="Their phone (optional)"
                        value={guardianPhone}
                        onChange={(raw, e164) => {
                            setGuardianPhone(raw);
                            setE164Phone(e164);
                        }}
                        error={errors.phone ?? null}
                    />
                    <div className="vs-step__actions">
                        <Button size="xl" type="submit">
                            Looks right — continue
                        </Button>
                        <Button
                            variant="ghost"
                            size="lg"
                            onClick={() => navigate('/onboarding/profile')}
                        >
                            Back
                        </Button>
                    </div>
                </form>
            </StepShell>
        </OnboardingLayout>
    );
}