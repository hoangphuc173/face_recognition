export function LoadingSpinner({ size = 'md' }: { size?: 'sm' | 'md' | 'lg' }) {
    const sizes = {
        sm: 'h-4 w-4',
        md: 'h-8 w-8',
        lg: 'h-12 w-12',
    };

    return (
        <div className="flex items-center justify-center">
            <svg
                className={`animate-spin ${sizes[size]} text-blue-500`}
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
            >
                <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                ></circle>
                <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                ></path>
            </svg>
        </div>
    );
}

export function SkeletonCard() {
    return (
        <div className="bg-gray-800 rounded-xl p-6 animate-pulse">
            <div className="h-6 bg-gray-700 rounded w-3/4 mb-4"></div>
            <div className="h-4 bg-gray-700 rounded w-1/2 mb-2"></div>
            <div className="h-4 bg-gray-700 rounded w-2/3"></div>
        </div>
    );
}

export function SkeletonTable({ rows = 5 }: { rows?: number }) {
    return (
        <div className="bg-gray-800 rounded-xl overflow-hidden">
            <div className="p-4 border-b border-gray-700 animate-pulse">
                <div className="h-6 bg-gray-700 rounded w-1/4"></div>
            </div>
            <div className="divide-y divide-gray-700">
                {Array.from({ length: rows }).map((_, i) => (
                    <div key={i} className="p-4 animate-pulse flex gap-4">
                        <div className="h-4 bg-gray-700 rounded flex-1"></div>
                        <div className="h-4 bg-gray-700 rounded flex-1"></div>
                        <div className="h-4 bg-gray-700 rounded w-20"></div>
                    </div>
                ))}
            </div>
        </div>
    );
}
