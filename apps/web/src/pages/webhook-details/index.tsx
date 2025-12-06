import { useParams, useNavigate } from 'react-router-dom';
import { useWebhook, useDeleteWebhook, useUpdateWebhook } from '@/hooks/use-webhooks';
import { useJobExecutions } from '@/hooks/use-job-executions';
import { FadeIn } from '@/components/motion/fade-in';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import {
  Pencil,
  Trash2,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Timer,
  Webhook,
  Copy,
  Check,
} from 'lucide-react';
import { Switch } from '@/components/ui/switch';
import { formatDistanceToNow, format } from 'date-fns';
import { useState, useMemo } from 'react';
import { ChartContainer, ChartTooltip } from '@/components/ui/chart';
import { CartesianGrid, XAxis, YAxis, Bar, BarChart, Cell } from 'recharts';
import { motion, AnimatePresence } from 'motion/react';
import { cn } from '@/lib/utils';
import { toast } from 'sonner';

// Transform API execution data to frontend format
const transformExecution = (execution: any) => {
  const statusCode =
    execution.response_code ||
    (execution.status === 'success' ? 200 : execution.status === 'failure' ? 500 : 0);
  const isSuccess = statusCode >= 200 && statusCode < 300;
  const timestamp = new Date(execution.created_at);

  // Parse response body if it's a string, otherwise use as-is
  let responseBody = execution.response_body;
  if (responseBody && typeof responseBody === 'string') {
    try {
      // Try to parse as JSON and format it nicely
      const parsed = JSON.parse(responseBody);
      responseBody = JSON.stringify(parsed, null, 2);
    } catch {
      // If not JSON, use as-is
    }
  }

  return {
    id: execution.id,
    timestamp,
    status:
      execution.status === 'success'
        ? 'success'
        : execution.status === 'failure'
          ? 'error'
          : execution.status === 'timed_out'
            ? 'timeout'
            : 'error',
    statusCode,
    duration: execution.duration_ms || 0,
    response: {
      status: statusCode,
      body:
        responseBody ||
        (isSuccess
          ? JSON.stringify({ message: 'Request processed successfully' }, null, 2)
          : JSON.stringify({ error: execution.error || 'Request failed' }, null, 2)),
      headers: {
        'content-type': 'application/json',
        ...(execution.worker_id && { 'x-worker-id': execution.worker_id }),
      },
    },
  };
};

const WebhookDetailsPage = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { data: webhook, isLoading, isError } = useWebhook(id!);
  const { data: executionsData, isLoading: isLoadingExecutions } = useJobExecutions(id);
  const deleteWebhook = useDeleteWebhook();
  const updateWebhook = useUpdateWebhook();
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [expandedExecution, setExpandedExecution] = useState<string | null>(null);
  const [copiedId, setCopiedId] = useState<string | null>(null);

  // Transform API executions to frontend format
  const executions = useMemo(() => {
    if (!executionsData) return [];
    return executionsData
      .map(transformExecution)
      .sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime());
  }, [executionsData]);

  // Prepare chart data - one bar per execution
  const chartData = useMemo(() => {
    return executions.map((exec, index) => ({
      name: `#${executions.length - index}`,
      duration: exec.duration,
      status: exec.statusCode >= 200 && exec.statusCode < 300 ? 'success' : 'error',
      statusCode: exec.statusCode,
      timestamp: format(exec.timestamp, 'MMM dd, HH:mm:ss'),
    }));
  }, [executions]);

  // Calculate summary stats
  const summaryStats = useMemo(() => {
    const total = executions.length;
    const success = executions.filter((e) => e.statusCode >= 200 && e.statusCode < 300).length;
    const error = total - success;
    const avgDuration =
      total > 0 ? Math.round(executions.reduce((sum, e) => sum + e.duration, 0) / total) : 0;
    const successRate = total > 0 ? Math.round((success / total) * 100) : 0;

    return { total, success, error, avgDuration, successRate };
  }, [executions]);

  const getStatusBadge = (_status: string, statusCode: number) => {
    if (statusCode >= 200 && statusCode < 300) {
      return (
        <Badge variant="outline" className="bg-green-500/10 text-green-600 border-green-500/20">
          <CheckCircle2 className="h-3 w-3 mr-1" />
          {statusCode}
        </Badge>
      );
    } else if (statusCode >= 400 && statusCode < 500) {
      return (
        <Badge variant="outline" className="bg-yellow-500/10 text-yellow-600 border-yellow-500/20">
          <AlertCircle className="h-3 w-3 mr-1" />
          {statusCode}
        </Badge>
      );
    } else {
      return (
        <Badge variant="outline" className="bg-red-500/10 text-red-600 border-red-500/20">
          <XCircle className="h-3 w-3 mr-1" />
          {statusCode}
        </Badge>
      );
    }
  };

  const handleDelete = () => {
    if (id) {
      deleteWebhook.mutate(id, {
        onSuccess: () => {
          navigate('/');
        },
      });
    }
  };

  const handleCopy = (text: string, executionId: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(executionId);
    toast('Copied!', {
      description: 'Content copied to clipboard',
    });
    setTimeout(() => setCopiedId(null), 2000);
  };

  // Handle toggle enable/disable
  const handleToggleEnabled = async (newEnabled: boolean) => {
    if (!id) return;
    try {
      await updateWebhook.mutateAsync({
        id,
        data: {
          job: {
            enabled: newEnabled,
          },
        } as any,
      });
      toast(newEnabled ? 'Webhook enabled' : 'Webhook disabled', {
        description: `Webhook has been ${newEnabled ? 'enabled' : 'disabled'}`,
      });
    } catch (error) {
      console.error('Failed to toggle webhook status:', error);
      toast.error('Error', {
        description: 'Failed to update webhook status',
      });
    }
  };

  // Loading state
  if (isLoading) {
    return (
      <div className="min-h-screen bg-background p-8 pl-32">
        <div className="container mx-auto space-y-6 max-w-7xl">
          <Skeleton className="h-10 w-32 mb-4" />
          <Skeleton className="h-16 w-full" />
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {[...Array(4)].map((_, i) => (
              <Skeleton key={i} className="h-24 w-full" />
            ))}
          </div>
        </div>
      </div>
    );
  }

  // Error state
  if (isError || !webhook) {
    return (
      <div className="min-h-screen bg-background p-8 pl-32">
        <div className="container mx-auto max-w-4xl">
          <FadeIn>
            <div className="rounded-lg border border-destructive/50 bg-destructive/5 p-6 text-center">
              <AlertCircle className="h-12 w-12 text-destructive mx-auto mb-4" />
              <h2 className="text-xl font-semibold mb-2">Webhook Not Found</h2>
              <p className="text-sm text-muted-foreground mb-4">
                The webhook you're looking for could not be found.
              </p>
              <Button onClick={() => navigate('/')}>Return to Dashboard</Button>
            </div>
          </FadeIn>
        </div>
      </div>
    );
  }

  const job = webhook.job;

  return (
    <div className="min-h-screen bg-background p-8 pl-32">
      <div className="container mx-auto space-y-6 max-w-7xl">
        {/* Header */}
        <FadeIn>
          <Card className="mb-4 rounded-xl border-border/50 bg-card transition-all shadow-none duration-200 hover:border-border hover:shadow-sm">
            <CardContent className="flex items-center justify-between gap-6 p-4">
              {/* Left Side - Information */}
              <div className="flex items-center gap-4 flex-1 min-w-0">
                <div className="flex-shrink-0 flex items-center justify-center w-10 h-10 rounded-lg bg-primary/10">
                  <Webhook className="h-5 w-5 text-primary" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <h3 className="font-semibold text-sm text-foreground truncate">
                      {job?.name || 'Unnamed Webhook'}
                    </h3>
                    <span className="text-xs text-muted-foreground">
                      {formatDistanceToNow(new Date(webhook.created_at), {
                        addSuffix: true,
                      })}
                    </span>
                  </div>
                  <div className="flex items-center gap-3 mt-1 text-xs text-muted-foreground">
                    <div className="flex items-center gap-1.5 min-w-0">
                      <code className="truncate font-mono">{webhook.url}</code>
                      <button
                        className="flex-shrink-0 rounded p-0.5 text-muted-foreground opacity-0 transition-all hover:text-foreground group-hover:opacity-100"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleCopy(webhook.url, webhook.id);
                        }}
                      >
                        {copiedId === webhook.id ? (
                          <Check className="h-3 w-3" />
                        ) : (
                          <Copy className="h-3 w-3" />
                        )}
                      </button>
                    </div>
                  </div>
                </div>
              </div>

              {/* Right Side - Actions */}
              <div className="flex items-center gap-3 flex-shrink-0">
                <div className="flex items-center gap-1">
                  {/* Edit Button */}
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => navigate(`/edit/${webhook.id}`)}
                    className="h-9 group"
                  >
                    <Pencil className="h-3.5 w-3.5 text-muted-foreground group-hover:text-primary transition-colors" />
                  </Button>
                  {/* Delete Button */}
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => setDeleteDialogOpen(true)}
                    className="h-9 group"
                  >
                    <Trash2 className="h-3.5 w-3.5 text-muted-foreground group-hover:text-destructive transition-colors" />
                  </Button>
                </div>
                {/* Enable/Disable Toggle */}
                <div className="flex items-center gap-2">
                  <Switch
                    checked={job?.enabled ?? false}
                    onCheckedChange={handleToggleEnabled}
                    disabled={updateWebhook.isPending}
                  />
                </div>
              </div>
            </CardContent>
          </Card>
        </FadeIn>

        {/* Execution Overview Chart */}
        <FadeIn delay={0.1}>
          <Card className="shadow-none border-border/50 bg-card transition-all duration-200 hover:border-border hover:shadow-sm">
            <CardContent className="p-5">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h3 className="text-sm font-semibold text-foreground">Execution Overview</h3>
                  <p className="text-xs text-muted-foreground mt-0.5">
                    Success rate: {summaryStats.successRate}% • Avg response:{' '}
                    {summaryStats.avgDuration}ms
                  </p>
                </div>
                <div className="flex items-center gap-4 text-xs">
                  <div className="flex items-center gap-1.5">
                    <div className="h-2 w-2 rounded-full bg-green-500" />
                    <span className="text-muted-foreground">Success ({summaryStats.success})</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <div className="h-2 w-2 rounded-full bg-red-500" />
                    <span className="text-muted-foreground">Error ({summaryStats.error})</span>
                  </div>
                </div>
              </div>
              <ChartContainer
                config={{
                  success: {
                    label: 'Success',
                    color: 'hsl(142, 71%, 45%)',
                  },
                  error: {
                    label: 'Error',
                    color: 'hsl(0, 84%, 60%)',
                  },
                }}
                className="h-[300px] w-full"
              >
                <BarChart
                  data={chartData}
                  barCategoryGap="20%"
                  margin={{ top: 8, right: 8, bottom: 8, left: 8 }}
                >
                  <CartesianGrid strokeDasharray="3 3" vertical={false} className="stroke-muted" />
                  <XAxis
                    dataKey="name"
                    tickLine={false}
                    axisLine={false}
                    tickMargin={8}
                    tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 11 }}
                  />
                  <YAxis
                    tickLine={false}
                    axisLine={false}
                    tickMargin={8}
                    width={50}
                    tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 11 }}
                    label={{
                      value: 'ms',
                      angle: -90,
                      position: 'insideLeft',
                      style: { textAnchor: 'middle', fontSize: 11 },
                    }}
                  />
                  <ChartTooltip
                    cursor={false}
                    content={({ active, payload }) => {
                      if (active && payload && payload.length) {
                        const data = payload[0].payload;
                        return (
                          <div className="rounded-lg border bg-background p-2.5 shadow-sm">
                            <div className="grid gap-1.5">
                              <div className="flex items-center justify-between gap-4">
                                <span className="text-[10px] text-muted-foreground">Status</span>
                                <Badge
                                  variant="outline"
                                  className={
                                    data.status === 'success'
                                      ? 'bg-green-500/10 text-green-600 border-green-500/20 text-[10px] h-5 px-1.5'
                                      : 'bg-red-500/10 text-red-600 border-red-500/20 text-[10px] h-5 px-1.5'
                                  }
                                >
                                  {data.statusCode}
                                </Badge>
                              </div>
                              <div className="flex items-center justify-between gap-4">
                                <span className="text-[10px] text-muted-foreground">Duration</span>
                                <span className="text-[10px] font-medium">{data.duration}ms</span>
                              </div>
                              <div className="flex items-center justify-between gap-4">
                                <span className="text-[10px] text-muted-foreground">Time</span>
                                <span className="text-[10px] font-medium">{data.timestamp}</span>
                              </div>
                            </div>
                          </div>
                        );
                      }
                      return null;
                    }}
                  />
                  <Bar dataKey="duration" radius={[2, 2, 0, 0]} maxBarSize={24}>
                    {chartData.map((entry, index) => (
                      <Cell
                        key={`cell-${index}`}
                        fill={
                          entry.status === 'success' ? 'hsl(142, 71%, 45%)' : 'hsl(0, 84%, 60%)'
                        }
                        style={{ opacity: 0.9 }}
                      />
                    ))}
                  </Bar>
                </BarChart>
              </ChartContainer>
            </CardContent>
          </Card>
        </FadeIn>

        {/* Main Content - Execution Logs with Animated Details */}
        <div>
          <motion.div
            className="grid gap-6 relative"
            initial={false}
            animate={{
              gridTemplateColumns: expandedExecution ? '1fr 1fr' : '1fr',
            }}
            transition={{
              duration: 0.4,
              ease: [0.16, 1, 0.3, 1],
            }}
          >
            {/* Execution Logs List */}
            <motion.div className="min-w-0" layout>
              <FadeIn delay={0.2}>
                <Card className="shadow-none bg-transparent border-none">
                  <CardHeader className="py-4 px-0">
                    <CardTitle>
                      <div className="flex items-center justify-between gap-2">
                        <p className="text-sm font-semibold">Execution Logs</p>
                        <span className="text-xs text-muted-foreground">
                          {isLoadingExecutions ? '...' : executions.length} executions
                        </span>
                      </div>
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="p-0">
                    {isLoadingExecutions ? (
                      <div className="space-y-2 p-4">
                        {[...Array(5)].map((_, i) => (
                          <Skeleton key={i} className="h-16 w-full" />
                        ))}
                      </div>
                    ) : executions.length === 0 ? (
                      <div className="py-8 px-4 text-center text-sm text-muted-foreground">
                        <p className="text-sm">No executions yet</p>
                        <p className="text-xs mt-1">
                          Executions will appear here once the webhook runs
                        </p>
                      </div>
                    ) : (
                      <div className="max-h-[calc(100vh-200px)] overflow-y-auto no-scrollbar space-y-2">
                        {executions.map((execution) => (
                          <button
                            key={execution.id}
                            onClick={() =>
                              setExpandedExecution(
                                expandedExecution === execution.id ? null : execution.id
                              )
                            }
                            className={cn(
                              'w-full text-left p-4 border border-border/50 rounded-lg transition-colors hover:bg-muted/50',
                              expandedExecution === execution.id
                                ? 'bg-primary/10 border-primary'
                                : ''
                            )}
                          >
                            <div className="flex items-center gap-2 mb-2">
                              <div className="flex items-center gap-2">
                                {getStatusBadge(execution.status, execution.statusCode)}
                                <div className="flex items-center gap-1 text-xs text-muted-foreground">
                                  <Timer className="h-3 w-3" />
                                  {execution.duration}ms
                                </div>
                              </div>
                              <div className="flex-1 text-right">
                                <p className="text-xs text-muted-foreground">
                                  {formatDistanceToNow(execution.timestamp, { addSuffix: true })}
                                </p>
                              </div>
                            </div>
                          </button>
                        ))}
                      </div>
                    )}
                  </CardContent>
                </Card>
              </FadeIn>
            </motion.div>

            {/* Right Column - Expanded Execution Details */}
            <AnimatePresence mode="wait">
              {expandedExecution && (
                <motion.div
                  key={expandedExecution}
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: 20 }}
                  transition={{
                    duration: 0.4,
                    ease: [0.16, 1, 0.3, 1],
                  }}
                  className="min-w-0"
                  layout
                >
                  {(() => {
                    const execution = executions.find((e) => e.id === expandedExecution);
                    if (!execution) return null;
                    return (
                      <Card className="shadow-none bg-transparent border-none">
                        <CardHeader className="py-4 px-0">
                          <CardTitle className="flex items-center justify-between">
                            <div className="flex items-center gap-2">
                              {getStatusBadge(execution.status, execution.statusCode)}
                              <span className="text-sm text-muted-foreground font-normal">
                                {execution.duration}ms
                              </span>
                            </div>
                            <span className="text-sm text-muted-foreground font-normal">
                              {formatDistanceToNow(execution.timestamp, { addSuffix: true })}
                            </span>
                          </CardTitle>
                        </CardHeader>
                        <CardContent className="bg-card rounded-lg p-4 border border-border/50">
                          <div className="space-y-4">
                            <div>
                              <p className="text-xs font-medium text-muted-foreground mb-2">
                                Response ({execution.response.status})
                              </p>
                              <div className="rounded-md border bg-background">
                                <div className="border-b p-2 bg-muted/30">
                                  <p className="text-xs font-medium text-foreground">Headers</p>
                                </div>
                                <div className="p-3">
                                  <div className="space-y-2">
                                    {Object.entries(execution.response.headers).map(
                                      ([key, value]) => (
                                        <div
                                          key={key}
                                          className="grid grid-cols-3 gap-2 p-2 rounded items-center"
                                        >
                                          <p className="text-sm font-semibold text-muted-foreground col-span-1">
                                            {key}
                                          </p>
                                          <div className="flex items-center justify-between gap-2 col-span-2">
                                            <code className="text-xs break-all font-mono">
                                              {String(value)}
                                            </code>
                                            <Button
                                              variant="ghost"
                                              size="sm"
                                              onClick={() =>
                                                handleCopy(`${key}: ${value}`, execution.id)
                                              }
                                              className="flex-shrink-0"
                                            >
                                              {copiedId === execution.id ? (
                                                <Check className="h-3 w-3" />
                                              ) : (
                                                <Copy className="h-3 w-3" />
                                              )}
                                            </Button>
                                          </div>
                                        </div>
                                      )
                                    )}
                                  </div>
                                </div>
                              </div>
                            </div>
                            <div>
                              <p className="text-xs font-medium text-muted-foreground mb-2">Body</p>
                              <div className="relative">
                                <pre className="text-xs font-mono p-3 rounded-md bg-muted/20 border overflow-x-auto max-h-[300px]">
                                  {execution.response.body}
                                </pre>
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  className="absolute top-2 right-2"
                                  onClick={() => handleCopy(execution.response.body, execution.id)}
                                >
                                  {copiedId === execution.id ? (
                                    <Check className="h-4 w-4" />
                                  ) : (
                                    <Copy className="h-4 w-4" />
                                  )}
                                </Button>
                              </div>
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    );
                  })()}
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>
        </div>
      </div>

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete webhook?</AlertDialogTitle>
            <AlertDialogDescription>
              This action cannot be undone. The webhook will be permanently removed and will stop
              sending scheduled requests.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDelete}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              {deleteWebhook.isPending ? 'Deleting...' : 'Delete'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
};

export default WebhookDetailsPage;
