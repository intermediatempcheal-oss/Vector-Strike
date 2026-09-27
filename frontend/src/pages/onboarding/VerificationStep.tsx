import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import OnboardingLayout from '../../components/OnboardingLayout';
import StepShell from '../../components/StepShell';
import Button from '../../components/Button';
import VerificationDropzone, { DocumentPreview, PendingDocument } from '../../components/VerificationDropzone';
import Icon from '../../components/Icon';
import { useOnboardingStore } from '../../store/onboarding';
import { OnboardingService } from '../../services/onboarding';
import { ApiRequestError } from '../../services/auth';

export default function VerificationStep() {
    const navigate = useNavigate();
    const region = useOnboardingStore((s) => s.region);
    const [file, setFile] = useState<PendingDocument | null>(null);
    const [uploading, setUploading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const handleUpload = async () => {
        if (!file) return;
        setUploading(true);
        setError(null);
        try {
            const result = await OnboardingService.uploadDocument(file.file, region);
            useOnboardingStore.getState().set({ verificationToken: result.verification_token });
            navigate('/onboarding/terms');
        } catch (err) {
            setError(
                err instanceof ApiRequestError
                    ? err.message
                    : "We couldn’t upload that document right now. Try a different file or connection."
            );
        } finally {
            setUploading(false);
        }
    };

    return (
        <OnboardingLayout step="verification">
            <StepShell
                eyebrow="VERIFICATION STEP · QUICK AND PRIVATE"
                title="Upload a photo or scan"
                subtitle="A government-issued ID, passport or driver’s license lets us confirm your age. This file is encrypted in transit and reviewed in one shot."
                wide
            >
                <div className="vs-note vs-note--info">
                    <Icon name="shield" size={16} />
                    <p>
                        After upload, your document never leaves Vector Strike’s secure infrastructure.
                        You can delete it anytime from your account settings later.
                    </p>
                </div>

                {file ? (
                    <DocumentPreview
                        doc={file}
                        onReplace={() => {
                            setFile(null);
                            setError(null);
                        }}
                        onRemove={() => {
                            setFile(null);
                            setError(null);
                        }}
                    />
                ) : (
                    <VerificationDropzone
                        onFile={setFile}
                        clearError={() => setError(null)}
                        sublabel="A clear photo, scan or PDF of an ID document"
                    />
                )}

                {error && <div className="vs-alert vs-alert--error">{error}</div>}

                <div className="vs-step__actions">
                    <Button
                        size="xl"
                        disabled={!file}
                        loading={uploading}
                        onClick={handleUpload}
                    >
                        Upload and continue
                    </Button>
                    <Button
                        variant="ghost"
                        size="lg"
                        onClick={() => navigate('/onboarding/profile')}
                    >
                        Back
                    </Button>
                </div>
            </StepShell>
        </OnboardingLayout>
    );
}