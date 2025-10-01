import { Card, CardContent } from '@/components/primitives/ui/card';
import { Button } from '@/components/primitives/ui/button';

interface ErrorStateProps {
  message: string;
  onRetry?: () => void;
}

export function ErrorState({ message, onRetry }: ErrorStateProps) {
  return (
    <Card className="border-destructive">
      <CardContent className="p-6 space-y-4">
        <div className="flex items-start gap-3">
          <span className="text-destructive text-xl">❌</span>
          <div className="flex-1">
            <p className="font-semibold text-destructive">Error</p>
            <p className="text-sm text-muted-foreground mt-1">{message}</p>
          </div>
        </div>
        {onRetry && (
          <Button onClick={onRetry} variant="outline" size="sm">
            Try Again
          </Button>
        )}
      </CardContent>
    </Card>
  );
}