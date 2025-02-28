import { Loader2 } from 'lucide-react';

interface LoadingSpinnerProps {
  text?: string;
  className?: string;
}

export function LoadingSpinner({ text = 'Loading...', className = '' }: LoadingSpinnerProps) {
  return (
    <div className={`flex flex-col items-center justify-center p-8 ${className}`}>
      <Loader2 className="h-8 w-8 animate-spin text-primary mb-2" />
      <p className="text-sm text-muted-foreground">{text}</p>
    </div>
  );
} 