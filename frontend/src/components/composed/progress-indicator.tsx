'use client';

interface ProgressIndicatorProps {
  progress: number;
  message: string;
  title?: string;
  hint?: string;
}

export function ProgressIndicator({
  progress,
  message,
  title = 'In progress...',
  hint
}: ProgressIndicatorProps) {
  return (
    <div className="mt-4 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-md border-2 border-blue-500">
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <p className="font-medium text-sm text-blue-900 dark:text-blue-100">{title}</p>
          <span className="text-lg font-bold text-blue-900 dark:text-blue-100">{progress}%</span>
        </div>

        {/* Progress bar */}
        <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-4 overflow-hidden border border-gray-300">
          <div
            className="bg-blue-600 h-4 transition-all duration-300 ease-out"
            style={{ width: `${progress}%`, minWidth: progress > 0 ? '20px' : '0' }}
          />
        </div>

        {/* Current step message */}
        <p className="text-sm font-medium text-blue-900 dark:text-blue-100">
          {message || 'Initializing...'}
        </p>

        {/* Optional hint */}
        {hint && (
          <p className="text-xs text-muted-foreground">{hint}</p>
        )}
      </div>
    </div>
  );
}
