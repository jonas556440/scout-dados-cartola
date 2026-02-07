import { HelpCircle } from "lucide-react";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";

interface HelpItem {
  term: string;
  definition: string;
}

interface HelpSectionProps {
  title: string;
  items: HelpItem[];
  className?: string;
}

export function HelpSection({ title, items, className }: HelpSectionProps) {
  return (
    <Accordion type="single" collapsible className={`w-full ${className || ''}`}>
      <AccordionItem value="help" className="border rounded-lg px-4">
        <AccordionTrigger className="text-sm hover:no-underline">
          <div className="flex items-center gap-2">
            <HelpCircle className="w-4 h-4 text-primary" />
            <span className="font-semibold">{title}</span>
          </div>
        </AccordionTrigger>
        <AccordionContent>
          <dl className="space-y-4 text-sm pb-2">
            {items.map((item, index) => (
              <div key={index} className="space-y-1">
                <dt className="font-semibold text-foreground">{item.term}</dt>
                <dd className="text-muted-foreground leading-relaxed">{item.definition}</dd>
              </div>
            ))}
          </dl>
        </AccordionContent>
      </AccordionItem>
    </Accordion>
  );
}
