import { Card, CardContent } from '@/components/primitives/ui/card';

interface EmptyStateProps {
  message: string;
  icon?: string;
}

export function EmptyState({ message, icon = '📭' }: EmptyStateProps) {
  return (
    <Card>
      <CardContent className="p-12 text-center">
        <p className="text-4xl mb-4">{icon}</p>
        <p className="text-muted-foreground">{message}</p>
      </CardContent>
    </Card>
  );
}