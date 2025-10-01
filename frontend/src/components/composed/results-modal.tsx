import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '@/components/primitives/ui/dialog';
import { Button } from '@/components/primitives/ui/button';

interface ResultsModalProps {
  open: boolean;
  onClose: () => void;
  title: string;
  description?: string;
  result: string;
  onCopy?: () => void;
}

export function ResultsModal({ open, onClose, title, description, result, onCopy }: ResultsModalProps) {
  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{title}</DialogTitle>
          {description && <DialogDescription>{description}</DialogDescription>}
        </DialogHeader>

        <div className="my-4 p-4 bg-muted rounded-md">
          <pre className="whitespace-pre-wrap text-sm">{result}</pre>
        </div>

        <DialogFooter>
          {onCopy && (
            <Button onClick={onCopy} variant="default">
              📋 Copy to Clipboard
            </Button>
          )}
          <Button onClick={onClose} variant="outline">
            Close
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}