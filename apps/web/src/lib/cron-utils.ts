// Cron expression parser and human-readable description generator
// Using cron-parser and cronstrue libraries for accurate calculations

import { CronExpressionParser } from 'cron-parser';
import cronstrue from 'cronstrue';

export interface CronField {
  second?: string;
  minute: string;
  hour: string;
  dayOfMonth: string;
  month: string;
  dayOfWeek: string;
}

export interface CronDescription {
  description: string;
  nextRuns: string[];
  isValid: boolean;
  error?: string;
}

// Parse cron expression into fields
export function parseCronExpression(cron: string): { fields: CronField | null; error?: string } {
  const trimmed = cron.trim();
  const parts = trimmed.split(/\s+/);

  // Handle both 5-field (minute hour day month weekday) and 6-field (second minute hour day month weekday)
  if (parts.length === 5) {
    return {
      fields: {
        minute: parts[0],
        hour: parts[1],
        dayOfMonth: parts[2],
        month: parts[3],
        dayOfWeek: parts[4],
      },
    };
  } else if (parts.length === 6) {
    return {
      fields: {
        second: parts[0],
        minute: parts[1],
        hour: parts[2],
        dayOfMonth: parts[3],
        month: parts[4],
        dayOfWeek: parts[5],
      },
    };
  }

  return {
    fields: null,
    error:
      'Cron expression must have exactly 5 fields (minute hour day month weekday) or 6 fields (second minute hour day month weekday)',
  };
}

// Validate cron expression using cron-parser
export function validateCronExpression(cron: string): { isValid: boolean; error?: string } {
  try {
    // cron-parser supports 6 fields with seconds option
    const hasSeconds = cron.trim().split(/\s+/).length === 6;
    CronExpressionParser.parse(cron, {
      ...(hasSeconds && { seconds: true }),
    });
    return { isValid: true };
  } catch (error: any) {
    return {
      isValid: false,
      error: error?.message || 'Invalid cron expression',
    };
  }
}

// Generate human-readable description using cronstrue
export function describeCronExpression(cron: string): CronDescription {
  const validation = validateCronExpression(cron);
  if (!validation.isValid) {
    return {
      description: '',
      nextRuns: [],
      isValid: false,
      error: validation.error,
    };
  }

  try {
    // Check if it's a 6-field expression
    const parts = cron.trim().split(/\s+/);
    const hasSeconds = parts.length === 6;

    // Generate human-readable description
    let description: string;
    try {
      if (hasSeconds) {
        const secondField = parts[0];
        const fiveFieldCron = parts.slice(1).join(' ');

        // Handle second-level patterns
        if (secondField === '*') {
          // Every second
          description = 'Every second';
        } else if (secondField.startsWith('*/')) {
          // Every N seconds
          const interval = secondField.substring(2);
          const fiveFieldDesc = cronstrue.toString(fiveFieldCron);
          // If the 5-field part is also "every minute", just say "every N seconds"
          if (fiveFieldDesc.toLowerCase().includes('every minute')) {
            description = `Every ${interval} second${interval !== '1' ? 's' : ''}`;
          } else {
            description = `Every ${interval} second${interval !== '1' ? 's' : ''}, ${fiveFieldDesc.toLowerCase()}`;
          }
        } else if (secondField === '0') {
          // At second 0 (every minute, hour, etc.)
          description = cronstrue.toString(fiveFieldCron);
        } else {
          // Specific second value
          const fiveFieldDesc = cronstrue.toString(fiveFieldCron);
          description = `${fiveFieldDesc} at second ${secondField}`;
        }
      } else {
        description = cronstrue.toString(cron);
      }
    } catch (e) {
      // Fallback description
      description = 'Valid cron expression';
    }

    // Generate next run times
    const nextRuns = generateNextRuns(cron, hasSeconds);

    return {
      description,
      nextRuns,
      isValid: true,
    };
  } catch (error: any) {
    return {
      description: '',
      nextRuns: [],
      isValid: false,
      error: error?.message || 'Failed to parse cron expression',
    };
  }
}

// Generate next few run times with seconds precision using cron-parser
function generateNextRuns(cron: string, hasSeconds: boolean): string[] {
  const runs: string[] = [];
  const now = new Date();

  try {
    // Parse the cron expression with seconds support
    // Using local timezone (no tz option means local time)
    const interval = CronExpressionParser.parse(cron, {
      currentDate: now,
      ...(hasSeconds && { seconds: true }),
    });

    // Get next 5 run times
    for (let i = 0; i < 5; i++) {
      try {
        const nextDate = interval.next().toDate();

        // Format with seconds
        const formatted = nextDate.toLocaleString('en-US', {
          month: 'short',
          day: 'numeric',
          year: nextDate.getFullYear() !== now.getFullYear() ? 'numeric' : undefined,
          hour: '2-digit',
          minute: '2-digit',
          second: '2-digit',
          hour12: true,
        });

        runs.push(formatted);
      } catch (e) {
        // If we can't get more dates, break
        break;
      }
    }
  } catch (error) {
    // If parsing fails, return empty array
    console.error('Error generating next runs:', error);
  }

  return runs;
}

// Common cron presets with descriptions
export const CRON_EXAMPLES = [
  {
    expression: '* * * * * *',
    description: 'Every second',
    label: 'Every second',
  },
  {
    expression: '*/10 * * * * *',
    description: 'Every 10 seconds',
    label: 'Every 10 seconds',
  },
  {
    expression: '0 * * * * *',
    description: 'Every minute',
    label: 'Every minute',
  },
  {
    expression: '0 */5 * * * *',
    description: 'Every 5 minutes',
    label: 'Every 5 minutes',
  },
  {
    expression: '0 0 * * * *',
    description: 'Every hour at minute 0',
    label: 'Every hour',
  },
  {
    expression: '0 0 14 * * *',
    description: 'Every day at 2:00 PM',
    label: 'Daily at 2 PM',
  },
  {
    expression: '0 0 9 * * 1',
    description: 'Every Monday at 9:00 AM',
    label: 'Weekly on Monday',
  },
  {
    expression: '0 0 0 1 * *',
    description: 'First day of month at midnight',
    label: 'Monthly',
  },
  {
    expression: '0 0 0 * * 0',
    description: 'Every Sunday at midnight',
    label: 'Weekly on Sunday',
  },
  {
    expression: '0 30 14 * * *',
    description: 'Every day at 2:30 PM',
    label: 'Daily at 2:30 PM',
  },
];
