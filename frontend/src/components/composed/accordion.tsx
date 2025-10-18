'use client';

import { useState, ReactNode } from 'react';
import { Card } from '@/components/primitives/ui/card';

interface AccordionItemProps {
  title: ReactNode;
  subtitle?: ReactNode;
  children: ReactNode;
  defaultOpen?: boolean;
  onToggle?: (isOpen: boolean) => void;
}

export function AccordionItem({
  title,
  subtitle,
  children,
  defaultOpen = false,
  onToggle
}: AccordionItemProps) {
  const [isOpen, setIsOpen] = useState(defaultOpen);

  const handleToggle = () => {
    const newState = !isOpen;
    setIsOpen(newState);
    onToggle?.(newState);
  };

  return (
    <Card className="overflow-hidden">
      <button
        onClick={handleToggle}
        className="w-full p-4 text-left hover:bg-accent/50 transition-colors"
      >
        <div className="flex items-start justify-between">
          <div className="flex-1 min-w-0">
            {title}
            {subtitle && <div className="mt-2">{subtitle}</div>}
          </div>
          <div className="text-2xl ml-4 shrink-0">
            {isOpen ? '−' : '+'}
          </div>
        </div>
      </button>

      {isOpen && (
        <div className="border-t bg-accent/10">
          {children}
        </div>
      )}
    </Card>
  );
}

interface AccordionProps {
  children: ReactNode;
}

export function Accordion({ children }: AccordionProps) {
  return <div className="space-y-3">{children}</div>;
}
