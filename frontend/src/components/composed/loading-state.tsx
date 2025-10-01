import { Card, CardContent } from '@/components/primitives/ui/card';
import { Spinner } from '@/components/primitives/icons/spinner';

interface LoadingStateProps {
  message?: string;
}

export function LoadingState({ message = 'Loading...' }: LoadingStateProps) {
  return (
    <Card>
      <CardContent className="flex items-center gap-3 p-6">
        <Spinner className="h-5 w-5" />
        <p className="text-sm text-muted-foreground">{message}</p>
      </CardContent>
    </Card>
  );
}