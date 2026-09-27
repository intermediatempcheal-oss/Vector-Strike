import { DragEvent, useCallback, useRef, useState } from 'react';
import { cn } from '../utils/cn';
import Icon from './Icon';
import Button from './Button';

export interface PendingDocument {
    file: File;
    previewUrl: string | null;
    sizeLabel: string;
}

interface VerificationDropzoneProps {
    onFile: (doc: PendingDocument) => void;
    clearError: () => void;
    sublabel?: string;
}

const ACCEPT = 'image/jpeg,image/png,application/pdf,.jpg,.jpeg,.png,.pdf';
const MAX_MB = 10;

export default function VerificationDropzone({ onFile, clearError, sublabel }: VerificationDropzoneProps) {
    const inputRef = useRef<HTMLInputElement>(null);
    const [dragOver, setDragOver] = useState(false);
    const [rejecting, setRejecting] = useState(false);
    const [rejectMsg, setRejectMsg] = useState<string | null>(null);

    const validate = useCallback(
        (file: File): string | null => {
            if (!ACCEPT.split(',').includes(file.type) && !/\.(jpe?g|png|pdf)$/i.test(file.name)) {
                return 'We accept JPG, PNG or PDF documents.';
            }
            if (file.size > MAX_MB * 1024 * 1024) {
                return `Keep the document under ${MAX_MB} MB.`;
            }
            return null;
        },
        []
    );

    const handleFile = useCallback(
        (file: File) => {
            const error = validate(file);
            if (error) {
                setRejecting(true);
                setRejectMsg(error);
                setTimeout(() => setRejecting(false), 2600);
                return;
            }
            setRejectMsg(null);
            setRejecting(false);
            const previewUrl = file.type.startsWith('image/')
                ? URL.createObjectURL(file)
                : null;
            const sizeLabel =
                file.size > 1024 * 1024
                    ? `${(file.size / (1024 * 1024)).toFixed(1)} MB`
                    : `${Math.max(1, Math.round(file.size / 1024))} KB`;
            onFile({ file, previewUrl, sizeLabel });
            clearError();
        },
        [validate, onFile, clearError]
    );

    const onDrop = useCallback(
        (e: DragEvent) => {
            e.preventDefault();
            setDragOver(false);
            const file = e.dataTransfer.files?.[0];
            if (file) handleFile(file);
        },
        [handleFile]
    );

    return (
        <div>
            <input
                ref={inputRef}
                type="file"
                accept={ACCEPT}
                className="vs-visually-hidden"
                onChange={(e) => {
                    const file = e.target.files?.[0];
                    if (file) handleFile(file);
                    e.target.value = '';
                }}
            />
            <button
                type="button"
                className={cn(
                    'vs-dropzone',
                    dragOver && 'vs-dropzone--drag',
                    rejecting && 'vs-dropzone--reject'
                )}
                onClick={() => inputRef.current?.click()}
                onDragOver={(e) => {
                    e.preventDefault();
                    setDragOver(true);
                }}
                onDragLeave={() => setDragOver(false)}
                onDrop={onDrop}
            >
                <span className="vs-dropzone__icon">
                    <Icon name={rejecting ? 'alert' : 'upload'} size={26} />
                </span>
                <span className="vs-dropzone__title">
                    {rejecting ? 'Hmm, that didn’t work' : 'Tap to upload or drag it here'}
                </span>
                <span className="vs-dropzone__sub">
                    {rejectMsg ?? (sublabel ?? 'JPG, PNG or PDF · up to 10 MB')}
                </span>
            </button>
        </div>
    );
}

export function DocumentPreview({ doc, onReplace, onRemove }: {
    doc: PendingDocument;
    onReplace: () => void;
    onRemove: () => void;
}) {
    return (
        <div className="vs-doc-preview">
            {doc.previewUrl ? (
                <img src={doc.previewUrl} alt="Document preview" className="vs-doc-preview__img" />
            ) : (
                <div className="vs-doc-preview__file">
                    <Icon name="shield" size={22} />
                    <span>{doc.file.name}</span>
                </div>
            )}
            <div className="vs-doc-preview__meta">
                <span className="vs-doc-preview__name">{doc.file.name}</span>
                <span className="vs-doc-preview__size">{doc.sizeLabel}</span>
            </div>
            <div className="vs-doc-preview__actions">
                <Button variant="ghost" size="sm" onClick={onReplace}>
                    Replace
                </Button>
                <Button variant="ghost" size="sm" onClick={onRemove}>
                    Remove
                </Button>
            </div>
        </div>
    );
}