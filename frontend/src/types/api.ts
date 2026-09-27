export interface ApiErrorBody {
    error: {
        code: string;
        message: string;
        fields: Record<string, unknown>;
    };
}

export interface ApiResult<T> {
    ok: boolean;
    status: number;
    data?: T;
    error?: {
        code: string;
        message: string;
        fields: Record<string, unknown>;
    };
}

export class NetworkError extends Error {
    cause?: Error;
    constructor(message: string, cause?: Error) {
        super(message);
        this.name = 'NetworkError';
        this.cause = cause;
    }
}