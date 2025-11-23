import { ReactNode } from 'react';

interface CardProps {
    children: ReactNode;
    className?: string;
    hover?: boolean;
}

export default function Card({ children, className = '', hover = false }: CardProps) {
    return (
        <div
            className={`
        bg-gradient-to-br from-gray-800 to-gray-900 
        rounded-xl shadow-xl border border-gray-700
        ${hover ? 'hover:shadow-2xl hover:border-gray-600 transition-all duration-300 hover:-translate-y-1' : ''}
        ${className}
      `}
        >
            {children}
        </div>
    );
}

export function CardHeader({ children, className = '' }: { children: ReactNode; className?: string }) {
    return <div className={`p-6 border-b border-gray-700 ${className}`}>{children}</div>;
}

export function CardBody({ children, className = '' }: { children: ReactNode; className?: string }) {
    return <div className={`p-6 ${className}`}>{children}</div>;
}

export function CardFooter({ children, className = '' }: { children: ReactNode; className?: string }) {
    return <div className={`p-6 border-t border-gray-700 ${className}`}>{children}</div>;
}
